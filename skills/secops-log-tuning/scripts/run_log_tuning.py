#!/usr/bin/env python3
"""Two-stage Google SecOps Log Volume & Tuning Analyzer.

Stage 1: Queries `ingestion` joined with `events` to identify the top log_types by byte
volume and their highest-volume (metadata.event_type, metadata.product_event_type) pairs.

Stage 2: Routes each top category by `metadata.event_type` to an actor-grouped Piped SQL
drill-down query (preventing high-cardinality target fields like random temp filenames from
shattering counts) and classifies each finding as FLEET_WIDE_POLICY vs. SINGLE_HOST_OUTLIER.

Usage:
    python scripts/run_log_tuning.py --days 7 --top-log-types 5 --top-categories 3
    python scripts/run_log_tuning.py --days 7 --log-type SENTINELONE_CF
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import sys
import urllib.error
import urllib.request

try:
    from dotenv import load_dotenv
    current_dir = os.path.dirname(os.path.abspath(__file__))
    venv_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "../.."))
    possible_env_paths = [
        os.path.join(current_dir, "../../../.env"),
        os.path.join(current_dir, "../../../../.env"),
        os.path.join(venv_root, ".env"),
        os.path.join(os.getcwd(), ".env"),
    ]
    for candidate in possible_env_paths:
        if os.path.exists(candidate):
            load_dotenv(dotenv_path=os.path.abspath(candidate))
            break
except ImportError:
    pass


def _extract_dashboard_rows(raw_response: dict) -> list:
    results = raw_response.get("results", [])
    if not results:
        return []
    columns = [r.get("column", f"col_{i}") for i, r in enumerate(results)]
    num_rows = len(results[0].get("values", []))
    rows = []
    for row_idx in range(num_rows):
        row = {}
        for col_idx, col_data in enumerate(results):
            col_name = columns[col_idx]
            values = col_data.get("values", [])
            val = None
            if row_idx < len(values):
                val_obj = values[row_idx].get("value", {})
                for key in (
                    "stringVal",
                    "stringValue",
                    "int64Val",
                    "int64Value",
                    "doubleVal",
                    "doubleValue",
                    "boolVal",
                    "boolValue",
                    "timestampVal",
                    "timestampValue",
                ):
                    if key in val_obj and val_obj[key] is not None:
                        val = val_obj[key]
                        break
            row[col_name] = val
        rows.append(row)
    return rows


def execute_dashboard_sql(query_text: str, days: int = 7) -> list:
    import google.auth
    from google.auth.transport.requests import Request

    project_id = (
        os.environ.get("SECOPS_PROJECT_ID")
        or os.environ.get("GCP_PROJECT_ID")
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
    )
    customer_id = os.environ.get("SECOPS_CUSTOMER_ID")
    region = os.environ.get("SECOPS_REGION", "us")

    if not customer_id or not project_id:
        raise ValueError(
            "Missing SECOPS_PROJECT_ID or SECOPS_CUSTOMER_ID in environment or .env."
        )

    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    if not credentials.valid:
        credentials.refresh(Request())

    url = (
        f"https://{region}-chronicle.googleapis.com/v1alpha/projects/{project_id}/"
        f"locations/{region}/instances/{customer_id}/dashboardQueries:execute"
    )
    body = {
        "query": {
            "query": query_text.strip(),
            "dialect": "SQL",
            "input": {"relativeTime": {"timeUnit": "DAY", "startTimeVal": str(days)}},
        },
        "filters": [],
        "usePreviousTimeRange": False,
        "querySource": "DASHBOARD",
    }
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-goog-user-project": project_id,
    }
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST"
    )
    with urllib.request.urlopen(req, timeout=45.0) as resp:
        raw = json.loads(resp.read().decode("utf-8"))
        return _extract_dashboard_rows(raw)


def build_stage1_query(
    days: int, top_log_types: int, top_categories: int, log_type_filter: str = ""
) -> str:
    extra_events_filter = (
        f"\n     AND metadata.log_type = '{log_type_filter}'" if log_type_filter else ""
    )
    extra_ing_filter = (
        f"\n          AND log_type = '{log_type_filter}'" if log_type_filter else ""
    )
    return f"""FROM events
