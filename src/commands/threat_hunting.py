import os
import argparse
import json
import sys
from core.mcp_client import call_mcp_tool

def setup_threat_hunting_parser(subparsers):
    """Sets up the argparse subcommands for the 'threat-hunting' domain."""
    th_parser = subparsers.add_parser("threat-hunting", help="Threat hunting and enrichment tools")
    th_subparsers = th_parser.add_subparsers(dest="th_command", required=True)

    # summarize_entity
    summary_parser = th_subparsers.add_parser("summarize-entity", help="Summarize entity activity using a UDM query")
    summary_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    summary_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    summary_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    summary_parser.add_argument("--query", required=True, help="UDM query to find the entity (e.g. principal.ip = \"1.2.3.4\")")
    summary_parser.add_argument("--start-time", required=True, help="Start time in ISO 8601 format (e.g. 2024-01-01T00:00:00Z)")
    summary_parser.add_argument("--end-time", required=True, help="End time in ISO 8601 format (e.g. 2024-01-02T00:00:00Z)")

    # get_involved_entity
    involved_parser = th_subparsers.add_parser("involved-entity", help="Get details of an entity involved in an alert")
    involved_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    involved_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    involved_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    involved_parser.add_argument("--case-id", required=True, help="Numeric ID of the case")
    involved_parser.add_argument("--alert-id", required=True, dest="case_alert_id", help="Numeric ID of the case alert")
    involved_parser.add_argument("--entity-id", required=True, dest="involved_entity_id", help="The ID of the involved entity to retrieve")

    # list_involved_entities
    involved_list_parser = th_subparsers.add_parser("involved-entities", help="List entities involved in a case alert")
    involved_list_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    involved_list_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    involved_list_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    involved_list_parser.add_argument("--case-id", required=True, help="Numeric ID of the case")
    involved_list_parser.add_argument("--alert-id", required=True, dest="case_alert_id", help="Numeric ID of the case alert")
    involved_list_parser.add_argument("--page-size", type=int, help="Maximum number of entities to return")
    involved_list_parser.add_argument("--filter", help="A filter to apply to the list of entities")
    involved_list_parser.add_argument("--order-by", help="The field to order the results by")

    # search_entity
    search_parser = th_subparsers.add_parser("search-entity", help="Search for entities within the SOAR platform")
    search_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    search_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    search_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    search_parser.add_argument("--indicator", required=True, help="Indicator string to search for (e.g. 1.2.3.4)")
    search_parser.add_argument("--page-size", type=int, help="Maximum number of entities to return")

    # udm_search
    udm_parser = th_subparsers.add_parser("udm-search", help="Execute a raw UDM search")
    udm_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    udm_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    udm_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    udm_parser.add_argument("--query", required=True, help="UDM query string")
    udm_parser.add_argument("--start-time", required=True, help="Start time (ISO 8601)")
    udm_parser.add_argument("--end-time", required=True, help="End time (ISO 8601)")
    udm_parser.add_argument("--max-events", type=int, help="Maximum events to return (default 100, max 10000)")

    # translate_udm_query
    translate_parser = th_subparsers.add_parser("translate-udm", help="Translate natural language to a UDM query")
    translate_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    translate_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    translate_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    translate_parser.add_argument("--text", required=True, help="Natural language description of the events you want to find")

    # get_ioc_match
    ioc_parser = th_subparsers.add_parser("get-ioc-match", help="Get IoC matches from Chronicle SIEM")
    ioc_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    ioc_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    ioc_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    ioc_parser.add_argument("--start-time", required=True, help="Start time (ISO 8601)")
    ioc_parser.add_argument("--end-time", required=True, help="End time (ISO 8601)")
    ioc_parser.add_argument("--max-matches", type=int, help="Maximum number of matches to return")

    # list_security_alerts
    alerts_parser = th_subparsers.add_parser("list-alerts", help="List security alerts globally in SIEM")
    alerts_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    alerts_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    alerts_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    alerts_parser.add_argument("--start-time", required=True, help="Start time in ISO 8601 format")
    alerts_parser.add_argument("--end-time", required=True, help="End time in ISO 8601 format")
    alerts_parser.add_argument("--status-filter", help="Filter (e.g. 'feedbackSummary.status != \"CLOSED\"')")
    alerts_parser.add_argument("--max-alerts", type=int, help="Maximum number of alerts to return")

    # get_security_alert
    get_alert_parser = th_subparsers.add_parser("get-alert", help="Get a specific security alert by ID from SIEM")
    get_alert_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    get_alert_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    get_alert_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    get_alert_parser.add_argument("--alert-id", required=True, help="The exact alert ID (e.g. de_12345)")
    get_alert_parser.add_argument("--include-detections", action="store_true", help="Include detection details")

    # get_alert_latest_investigation
    get_alert_inv_parser = th_subparsers.add_parser("get-alert-latest-investigation", help="Retrieves the most recent Triage Agent investigation for a specific alert ID")
    get_alert_inv_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    get_alert_inv_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    get_alert_inv_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    get_alert_inv_parser.add_argument("--alert-id", required=True, help="The exact alert ID (e.g. de_12345)")

    # get_investigation_by_id
    get_inv_by_id_parser = th_subparsers.add_parser("get-investigation", help="Retrieves a single complete agent-generated investigation report by its full resource name")
    get_inv_by_id_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    get_inv_by_id_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    get_inv_by_id_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    get_inv_by_id_parser.add_argument("--investigation-id", required=True, help="The investigation ID")

    # trigger_investigation
    trigger_inv_parser = th_subparsers.add_parser("trigger-investigation", help="Manually starts a new SecOps Triage Agent investigation for a specific alert")
    trigger_inv_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    trigger_inv_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    trigger_inv_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    trigger_inv_parser.add_argument("--alert-id", required=True, help="The exact alert ID (e.g. de_12345)")

    # get_agent_settings
    agent_settings_parser = th_subparsers.add_parser("get-agent-settings", help="Retrieves the current configuration settings for the SecOps Investigation Agent")
    agent_settings_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    agent_settings_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    agent_settings_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")

    # update_security_alert
    update_alert_parser = th_subparsers.add_parser("update-alert", help="Update security alert attributes directly in SIEM")
    update_alert_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    update_alert_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    update_alert_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    update_alert_parser.add_argument("--alert-id", required=True, help="The exact alert ID")
    update_alert_parser.add_argument("--status", help="New status (e.g. CLOSED)")
    update_alert_parser.add_argument("--severity", help="New severity")
    update_alert_parser.add_argument("--priority", help="New priority")
    update_alert_parser.add_argument("--verdict", help="New verdict (e.g. false_positive)")
    update_alert_parser.add_argument("--comment", help="Analyst comment")
    update_alert_parser.add_argument("--root-cause", help="Root cause")
    update_alert_parser.add_argument("--reason", help="Reason")
    update_alert_parser.add_argument("--case-name", help="Case name")

