#!/usr/bin/env python3
"""
SOAR Alert-to-Case Grouping and Merging Tool
Scans Chronicle SecOps cases, extracts alert entities, identifies overlaps, and merges redundant cases.
"""

import os
import sys
import json
import argparse
import asyncio
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Set, Any, Tuple

import httpx
import google.auth
from google.auth.transport.requests import Request


def get_config() -> Tuple[str, str, str]:
    """Resolves Chronicle config from environment or .env file."""
    cur = os.path.dirname(os.path.abspath(__file__))
    while cur and cur != os.path.dirname(cur):
        env_path = os.path.join(cur, ".env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ[k.strip()] = v.strip().strip('"').strip("'")
            break
        cur = os.path.dirname(cur)

    region = (
        os.environ.get("CHRONICLE_REGION")
        or os.environ.get("SECOPS_REGION")
        or "us"
    )
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    credentials, default_project = google.auth.default(scopes=scopes)
    project_id = (
        os.environ.get("CHRONICLE_PROJECT_ID")
        or os.environ.get("SECOPS_PROJECT_ID")
        or os.environ.get("GCP_PROJECT_ID")
        or default_project
    )
    instance_id = (
        os.environ.get("CHRONICLE_INSTANCE_ID")
        or os.environ.get("SECOPS_CUSTOMER_ID")
        or "default-instance"
    )
    return region, project_id, instance_id


async def api_request(method: str, path: str, params: dict = None, json_data: dict = None) -> dict:
    """Dispatches authenticated REST requests to Chronicle API."""
    region, project_id, instance_id = get_config()
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    credentials, _ = google.auth.default(scopes=scopes)
    if not credentials.valid:
        credentials.refresh(Request())

    parent = f"projects/{project_id}/locations/{region}/instances/{instance_id}"
    base_url = f"https://chronicle.{region}.rep.googleapis.com/v1beta/{parent}"
    url = f"{base_url}{path}" if path.startswith(":") else f"{base_url}/{path}"

    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Accept": "application/json",
        "X-Goog-User-Project": project_id
    }
    if json_data is not None:
        headers["Content-Type"] = "application/json"

    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        resp = await client.request(method, url, params=params, json=json_data)
        if resp.status_code >= 400:
            raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")
        return resp.json()


async def fetch_case_entities(case: dict) -> Tuple[str, dict, List[dict], Dict[str, Set[str]]]:
    """Fetches alerts and extracts normalized entities for a given case."""
    case_name = case.get("name", "")
    case_id = case_name.split("/")[-1] if "/" in case_name else str(case.get("id", ""))
    
    try:
        alerts_resp = await api_request("GET", f"cases/{case_id}/caseAlerts")
        alerts = alerts_resp.get("caseAlerts", [])
    except Exception as e:
        print(f"[!] Error fetching alerts for case {case_id}: {e}", file=sys.stderr)
        alerts = []

    case_entities = defaultdict(set)
    for alert in alerts:
        alert_name = alert.get("name", "")
        alert_id = alert_name.split("/")[-1] if "/" in alert_name else str(alert.get("id", ""))
        try:
            ent_resp = await api_request("GET", f"cases/{case_id}/caseAlerts/{alert_id}/involvedEntities", params={"pageSize": 100})
            entities = ent_resp.get("involvedEntities", [])
            for ent in entities:
                ent_type = ent.get("type", "UNKNOWN").upper()
                ident = ent.get("identifier", "").strip()
                if ident and ent_type not in ["GENERIC", "THREATSIGNATURE"]:
                    norm_ident = ident.upper()
                    if norm_ident not in ["OUTCOME", "UNKNOWN", "TRUE", "FALSE", "NONE", "NULL"]:
                        case_entities[ent_type].add(norm_ident)
        except Exception as e:
            print(f"[!] Error fetching entities for alert {alert_id} in case {case_id}: {e}", file=sys.stderr)

    return case_id, case, alerts, case_entities