|> WHERE TIMESTAMP_SECONDS(metadata.event_timestamp.seconds) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
     AND NULLIF(metadata.log_type, '') IS NOT NULL{extra_events_filter}
|> AGGREGATE COUNT(1) AS event_count
   GROUP BY
     metadata.log_type AS log_type,
     metadata.event_type AS event_type,
     COALESCE(NULLIF(metadata.product_event_type, ''), 'UNSET') AS product_event_type
|> JOIN (
     FROM ingestion
     |> WHERE component = 'Ingestion API'
          AND NULLIF(log_type, '') IS NOT NULL
          AND TIMESTAMP_SECONDS(start_time) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY){extra_ing_filter}
     |> AGGREGATE
          SUM(log_volume) AS total_volume_bytes,
          SUM(log_count) AS total_ingested_logs,
          ROUND(SAFE_DIVIDE(SUM(log_volume), NULLIF(SUM(log_count), 0)), 2) AS avg_bytes_per_log
        GROUP BY log_type
     |> ORDER BY total_volume_bytes DESC
     |> LIMIT {top_log_types}
   ) USING (log_type)
|> EXTEND
     SUM(event_count) OVER (PARTITION BY log_type) AS total_udm_events_for_log_type,
     ROUND(event_count * 100.0 / SUM(event_count) OVER (PARTITION BY log_type), 2) AS pct_of_log_type,
     ROUND(total_volume_bytes / 1073741824.0, 2) AS log_type_ingested_gb,
     ROUND(event_count * avg_bytes_per_log / 1048576.0, 2) AS est_product_event_mb,
     ROW_NUMBER() OVER (PARTITION BY log_type ORDER BY event_count DESC) AS rank_in_log_type
|> WHERE rank_in_log_type <= {top_categories}
|> ORDER BY total_volume_bytes DESC, pct_of_log_type DESC
|> LIMIT {top_log_types * top_categories};"""


def build_stage2_query(
    days: int,
    log_type: str,
    event_type: str,
    product_event_type: str,
    avg_bytes_per_log: float,
    limit: int = 5,
) -> str:
    safe_pet = product_event_type.replace("'", "\\'")
    base_where = f"""FROM events