def execute_threat_hunting_command(args):
    """Routes the command to the appropriate MCP tool call."""
    if args.th_command == "summarize-entity":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "query": args.query,
            "startTime": args.start_time,
            "endTime": args.end_time
        }
            
        return call_mcp_tool(args.project_id, args.region, "summarize_entity", arguments)

    elif args.th_command == "update-alert":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "alertId": args.alert_id
        }
        if getattr(args, 'status', None): arguments["status"] = args.status
        if getattr(args, 'severity', None): arguments["severity"] = args.severity
        if getattr(args, 'priority', None): arguments["priority"] = args.priority
        if getattr(args, 'verdict', None): arguments["verdict"] = args.verdict
        if getattr(args, 'comment', None): arguments["comment"] = args.comment
        if getattr(args, 'root_cause', None): arguments["rootCause"] = args.root_cause
        if getattr(args, 'reason', None): arguments["reason"] = args.reason
        if getattr(args, 'case_name', None): arguments["caseName"] = args.case_name
            
        return call_mcp_tool(args.project_id, args.region, "update_security_alert", arguments)

    elif args.th_command == "get-alert":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "alertId": args.alert_id
        }
        if getattr(args, 'include_detections', False): arguments["includeDetections"] = True
            
        return call_mcp_tool(args.project_id, args.region, "get_security_alert", arguments)

    elif args.th_command == "get-alert-latest-investigation":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "alertId": args.alert_id
        }
        return call_mcp_tool(args.project_id, args.region, "get_alert_latest_investigation", arguments)

    elif args.th_command == "get-investigation":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "investigationId": args.investigation_id
        }
        return call_mcp_tool(args.project_id, args.region, "get_investigation_by_id", arguments)

    elif args.th_command == "trigger-investigation":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "alertId": args.alert_id
        }
        return call_mcp_tool(args.project_id, args.region, "trigger_investigation", arguments)

    elif args.th_command == "get-agent-settings":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region
        }
        return call_mcp_tool(args.project_id, args.region, "get_agent_settings", arguments)

    elif args.th_command == "list-alerts":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "startTime": args.start_time,
            "endTime": args.end_time
        }
        if getattr(args, 'status_filter', None): arguments["statusFilter"] = args.status_filter
        if getattr(args, 'max_alerts', None): arguments["maxAlerts"] = args.max_alerts
            
        return call_mcp_tool(args.project_id, args.region, "list_security_alerts", arguments)

    elif args.th_command == "get-ioc-match":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "startTime": args.start_time,
            "endTime": args.end_time
        }
        if getattr(args, 'max_matches', None): arguments["maxMatches"] = args.max_matches
            
        return call_mcp_tool(args.project_id, args.region, "get_ioc_match", arguments)

    elif args.th_command == "search-entity":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "indicator": args.indicator
        }
        if getattr(args, 'page_size', None): arguments["pageSize"] = args.page_size
            
        return call_mcp_tool(args.project_id, args.region, "search_entity", arguments)

    elif args.th_command == "udm-search":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "query": args.query,
            "startTime": args.start_time,
            "endTime": args.end_time
        }
        if getattr(args, 'max_events', None): arguments["maxEvents"] = args.max_events
            
        return call_mcp_tool(args.project_id, args.region, "udm_search", arguments)

    elif args.th_command == "translate-udm":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "text": args.text
        }
        return call_mcp_tool(args.project_id, args.region, "translate_udm_query", arguments)

    elif args.th_command == "involved-entities":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "caseId": args.case_id,
            "caseAlertId": args.case_alert_id
        }
        if getattr(args, 'page_size', None): arguments["pageSize"] = args.page_size
        if getattr(args, 'filter', None): arguments["filter"] = args.filter
        if getattr(args, 'order_by', None): arguments["orderBy"] = args.order_by
            
        return call_mcp_tool(args.project_id, args.region, "list_involved_entities", arguments)
    elif args.th_command == "involved-entity":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "caseId": args.case_id,
            "caseAlertId": args.case_alert_id,
            "involvedEntityId": args.involved_entity_id
        }
            
        return call_mcp_tool(args.project_id, args.region, "get_involved_entity", arguments)

    else:
        raise RuntimeError(f"Unhandled command '{args.th_command}'")