async def run_grouping(count: int = 10, execute_merge: bool = False, min_overlap: int = 1) -> dict:
    """Scans cases, finds entity overlaps, and optionally merges cases."""
    print(f"[*] Querying latest {count} Chronicle cases...")
    cases_resp = await api_request("GET", "cases", params={"pageSize": count, "filter": 'status = "OPENED"'})
    cases = cases_resp.get("cases", [])
    if not cases:
        cases_resp = await api_request("GET", "cases", params={"pageSize": count})
        cases = cases_resp.get("cases", [])

    print(f"[*] Analyzing {len(cases)} cases for alert entities...")
    tasks = [fetch_case_entities(c) for c in cases]
    results = await asyncio.gather(*tasks)

    entity_to_cases = defaultdict(set)
    case_data_map = {}
    case_entities_map = {}
    case_alerts_map = {}

    for case_id, case_info, alerts, entities in results:
        case_data_map[case_id] = case_info
        case_entities_map[case_id] = entities
        case_alerts_map[case_id] = alerts
        for ent_type, idents in entities.items():
            for ident in idents:
                entity_to_cases[(ent_type, ident)].add(case_id)

    # Find cross-case overlaps
    overlap_pairs = {}
    case_ids = list(case_data_map.keys())
    for i in range(len(case_ids)):
        for j in range(i + 1, len(case_ids)):
            cid1 = case_ids[i]
            cid2 = case_ids[j]
            shared_entities = defaultdict(list)
            for ent_type in case_entities_map[cid1]:
                if ent_type in case_entities_map[cid2]:
                    common = case_entities_map[cid1][ent_type].intersection(case_entities_map[cid2][ent_type])
                    if common:
                        shared_entities[ent_type].extend(list(common))
            
            total_shared = sum(len(v) for v in shared_entities.values())
            if total_shared >= min_overlap:
                overlap_pairs[(cid1, cid2)] = {
                    "case_1": cid1,
                    "case_2": cid2,
                    "case_1_title": case_data_map[cid1].get("displayName", ""),
                    "case_2_title": case_data_map[cid2].get("displayName", ""),
                    "shared_count": total_shared,
                    "shared_entities": {k: list(v) for k, v in shared_entities.items()}
                }

    # Group into connected merge clusters
    parent = {}
    def find(item):
        parent.setdefault(item, item)
        if parent[item] != item:
            parent[item] = find(parent[item])
        return parent[item]

    def union(item1, item2):
        root1 = find(item1)
        root2 = find(item2)
        if root1 != root2:
            parent[root1] = root2

    for cid1, cid2 in overlap_pairs.keys():
        type1 = case_data_map[cid1].get("type")
        type2 = case_data_map[cid2].get("type")
        # Chronicle SOAR prevents merging simulated TEST cases with normal/external cases
        if (type1 == "TEST") != (type2 == "TEST"):
            continue
        union(cid1, cid2)

    clusters_dict = defaultdict(list)
    for cid in case_ids:
        root = find(cid)
        clusters_dict[root].append(cid)

    multi_case_clusters = [members for members in clusters_dict.values() if len(members) > 1]

    # Inspect internal multi-alert correlation (e.g. Case 108080)
    consolidated_multi_alert_cases = []
    for cid, alerts in case_alerts_map.items():
        if len(alerts) > 1:
            consolidated_multi_alert_cases.append({
                "case_id": cid,
                "title": case_data_map[cid].get("displayName", ""),
                "alert_count": len(alerts),
                "alerts": [
                    {
                        "alert_id": a.get("name", "").split("/")[-1],
                        "rule_generator": a.get("ruleGenerator", ""),
                        "ticket_id": a.get("ticketId", "")
                    }
                    for a in alerts
                ],
                "entities": {k: list(v) for k, v in case_entities_map[cid].items()}
            })

    merge_results = []
    if execute_merge and multi_case_clusters:
        for cluster in multi_case_clusters:
            sorted_cases = sorted(cluster, key=lambda x: int(case_data_map[x].get("createTime", "0")))
            target_cid = sorted_cases[0]
            source_cids = sorted_cases[1:]
            print(f"[*] Merging cases {source_cids} into destination case {target_cid}...")
            try:
                body = {
                    "casesIds": [int(c) if str(c).isdigit() else c for c in sorted_cases],
                    "caseToMergeWith": int(target_cid) if str(target_cid).isdigit() else target_cid
                }
                res = await api_request("POST", "cases:merge", json_data=body)
                merge_results.append({
                    "cluster": cluster,
                    "target_case_id": target_cid,
                    "source_cases": source_cids,
                    "status": "MERGED",
                    "response": res
                })
            except Exception as e:
                merge_results.append({
                    "cluster": cluster,
                    "target_case_id": target_cid,
                    "source_cases": source_cids,
                    "status": "ERROR",
                    "error": str(e)
                })

    return {
        "scanned_cases_count": len(cases),
        "overlap_pairs_count": len(overlap_pairs),
        "overlap_pairs": list(overlap_pairs.values()),
        "multi_case_clusters": multi_case_clusters,
        "consolidated_multi_alert_cases": consolidated_multi_alert_cases,
        "merge_executions": merge_results
    }