|> WHERE TIMESTAMP_SECONDS(metadata.event_timestamp.seconds) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
     AND metadata.log_type = '{log_type}'
     AND metadata.event_type = '{event_type}'
     AND COALESCE(NULLIF(metadata.product_event_type, ''), 'UNSET') = '{safe_pet}'"""

    if event_type.startswith("FILE_"):
        agg_group = """|> AGGREGATE
     COUNT(1) AS event_count,
     COUNT(DISTINCT principal.hostname) AS distinct_hosts,
     ANY_VALUE(principal.hostname) AS sample_host,
     COUNT(DISTINCT target.file.full_path) AS distinct_targets,
     ANY_VALUE(target.file.full_path) AS sample_target
   GROUP BY
     COALESCE(NULLIF(principal.process.file.full_path, ''), NULLIF(target.process.file.full_path, ''), 'UNSET') AS primary_dimension"""
    elif event_type.startswith("PROCESS_"):
        agg_group = """|> AGGREGATE
     COUNT(1) AS event_count,
     COUNT(DISTINCT principal.hostname) AS distinct_hosts,
     ANY_VALUE(principal.hostname) AS sample_host,
     COUNT(DISTINCT target.process.command_line) AS distinct_targets,
     ANY_VALUE(SUBSTR(target.process.command_line, 1, 160)) AS sample_target
   GROUP BY
     COALESCE(NULLIF(principal.process.file.full_path, ''), 'UNSET') AS parent_process,
     COALESCE(NULLIF(target.process.file.full_path, ''), SUBSTR(NULLIF(target.process.command_line, ''), 1, 100), 'UNSET') AS primary_dimension"""
    elif event_type == "NETWORK_DNS":
        agg_group = """|> AGGREGATE
     COUNT(1) AS event_count,
     COUNT(DISTINCT principal.ip[SAFE_OFFSET(0)]) AS distinct_hosts,
     ANY_VALUE(principal.ip[SAFE_OFFSET(0)]) AS sample_host,
     COUNT(DISTINCT target.ip[SAFE_OFFSET(0)]) AS distinct_targets,
     ANY_VALUE(target.ip[SAFE_OFFSET(0)]) AS sample_target
   GROUP BY
     COALESCE(NULLIF(network.dns.questions[SAFE_OFFSET(0)].name, ''), 'UNSET') AS primary_dimension,
     COALESCE(NULLIF(principal.ip[SAFE_OFFSET(0)], ''), 'UNSET') AS src_ip,
     COALESCE(NULLIF(target.ip[SAFE_OFFSET(0)], ''), 'UNSET') AS dst_ip"""
    elif event_type == "NETWORK_HTTP":
        agg_group = """|> AGGREGATE
     COUNT(1) AS event_count,
     COUNT(DISTINCT principal.ip[SAFE_OFFSET(0)]) AS distinct_hosts,
     ANY_VALUE(principal.ip[SAFE_OFFSET(0)]) AS sample_host,
     COUNT(DISTINCT target.url) AS distinct_targets,
     ANY_VALUE(SUBSTR(target.url, 1, 140)) AS sample_target
   GROUP BY
     COALESCE(NULLIF(target.hostname, ''), NULLIF(network.tls.client.server_name, ''), NULLIF(target.ip[SAFE_OFFSET(0)], ''), 'UNSET') AS primary_dimension,
     COALESCE(NULLIF(network.http.user_agent, ''), 'UNSET') AS user_agent"""
    elif event_type.startswith("NETWORK_"):
        agg_group = """|> AGGREGATE
     COUNT(1) AS event_count,
     COUNT(DISTINCT principal.ip[SAFE_OFFSET(0)]) AS distinct_hosts,
     ANY_VALUE(principal.ip[SAFE_OFFSET(0)]) AS sample_host,
     COUNT(DISTINCT target.ip[SAFE_OFFSET(0)]) AS distinct_targets,
     ANY_VALUE(COALESCE(NULLIF(network.tls.client.server_name, ''), NULLIF(security_result[SAFE_OFFSET(0)].summary, ''), NULLIF(metadata.description, ''))) AS sample_target
   GROUP BY
     COALESCE(NULLIF(principal.ip[SAFE_OFFSET(0)], ''), 'UNSET') AS src_ip,
     COALESCE(NULLIF(target.ip[SAFE_OFFSET(0)], ''), 'UNSET') AS dst_ip,
     target.port AS dst_port,
     network.ip_protocol AS ip_protocol"""
    elif event_type.startswith("REGISTRY_"):
        agg_group = """|> AGGREGATE
     COUNT(1) AS event_count,
     COUNT(DISTINCT principal.hostname) AS distinct_hosts,
     ANY_VALUE(principal.hostname) AS sample_host,
     COUNT(DISTINCT target.registry.registry_value_name) AS distinct_targets,
     ANY_VALUE(target.registry.registry_value_name) AS sample_target
   GROUP BY
     COALESCE(NULLIF(principal.process.file.full_path, ''), 'UNSET') AS primary_dimension,
     COALESCE(NULLIF(target.registry.registry_key, ''), 'UNSET') AS registry_key"""
    else:
        agg_group = """|> AGGREGATE
     COUNT(1) AS event_count,
     COUNT(DISTINCT COALESCE(NULLIF(principal.hostname, ''), NULLIF(target.hostname, ''))) AS distinct_hosts,
     ANY_VALUE(COALESCE(NULLIF(principal.hostname, ''), NULLIF(target.hostname, ''))) AS sample_host,
     COUNT(DISTINCT COALESCE(NULLIF(principal.user.userid, ''), NULLIF(target.user.userid, ''))) AS distinct_targets,
     ANY_VALUE(COALESCE(NULLIF(principal.user.userid, ''), NULLIF(target.user.userid, ''))) AS sample_target
   GROUP BY
     COALESCE(
       NULLIF(principal.process.file.full_path, ''),
       NULLIF(target.process.file.full_path, ''),
       NULLIF(target.resource.name, ''),
       NULLIF(principal.application, ''),
       NULLIF(security_result[SAFE_OFFSET(0)].summary, ''),
       'UNSET'
     ) AS primary_dimension"""

    return f"""{base_where}
{agg_group}
|> EXTEND
     ROUND(event_count * 100.0 / SUM(event_count) OVER (), 2) AS pct_of_category,
     ROUND(event_count * {avg_bytes_per_log} / 1048576.0, 2) AS est_mb
