import os
from core.mcp_client import call_mcp_tool

def setup_cases_parser(subparsers):
    """Sets up the argparse subcommands for the 'cases' domain."""
    cases_parser = subparsers.add_parser("cases", help="Manage SecOps Cases")
    cases_subparsers = cases_parser.add_subparsers(dest="case_command", required=True)

    # list_cases
    list_parser = cases_subparsers.add_parser("list", help="List cases")
    list_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    list_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    list_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    list_parser.add_argument("--page-size", type=int, help="Maximum cases to return")
    list_parser.add_argument("--filter", help="Filter string")
    list_parser.add_argument("--order-by", help="Order by string")

    # get_case
    get_parser = cases_subparsers.add_parser("get", help="Get a single case")
    get_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    get_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    get_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    get_parser.add_argument("--case-id", required=True, help="Numeric ID of the case")
    get_parser.add_argument("--expand", help="Comma-separated relations (e.g. tasks,tags)")

    # comments
    comments_parser = cases_subparsers.add_parser("comments", help="List comments for a case")
    comments_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    comments_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    comments_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    comments_parser.add_argument("--case-id", required=True, help="Numeric ID of the case")
    comments_parser.add_argument("--page-size", type=int, help="Maximum comments to return")
    comments_parser.add_argument("--filter", help="Filter string")
    comments_parser.add_argument("--order-by", help="Order by string")

    # update_case
    update_parser = cases_subparsers.add_parser("update", help="Update a case")
    update_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    update_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    update_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    update_parser.add_argument("--case-id", required=True, help="Numeric ID of the case to update")
    update_parser.add_argument("--display-name", help="New display name")
    update_parser.add_argument("--stage", help="New stage (e.g. Triage, Incident)")
    update_parser.add_argument("--priority", help="New priority (e.g. PRIORITY_HIGH)")
    update_parser.add_argument("--assignee", help="User or @SocRole to assign")
    update_parser.add_argument("--description", help="Case description")
    update_parser.add_argument("--type", help="Case type")
    update_parser.add_argument("--environment", help="Case environment")
    update_parser.add_argument("--important", action="store_true", help="Set important to true")
    update_parser.add_argument("--incident", action="store_true", help="Set incident to true")
    
    # alert
    alert_parser = cases_subparsers.add_parser("alert", help="Get a specific case alert")
    alert_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    alert_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    alert_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    alert_parser.add_argument("--case-id", required=True, help="Numeric ID of the case")
    alert_parser.add_argument("--alert-id", required=True, dest="case_alert_id", help="Numeric ID of the case alert")
    alert_parser.add_argument("--expand", help="Comma-separated relations (e.g. sla,involvedRelations)")
    
    # alerts
    alerts_parser = cases_subparsers.add_parser("alerts", help="List alerts for a specific case")
    alerts_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    alerts_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    alerts_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    alerts_parser.add_argument("--case-id", required=True, help="Numeric ID of the case")
    alerts_parser.add_argument("--page-size", type=int, help="Maximum alerts to return")
    alerts_parser.add_argument("--filter", help="Filter string (e.g. Status, Priority)")
    alerts_parser.add_argument("--order-by", help="Order by string (e.g. CreateTime desc)")

    # update_alert
    update_alert_parser = cases_subparsers.add_parser("update-alert", help="Update a case alert")
    update_alert_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    update_alert_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    update_alert_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    update_alert_parser.add_argument("--case-id", required=True, help="Numeric ID of the case")
    update_alert_parser.add_argument("--alert-id", required=True, dest="case_alert_id", help="Numeric ID of the case alert")
    update_alert_parser.add_argument("--priority", help="New priority (e.g. HIGH)")
    update_alert_parser.add_argument("--status", help="New status (e.g. OPEN or CLOSE)")
    update_alert_parser.add_argument("--close-reason", help="Close reason (if closing)")
    update_alert_parser.add_argument("--close-comment", help="Close comment (if closing)")

    # create_comment
    add_comment_parser = cases_subparsers.add_parser("add-comment", help="Add a comment to a case")
    add_comment_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    add_comment_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    add_comment_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    add_comment_parser.add_argument("--case-id", required=True, help="Numeric ID of the case")
    add_comment_parser.add_argument("--comment", required=True, help="The content of the comment to add")

    # bulk_close
    bulk_close_parser = cases_subparsers.add_parser("bulk-close", help="Bulk close multiple cases")
    bulk_close_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    bulk_close_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    bulk_close_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    bulk_close_parser.add_argument("--cases-ids", required=True, help="Comma-separated list of case IDs (e.g. 123,456)")
    bulk_close_parser.add_argument("--close-reason", required=True, help="Reason (MALICIOUS, NOT_MALICIOUS, MAINTENANCE, INCONCLUSIVE, UNKNOWN)")
    bulk_close_parser.add_argument("--root-cause", help="Root cause explanation")
    bulk_close_parser.add_argument("--close-comment", help="Close comment to add to each case")

    # get_connector_event
    connector_event_parser = cases_subparsers.add_parser("connector-event", help="Get a specific connector event")
    connector_event_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    connector_event_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    connector_event_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    connector_event_parser.add_argument("--case-id", required=True, help="Numeric ID of the case")
    connector_event_parser.add_argument("--alert-id", required=True, dest="case_alert_id", help="Numeric ID of the case alert")
    connector_event_parser.add_argument("--event-id", required=True, dest="connector_event_id", help="Numeric ID of the connector event")
    connector_event_parser.add_argument("--expand-data", action="store_true", help="Expand event JSON data")

    # connector_events
    connector_events_parser = cases_subparsers.add_parser("connector-events", help="List connector events for an alert")
    connector_events_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    connector_events_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    connector_events_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    connector_events_parser.add_argument("--case-id", required=True, help="Numeric ID of the case")
    connector_events_parser.add_argument("--alert-id", required=True, dest="case_alert_id", help="Numeric ID of the case alert")
    connector_events_parser.add_argument("--page-size", type=int, help="Maximum events to return")
    connector_events_parser.add_argument("--filter", help="Filter string")
    connector_events_parser.add_argument("--order-by", help="Order by string")
    connector_events_parser.add_argument("--expand-data", action="store_true", help="Expand event JSON data")

