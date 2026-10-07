#!/usr/bin/env python3
"""Bindplane REST API CLI and OTTL Processor Builder.

Authenticates using BINDPLANE_API_KEY and BINDPLANE_PROJECT_ID from .env
and supports:
  - list-configs / get-config <name>
  - list-processors / get-processor <name> / delete-processor <name>
  - list-sources / get-source <name>
  - get-processor-type <type>
  - build-filter: Validates OTTL condition and builds/applies a Bindplane
    `filter-by-condition:3` or `secops_filter:2` Processor resource.
  - build-transform: Validates OTTL statements and builds/applies a Bindplane
    `transform:2` Processor resource.
"""

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple
import urllib.error
import urllib.parse
import urllib.request

from dotenv import load_dotenv

# Ensure local validate_ottl import works regardless of working directory
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import validate_ottl  # noqa: E402


def load_bindplane_env() -> Dict[str, str]:
    """Loads Bindplane credentials from repo .env or environment variables."""
    repo_root = SCRIPT_DIR.parent.parent.parent
    env_file = repo_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        load_dotenv()

    api_key = os.environ.get("BINDPLANE_API_KEY", "").strip()
    project_id = os.environ.get("BINDPLANE_PROJECT_ID", "").strip()
    api_url = (
        os.environ.get("BINDPLANE_API_URL", "https://app.bindplane.com/v1")
        .strip()
        .rstrip("/")
    )

    if not api_key or not project_id:
        raise RuntimeError(
            "Missing BINDPLANE_API_KEY or BINDPLANE_PROJECT_ID in environment or .env file."
        )

    return {
        "api_key": api_key,
        "project_id": project_id,
        "api_url": api_url,
    }


def bindplane_request(
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Any:
    """Executes an authenticated HTTP request against the Bindplane REST API."""
    creds = load_bindplane_env()
    url = f"{creds['api_url']}/{path.lstrip('/')}"
    headers = {
        "X-Bindplane-Api-Key": creds["api_key"],
        "X-Bindplane-Account-ID": creds["project_id"],
        "Accept": "application/json",
    }
    data_bytes = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data_bytes = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            if not raw:
                return {}
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Bindplane API {method} {url} failed with HTTP {exc.code}: {err_body}"
        ) from exc