|> ORDER BY event_count DESC
|> LIMIT {limit};"""


def main():
    parser = argparse.ArgumentParser(description="Two-stage SecOps Log Tuning Analyzer")
    parser.add_argument("--days", type=int, default=7, help="Lookback window in days")
    parser.add_argument("--top-log-types", type=int, default=5, help="Top log types by volume")
    parser.add_argument("--top-categories", type=int, default=3, help="Top event categories per log type")
    parser.add_argument("--log-type", type=str, default="", help="Optional single log_type filter")
    parser.add_argument("--min-mb", type=float, default=50.0, help="Min estimated MB for Stage 2 drill-down")
    parser.add_argument("--stage2-limit", type=int, default=5, help="Top rows per Stage 2 drill-down")
    args = parser.parse_args()

    stage1_sql = build_stage1_query(
        days=args.days,
        top_log_types=args.top_log_types,
        top_categories=args.top_categories,
        log_type_filter=args.log_type,
    )

    try:
        stage1_rows = execute_dashboard_sql(stage1_sql, days=args.days)
    except urllib.error.HTTPError as e:
        print(f"STAGE1_HTTP_ERROR: {e.read().decode('utf-8', errors='replace')}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"STAGE1_ERROR: {e}", file=sys.stderr)
        sys.exit(3)

    candidates = [
        r for r in stage1_rows if float(r.get("est_product_event_mb") or 0.0) >= args.min_mb
    ]

    def _run_stage2(row: dict) -> dict:
        lt = row["log_type"]
        et = row["event_type"]
        pet = row["product_event_type"]
        avg_b = float(row.get("avg_bytes_per_log") or 0.0)
        s2_sql = build_stage2_query(
            days=args.days,
            log_type=lt,
            event_type=et,
            product_event_type=pet,
            avg_bytes_per_log=avg_b,
            limit=args.stage2_limit,
        )
        s2_rows = execute_dashboard_sql(s2_sql, days=args.days)
        window_seconds = max(args.days * 86400, 1)
        for item in s2_rows:
            dh = max(int(item.get("distinct_hosts") or 0), 1)
            ec = int(item.get("event_count") or 0)
            eps_per_host = round(ec / (window_seconds * dh), 2)
            item["events_per_sec_per_host"] = eps_per_host
            if eps_per_host >= 1.0 and int(item.get("distinct_hosts") or 0) <= 5:
                item["tuning_scope"] = (
                    "SOURCE_MISCONFIGURATION_LIKELY_FIX_AT_SOURCE_AND_PIN_TUPLE"
                )
            elif int(item.get("distinct_hosts") or 0) <= 3:
                item["tuning_scope"] = "SINGLE_HOST_OR_COLLECTOR_OUTLIER_PIN_TUPLE"
            else:
                item["tuning_scope"] = "FLEET_WIDE_POLICY_EXCLUSION"
        return {
            "log_type": lt,
            "event_type": et,
            "product_event_type": pet,
            "log_type_ingested_gb": row.get("log_type_ingested_gb"),
            "avg_bytes_per_log": avg_b,
            "category_event_count": row.get("event_count"),
            "pct_of_log_type": row.get("pct_of_log_type"),
            "est_product_event_mb": row.get("est_product_event_mb"),
            "stage2_sql": s2_sql,
            "top_drivers": s2_rows,
        }

    drilldowns = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        future_map = {pool.submit(_run_stage2, r): i for i, r in enumerate(candidates)}
        ordered = [None] * len(candidates)
        for fut in as_completed(future_map):
            idx = future_map[fut]
            try:
                ordered[idx] = fut.result()
            except Exception as exc:
                ordered[idx] = {"error": str(exc), "candidate": candidates[idx]}
        drilldowns = [x for x in ordered if x is not None]

    output = {
        "lookback_days": args.days,
        "stage1_sql": stage1_sql,
        "stage1_summary": stage1_rows,
        "stage2_drilldowns": drilldowns,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
