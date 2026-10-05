#!/usr/bin/env python3
"""Validation utility for Google SecOps GoogleSQL and PipedSQL queries.

Usage:
    python scripts/validate_sql.py "FROM events |> AGGREGATE COUNT(1) GROUP BY metadata.log_type"
    cat query.sql | python scripts/validate_sql.py
"""

import sys
import os

import json
import urllib.parse
import urllib.request

# Attempt to load .env if python-dotenv is installed
try:
    from dotenv import load_dotenv
    current_dir = os.path.dirname(os.path.abspath(__file__))
    possible_env_paths = [
        os.path.join(current_dir, "../../../.env"),  # repo root if in skills/secops-nl2sql/scripts
        os.path.join(current_dir, "../../../../.env"),
        os.path.join(os.getcwd(), ".env"),
    ]
    for env_path in possible_env_paths:
        if os.path.exists(env_path):
            load_dotenv(dotenv_path=os.path.abspath(env_path))
            break
except ImportError:
    pass

# Ensure workspace root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.abspath(os.path.join(current_dir, "../../../.."))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)


def validate_via_api(query_text: str, dialect: str = "DIALECT_SQL") -> dict:
    """Validates the query directly against Google SecOps REST API."""
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
            "Missing SECOPS_PROJECT_ID or SECOPS_CUSTOMER_ID. "
            "Please configure them in your environment or .env file."
        )

    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    if not credentials.valid:
        credentials.refresh(Request())

    url = (
        f"https://{region}-chronicle.googleapis.com/v1alpha/projects/{project_id}/"
        f"locations/{region}/instances/{customer_id}:validateQuery"
    )
    params = urllib.parse.urlencode({
        "dialect": dialect,
        "allowUnreplacedPlaceholders": "false",
        "rawQuery": query_text,
    })
    full_url = f"{url}?{params}"
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-goog-user-project": project_id,
    }

    req = urllib.request.Request(full_url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=30.0) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    if len(sys.argv) > 1:
        query_text = " ".join(sys.argv[1:])
    else:
        query_text = sys.stdin.read().strip()

    if not query_text:
        print("Error: No SQL query provided.", file=sys.stderr)
        sys.exit(1)

    # Try using GoogleSecOpsAdapter if available in parent environment
    try:
        from adapters.google_secops import GoogleSecOpsAdapter
        adapter = GoogleSecOpsAdapter()

        # If the query explicitly targets the ingestion table, use dashboard validation
        if "ingestion" in query_text.lower():
            try:
                # Append LIMIT 1 if no LIMIT is present to avoid long scans
                test_query = query_text
                if "limit" not in test_query.lower():
                    test_query += "\n|> LIMIT 1;" if "|>" in test_query else "\nLIMIT 1;"
                adapter.execute_dashboard_query(query_name="", query_text=test_query, dialect="SQL")
                print("STATUS: VALID (Dashboard Engine)")
                sys.exit(0)
            except Exception as e:
                print("STATUS: INVALID (Dashboard Engine)", file=sys.stderr)
                print(f"ERROR: {e}", file=sys.stderr)
                sys.exit(2)

        res = adapter.validate_query(query_text, dialect="DIALECT_SQL")
        if res.valid:
            print("STATUS: VALID (Search Engine)")
            sys.exit(0)
        elif "selecting from ingestion is not supported in search" in (res.error_message or ""):
            # Fallback to dashboard execution for ingestion references
            try:
                adapter.execute_dashboard_query(query_name="", query_text=query_text, dialect="SQL")
                print("STATUS: VALID (Dashboard Engine Fallback)")
                sys.exit(0)
            except Exception as e:
                print("STATUS: INVALID (Dashboard Engine)", file=sys.stderr)
                print(f"ERROR: {e}", file=sys.stderr)
                sys.exit(2)
        else:
            print("STATUS: INVALID", file=sys.stderr)
            print(f"ERROR: {res.error_message}", file=sys.stderr)
            sys.exit(2)
    except (ImportError, ModuleNotFoundError):
        # Fall back to direct REST API validation
        try:
            res_json = validate_via_api(query_text, dialect="DIALECT_SQL")
            err_text = res_json.get("errorText") or res_json.get("errorType")
            query_type = res_json.get("queryType")
            if query_type in ["QUERY_TYPE_UDM_QUERY", "QUERY_TYPE_ENTITY_GRAPH_QUERY", "QUERY_TYPE_STATS_QUERY"] and not err_text:
                print("STATUS: VALID (Search Engine)")
                sys.exit(0)
            elif err_text:
                print("STATUS: INVALID", file=sys.stderr)
                print(f"ERROR: {err_text}", file=sys.stderr)
                sys.exit(2)
            else:
                print("STATUS: VALID", file=sys.stderr)
                sys.exit(0)
        except Exception as e:
            print(f"API_ERROR: {e}", file=sys.stderr)
            sys.exit(3)
    except Exception as e:
        print(f"API_ERROR: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