def build_filter_resource(
    name: str,
    condition: str,
    action: str = "exclude",
    processor_type: str = "filter-by-condition:3",
    telemetry_types: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Builds a validated Bindplane `filter-by-condition:3` or `secops_filter:2` Processor resource."""
    val = validate_ottl.validate_ottl_expression(
        condition, mode="condition", context="log"
    )
    if not val["valid"]:
        raise ValueError(
            f"OTTL condition validation failed:\n  " + "\n  ".join(val["errors"])
        )

    cleaned_cond = val["expression"]
    if processor_type == "secops_filter:2":
        return {
            "apiVersion": "bindplane.observiq.com/v1",
            "kind": "Processor",
            "metadata": {"name": name},
            "spec": {
                "type": "secops_filter:2",
                "parameters": [
                    {"name": "filter_method", "value": "Conditions"},
                    {"name": "log_conditions", "value": [cleaned_cond]},
                    {"name": "error_mode", "value": "ignore"},
                ],
            },
        }

    return {
        "apiVersion": "bindplane.observiq.com/v1",
        "kind": "Processor",
        "metadata": {"name": name},
        "spec": {
            "type": "filter-by-condition:3",
            "parameters": [
                {
                    "name": "telemetry_types",
                    "value": telemetry_types or ["Logs"],
                },
                {
                    "name": "action",
                    "value": action,
                },
                {
                    "name": "condition",
                    "value": {
                        "ottl": f"({cleaned_cond})",
                        "ui": {
                            "operator": "",
                            "statements": [
                                {
                                    "key": "",
                                    "match": "custom",
                                    "operator": "Equals",
                                    "value": cleaned_cond,
                                }
                            ],
                        },
                    },
                },
            ],
        },
    }


def build_transform_resource(
    name: str,
    statements: List[str],
    conditions: Optional[List[str]] = None,
    context: str = "log",
    telemetry_type: str = "Logs",
    error_mode: str = "ignore",
) -> Dict[str, Any]:
    """Builds a validated Bindplane `transform:2` Processor resource."""
    cleaned_statements: List[str] = []
    for stmt in statements:
        val = validate_ottl.validate_ottl_expression(
            stmt, mode="statement", context=context
        )
        if not val["valid"]:
            raise ValueError(
                f"OTTL statement validation failed for '{stmt}':\n  "
                + "\n  ".join(val["errors"])
            )
        cleaned_statements.append(val["expression"])

    cleaned_conditions: List[str] = []
    for cond in conditions or []:
        val = validate_ottl.validate_ottl_expression(
            cond, mode="condition", context=context
        )
        if not val["valid"]:
            raise ValueError(
                f"OTTL condition validation failed for '{cond}':\n  "
                + "\n  ".join(val["errors"])
            )
        cleaned_conditions.append(val["expression"])

    context_param_name = {
        "Logs": "logs_context",
        "Metrics": "metrics_context",
        "Traces": "traces_context",
    }.get(telemetry_type, "logs_context")

    return {
        "apiVersion": "bindplane.observiq.com/v1",
        "kind": "Processor",
        "metadata": {"name": name},
        "spec": {
            "type": "transform:2",
            "parameters": [
                {"name": "telemetry_type", "value": telemetry_type},
                {"name": context_param_name, "value": context},
                {"name": "error_mode", "value": error_mode},
                {"name": "conditions", "value": cleaned_conditions},
                {"name": "statements", "value": cleaned_statements},
            ],
        },
    }


def _extract_item_names(items: List[Any]) -> List[str]:
    names: List[str] = []
    for item in items:
        if isinstance(item, str):
            names.append(item)
        elif isinstance(item, dict):
            name = (
                item.get("name")
                or item.get("metadata", {}).get("name")
                or item.get("spec", {}).get("type")
                or item.get("type")
            )
            if name:
                names.append(name)
    return names


def cmd_list_configs(_args: argparse.Namespace) -> None:
    resp = bindplane_request("GET", "/configurations")
    configs = resp.get("configurations", []) if isinstance(resp, dict) else resp
    summary = []
    for cfg in configs:
        meta = cfg.get("metadata", {})
        spec = cfg.get("spec", {})
        sources_summary = []
        for s in spec.get("sources", []):
            if isinstance(s, dict):
                s_name = (
                    s.get("name")
                    or s.get("metadata", {}).get("name")
                    or s.get("spec", {}).get("type")
                )
                s_procs = _extract_item_names(s.get("processors", []))
                sources_summary.append({"source": s_name, "processors": s_procs})
            elif isinstance(s, str):
                sources_summary.append({"source": s, "processors": []})

        dest_summary = []
        for d in spec.get("destinations", []):
            if isinstance(d, dict):
                d_name = (
                    d.get("name")
                    or d.get("metadata", {}).get("name")
                    or d.get("spec", {}).get("type")
                )
                d_procs = _extract_item_names(d.get("processors", []))
                dest_summary.append({"destination": d_name, "processors": d_procs})
            elif isinstance(d, str):
                dest_summary.append({"destination": d, "processors": []})

        summary.append(
            {
                "name": meta.get("name"),
                "version": meta.get("version"),
                "platform": spec.get("platform"),
                "sources": sources_summary,
                "destinations": dest_summary,
            }
        )
    print(json.dumps(summary, indent=2))


def cmd_get_config(args: argparse.Namespace) -> None:
    cfg = bindplane_request(
        "GET", f"/configurations/{urllib.parse.quote(args.name)}"
    )
    print(json.dumps(cfg, indent=2))


def cmd_list_processors(_args: argparse.Namespace) -> None:
    resp = bindplane_request("GET", "/processors")
    procs = resp.get("processors", []) if isinstance(resp, dict) else resp
    summary = [
        {
            "name": p.get("metadata", {}).get("name"),
            "type": p.get("spec", {}).get("type"),
            "version": p.get("metadata", {}).get("version"),
        }
        for p in procs
        if isinstance(p, dict)
    ]
    print(json.dumps(summary, indent=2))


def cmd_get_processor(args: argparse.Namespace) -> None:
    proc = bindplane_request(
        "GET", f"/processors/{urllib.parse.quote(args.name)}"
    )
    print(json.dumps(proc, indent=2))


def cmd_delete_processor(args: argparse.Namespace) -> None:
    res = bindplane_request(
        "DELETE", f"/processors/{urllib.parse.quote(args.name)}"
    )
    print(
        json.dumps(
            {"deleted": args.name, "response": res},
            indent=2,
        )
    )


def cmd_list_sources(_args: argparse.Namespace) -> None:
    resp = bindplane_request("GET", "/sources")
    sources = resp.get("sources", []) if isinstance(resp, dict) else resp
    summary = [
        {
            "name": s.get("metadata", {}).get("name"),
            "type": s.get("spec", {}).get("type"),
            "version": s.get("metadata", {}).get("version"),
        }
        for s in sources
        if isinstance(s, dict)
    ]
    print(json.dumps(summary, indent=2))


def cmd_get_source(args: argparse.Namespace) -> None:
    src = bindplane_request("GET", f"/sources/{urllib.parse.quote(args.name)}")
    print(json.dumps(src, indent=2))


def cmd_get_processor_type(args: argparse.Namespace) -> None:
    pt = bindplane_request(
        "GET", f"/processor-types/{urllib.parse.quote(args.type)}"
    )
    print(json.dumps(pt, indent=2))


def cmd_build_filter(args: argparse.Namespace) -> None:
    resource = build_filter_resource(
        name=args.name,
        condition=args.condition,
        action=args.action,
        processor_type=args.processor_type,
    )
    if args.apply:
        apply_resp = bindplane_request("POST", "/apply", {"resources": [resource]})
        print(
            json.dumps(
                {"applied": True, "resource": resource, "response": apply_resp},
                indent=2,
            )
        )
    else:
        print(json.dumps(resource, indent=2))


def cmd_build_transform(args: argparse.Namespace) -> None:
    resource = build_transform_resource(
        name=args.name,
        statements=args.statement,
        conditions=args.condition,
        context=args.context,
        telemetry_type=args.telemetry_type,
        error_mode=args.error_mode,
    )
    if args.apply:
        apply_resp = bindplane_request("POST", "/apply", {"resources": [resource]})
        print(
            json.dumps(
                {"applied": True, "resource": resource, "response": apply_resp},
                indent=2,
            )
        )
    else:
        print(json.dumps(resource, indent=2))


def _resolve_processor_type(
    proc_item: Dict[str, Any], library_types: Dict[str, str]
) -> Tuple[str, str, List[Dict[str, Any]]]:
    """Returns (display_name, processor_type, parameters) for a processor entry in a config."""
    name = (
        proc_item.get("name")
        or proc_item.get("metadata", {}).get("name")
        or ""
    )
    ptype = (
        proc_item.get("type")
        or proc_item.get("spec", {}).get("type")
        or ""
    )
    params = (
        proc_item.get("parameters")
        or proc_item.get("spec", {}).get("parameters")
        or []
    )
    if not ptype and name:
        base_name = name.split(":")[0]
        ptype = library_types.get(base_name, "")
    display_name = name or ptype or "unnamed"
    return display_name, ptype, params


def cmd_audit_config(args: argparse.Namespace) -> None:
    """Audits a Bindplane configuration for body STRING/MAP state mismatches, ordering issues, and detection blind spots."""
    cfg_resp = bindplane_request(
        "GET", f"/configurations/{urllib.parse.quote(args.name)}"
    )
    cfg = cfg_resp.get("configuration", cfg_resp)
    procs_resp = bindplane_request("GET", "/processors")
    lib_procs = (
        procs_resp.get("processors", [])
        if isinstance(procs_resp, dict)
        else procs_resp
    )
    library_types: Dict[str, str] = {}
    for lp in lib_procs:
        if isinstance(lp, dict):
            lp_name = lp.get("metadata", {}).get("name", "")
            lp_type = lp.get("spec", {}).get("type", "")
            if lp_name and lp_type:
                library_types[lp_name] = lp_type

    spec = cfg.get("spec", {})
    source_audits = []
    total_issues = 0

    for src in spec.get("sources", []):
        if not isinstance(src, dict):
            continue
        src_name = src.get("name") or src.get("metadata", {}).get("name") or "unnamed_source"
        body_state = "string"
        seen_standardization = False
        steps = []
        source_issues: List[str] = []

        for idx, p in enumerate(src.get("processors", []), start=1):
            if not isinstance(p, dict):
                continue
            disp_name, ptype, params = _resolve_processor_type(p, library_types)
            param_map = {
                item.get("name"): item.get("value")
                for item in params
                if isinstance(item, dict)
            }
            step_info: Dict[str, Any] = {
                "step": idx,
                "processor": disp_name,
                "type": ptype,
                "body_state_on_entry": body_state,
                "errors": [],
                "warnings": [],
            }

            if ptype.startswith("parse_json"):
                if param_map.get("log_target_field_type", "Body") == "Body" and not param_map.get("log_body_target_field"):
                    body_state = "map"
                step_info["body_state_on_exit"] = body_state
            elif ptype.startswith("google_secops_standardization") or ptype.startswith("marshal"):
                body_state = "string"
                seen_standardization = True
                step_info["body_state_on_exit"] = body_state
            elif ptype.startswith("filter-by-condition"):
                cond_obj = param_map.get("condition", {})
                ottl_expr = ""
                if isinstance(cond_obj, dict):
                    stmts = cond_obj.get("ui", {}).get("statements", [])
                    if stmts and isinstance(stmts[0], dict) and stmts[0].get("value"):
                        ottl_expr = stmts[0]["value"]
                    else:
                        ottl_expr = cond_obj.get("ottl", "")
                step_info["ottl"] = ottl_expr
                if seen_standardization:
                    step_info["warnings"].append(
                        f"PIPELINE ORDERING: '{disp_name}' runs AFTER 'google_secops_standardization'. "
                        f"Filter early (immediately after 'parse_json' and before 'google_secops_standardization') so downstream steps process fewer records and parsed 'body[...]' fields remain accessible."
                    )
                if ottl_expr:
                    val = validate_ottl.validate_ottl_expression(
                        ottl_expr,
                        mode="condition",
                        context="log",
                        body_state=body_state,
                    )
                    step_info["errors"].extend(val["errors"])
                    step_info["warnings"].extend(val["warnings"])
                    # Also check if moving this filter to 'map' state (before standardization) would break it
                    if body_state == "string":
                        val_if_map = validate_ottl.validate_ottl_expression(
                            ottl_expr,
                            mode="condition",
                            context="log",
                            body_state="map",
                        )
                        for err in val_if_map["errors"]:
                            if "passes 'body' directly to a string function" in err:
                                step_info["warnings"].append(
                                    f"REORDER HAZARD: Moving this filter before 'google_secops_standardization' (where 'body' is a MAP) without rewriting it will break it: {err}"
                                )
                step_info["body_state_on_exit"] = body_state
            elif ptype.startswith("secops_filter"):
                conds = param_map.get("log_conditions", []) or []
                step_info["ottl_conditions"] = conds
                for c_expr in conds:
                    val = validate_ottl.validate_ottl_expression(
                        c_expr, mode="condition", context="log", body_state=body_state
                    )
                    step_info["errors"].extend(val["errors"])
                    step_info["warnings"].extend(val["warnings"])
                step_info["body_state_on_exit"] = body_state
            elif ptype.startswith("transform"):
                stmts = param_map.get("statements", []) or []
                ctx = param_map.get("logs_context", "log")
                step_info["ottl_statements"] = stmts
                for s_expr in stmts:
                    val = validate_ottl.validate_ottl_expression(
                        s_expr, mode="statement", context=ctx, body_state=body_state
                    )
                    step_info["errors"].extend(val["errors"])
                    step_info["warnings"].extend(val["warnings"])
                step_info["body_state_on_exit"] = body_state
            else:
                step_info["body_state_on_exit"] = body_state

            total_issues += len(step_info["errors"]) + len(step_info["warnings"])
            for e in step_info["errors"]:
                source_issues.append(f"Step {idx} ({disp_name}) ERROR: {e}")
            for w in step_info["warnings"]:
                source_issues.append(f"Step {idx} ({disp_name}) WARNING: {w}")
            steps.append(step_info)

        source_audits.append(
            {
                "source": src_name,
                "issue_count": len(source_issues),
                "issues_summary": source_issues,
                "pipeline_steps": steps,
            }
        )

    print(
        json.dumps(
            {
                "configuration": args.name,
                "total_findings": total_issues,
                "sources": source_audits,
            },
            indent=2,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect Bindplane configurations/processors and build/apply validated OTTL processors."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-configs", help="List all Bindplane configurations.")
    p_get_cfg = subparsers.add_parser(
        "get-config", help="Get a specific Bindplane configuration by name."
    )
    p_get_cfg.add_argument("name", help="Configuration name (e.g., ZEEK).")

    p_audit_cfg = subparsers.add_parser(
        "audit-config",
        help="Audit a Bindplane configuration for OTTL body state mismatches, processor ordering bugs, and detection blind spots.",
    )
    p_audit_cfg.add_argument("name", help="Configuration name (e.g., ZEEK).")

    subparsers.add_parser(
        "list-processors", help="List all processors in the Bindplane library."
    )
    p_get_proc = subparsers.add_parser(
        "get-processor", help="Get a specific processor by name."
    )
    p_get_proc.add_argument("name", help="Processor name.")

    p_del_proc = subparsers.add_parser(
        "delete-processor", help="Delete a processor from the Bindplane library."
    )
    p_del_proc.add_argument("name", help="Processor name.")

    subparsers.add_parser("list-sources", help="List all sources in Bindplane.")
    p_get_src = subparsers.add_parser(
        "get-source", help="Get a specific source by name."
    )
    p_get_src.add_argument("name", help="Source name.")

    p_get_pt = subparsers.add_parser(
        "get-processor-type",
        help="Get parameter schema for a Bindplane processor type (e.g., transform:2, filter-by-condition:3).",
    )
    p_get_pt.add_argument("type", help="Processor type ID (e.g., transform:2).")

    p_filter = subparsers.add_parser(
        "build-filter",
        help="Validate an OTTL condition and build/apply a Bindplane filter processor.",
    )
    p_filter.add_argument("--name", required=True, help="Processor metadata.name.")
    p_filter.add_argument(
        "--condition", required=True, help="OTTL boolean filter condition."
    )
    p_filter.add_argument(
        "--action",
        choices=["exclude", "include"],
        default="exclude",
        help="Filter action for filter-by-condition:3 (default: exclude).",
    )
    p_filter.add_argument(
        "--processor-type",
        choices=["filter-by-condition:3", "secops_filter:2"],
        default="filter-by-condition:3",
        help="Bindplane processor type (default: filter-by-condition:3).",
    )
    p_filter.add_argument(
        "--apply",
        action="store_true",
        help="Apply the processor to the live Bindplane project via POST /v1/apply.",
    )

    p_transform = subparsers.add_parser(
        "build-transform",
        help="Validate OTTL statements and build/apply a Bindplane transform:2 processor.",
    )
    p_transform.add_argument("--name", required=True, help="Processor metadata.name.")
    p_transform.add_argument(
        "--statement",
        action="append",
        required=True,
        help="OTTL Editor statement (can be specified multiple times).",
    )
    p_transform.add_argument(
        "--condition",
        action="append",
        default=[],
        help="Optional OTTL boolean condition for the processor (can be specified multiple times).",
    )
    p_transform.add_argument(
        "--context",
        choices=["log", "resource", "datapoint", "metric", "span", "spanevent"],
        default="log",
        help="OTTL context (default: log).",
    )
    p_transform.add_argument(
        "--telemetry-type",
        choices=["Logs", "Metrics", "Traces"],
        default="Logs",
        help="Telemetry type (default: Logs).",
    )
    p_transform.add_argument(
        "--error-mode",
        choices=["ignore", "silent", "propagate"],
        default="ignore",
        help="OTTL error mode (default: ignore).",
    )
    p_transform.add_argument(
        "--apply",
        action="store_true",
        help="Apply the processor to the live Bindplane project via POST /v1/apply.",
    )

    args = parser.parse_args()
    dispatch = {
        "list-configs": cmd_list_configs,
        "get-config": cmd_get_config,
        "audit-config": cmd_audit_config,
        "list-processors": cmd_list_processors,
        "get-processor": cmd_get_processor,
        "delete-processor": cmd_delete_processor,
        "list-sources": cmd_list_sources,
        "get-source": cmd_get_source,
        "get-processor-type": cmd_get_processor_type,
        "build-filter": cmd_build_filter,
        "build-transform": cmd_build_transform,
    }
    try:
        dispatch[args.command](args)
        return 0
    except Exception as exc:  # pylint: disable=broad-except
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