def execute_cases_command(args):
    """Routes the command to the appropriate MCP tool call."""
    if args.case_command == "list":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region
        }
        if args.page_size: arguments["pageSize"] = args.page_size
        if args.filter: arguments["filter"] = args.filter
        if getattr(args, 'order_by', None): arguments["orderBy"] = args.order_by
        
        return call_mcp_tool(args.project_id, args.region, "list_cases", arguments)

    elif args.case_command == "get":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "caseId": args.case_id
        }
        if args.expand: arguments["expand"] = args.expand
        
        return call_mcp_tool(args.project_id, args.region, "get_case", arguments)

    elif args.case_command == "update":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "caseId": args.case_id
        }
        if getattr(args, 'display_name', None): arguments["displayName"] = args.display_name
        if getattr(args, 'stage', None): arguments["stage"] = args.stage
        if getattr(args, 'priority', None): arguments["priority"] = args.priority
        if getattr(args, 'assignee', None): arguments["assignee"] = args.assignee
        if getattr(args, 'description', None): arguments["description"] = args.description
        if getattr(args, 'type', None): arguments["type"] = args.type
        if getattr(args, 'environment', None): arguments["environment"] = args.environment
        if getattr(args, 'important', False): arguments["important"] = True
        if getattr(args, 'incident', False): arguments["incident"] = True
        
        return call_mcp_tool(args.project_id, args.region, "update_case", arguments)

    elif args.case_command == "comments":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "caseId": args.case_id
        }
        if args.page_size: arguments["pageSize"] = args.page_size
        if getattr(args, 'filter', None): arguments["filter"] = args.filter
        if getattr(args, 'order_by', None): arguments["orderBy"] = args.order_by
        
        return call_mcp_tool(args.project_id, args.region, "list_case_comments", arguments)

    elif args.case_command == "bulk-close":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "casesIds": [int(cid.strip()) for cid in args.cases_ids.split(',')],
            "closeReason": args.close_reason
        }
        if getattr(args, 'root_cause', None): arguments["rootCause"] = args.root_cause
        if getattr(args, 'close_comment', None): arguments["closeComment"] = args.close_comment
        
        return call_mcp_tool(args.project_id, args.region, "execute_bulk_close_case", arguments)

    elif args.case_command == "add-comment":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "caseId": args.case_id,
            "comment": args.comment
        }
        return call_mcp_tool(args.project_id, args.region, "create_case_comment", arguments)

    elif args.case_command == "connector-event":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "caseId": args.case_id,
            "caseAlertId": args.case_alert_id,
            "connectorEventId": args.connector_event_id
        }
        if getattr(args, 'expand_data', False): arguments["expandEventJsonData"] = True
        
        return call_mcp_tool(args.project_id, args.region, "get_connector_event", arguments)

    elif args.case_command == "connector-events":
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
        if getattr(args, 'expand_data', False): arguments["expandEventJsonData"] = True
        
        return call_mcp_tool(args.project_id, args.region, "list_connector_events", arguments)

    elif args.case_command == "update-alert":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "caseId": args.case_id,
            "caseAlertId": args.case_alert_id
        }
        if getattr(args, 'priority', None): arguments["priority"] = args.priority
        if getattr(args, 'status', None): arguments["status"] = args.status
        
        if getattr(args, 'close_reason', None) or getattr(args, 'close_comment', None):
            closure_details = {}
            if getattr(args, 'close_reason', None): closure_details["reason"] = args.close_reason
            if getattr(args, 'close_comment', None): closure_details["comment"] = args.close_comment
            arguments["closureDetails"] = closure_details
            
        return call_mcp_tool(args.project_id, args.region, "update_case_alert", arguments)

    elif args.case_command == "alerts":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "caseId": args.case_id
        }
        if getattr(args, 'page_size', None): arguments["pageSize"] = args.page_size
        if getattr(args, 'filter', None): arguments["filter"] = args.filter
        if getattr(args, 'order_by', None): arguments["orderBy"] = args.order_by
        
        return call_mcp_tool(args.project_id, args.region, "list_case_alerts", arguments)

    elif args.case_command == "alert":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "caseId": args.case_id,
            "caseAlertId": args.case_alert_id
        }
        if getattr(args, 'expand', None): arguments["expand"] = args.expand
        
        return call_mcp_tool(args.project_id, args.region, "get_case_alert", arguments)

    else:
        raise RuntimeError(f"Unhandled command '{args.case_command}'")