def main():
    parser = argparse.ArgumentParser(description="SOAR Alert-to-Case Grouping and Merging Tool")
    parser.add_argument("--count", type=int, default=10, help="Number of cases to inspect (default: 10)")
    parser.add_argument("--min-overlap", type=int, default=1, help="Minimum shared entities to trigger overlap (default: 1)")
    parser.add_argument("--merge", action="store_true", help="Execute merge on detected clusters (default: False/Dry-Run)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON results")
    args = parser.parse_args()

    results = asyncio.run(run_grouping(count=args.count, execute_merge=args.merge, min_overlap=args.min_overlap))

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print("\n" + "=" * 70)
    print("🛡️  SOAR ALERT-TO-CASE GROUPING & OVERLAP REPORT")
    print("=" * 70)
    print(f"Total Cases Scanned: {results['scanned_cases_count']}")
    print(f"Overlapping Case Pairs Found: {results['overlap_pairs_count']}")
    print(f"Multi-Case Merge Candidates: {len(results['multi_case_clusters'])}")

    if results["consolidated_multi_alert_cases"]:
        print("\n🔹 Cases with Multiple Correlated Alerts (e.g. Previously Merged):")
        for cm in results["consolidated_multi_alert_cases"]:
            print(f"  • Case [{cm['case_id']}]: '{cm['title']}' ({cm['alert_count']} Alerts)")
            for al in cm["alerts"]:
                print(f"      - Alert {al['alert_id']}: {al['rule_generator']}")
            for etype, vals in cm["entities"].items():
                print(f"      - {etype}: {', '.join(vals[:3])}{'...' if len(vals) > 3 else ''}")

    if results["overlap_pairs"]:
        print("\n🔹 Overlapping Cases Identified Across Queue:")
        for op in results["overlap_pairs"]:
            print(f"  • Overlap between Case [{op['case_1']}] and Case [{op['case_2']}]:")
            print(f"      Case 1 Title: {op['case_1_title']}")
            print(f"      Case 2 Title: {op['case_2_title']}")
            print(f"      Shared Entities ({op['shared_count']}):")
            for etype, vals in op["shared_entities"].items():
                print(f"        - {etype}: {', '.join(vals)}")

    if results["multi_case_clusters"]:
        print("\n🔹 Recommended Merge Action:")
        for cluster in results["multi_case_clusters"]:
            target = cluster[0]
            sources = cluster[1:]
            print(f"  • Merge {sources} into target Case [{target}]")

    if results["merge_executions"]:
        print("\n🔹 Execution Results:")
        for me in results["merge_executions"]:
            print(f"  • Cluster {me['cluster']}: {me['status']} -> Target {me['target_case_id']}")


if __name__ == "__main__":
    main()
