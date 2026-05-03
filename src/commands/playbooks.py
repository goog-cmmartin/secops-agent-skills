import os
import argparse
import json
import sys
from core.mcp_client import call_mcp_tool

def setup_playbooks_parser(subparsers):
    """Sets up the argparse subcommands for the 'playbooks' domain."""
    playbooks_parser = subparsers.add_parser("playbooks", help="Manage and execute SOAR Playbooks")
    playbooks_subparsers = playbooks_parser.add_subparsers(dest="playbook_command", required=True)

    # list_instances
    list_inst_parser = playbooks_subparsers.add_parser("list-instances", help="Lists all execution instances of playbooks for a case/alert")
    list_inst_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    list_inst_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    list_inst_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    list_inst_parser.add_argument("--case-id", required=True, help="Numeric ID of the case")
    list_inst_parser.add_argument("--alert-group-id", required=True, dest="alert_group_identifier", help="Alert Group Identifier string")

    # list_playbooks
    list_pb_parser = playbooks_subparsers.add_parser("list", help="List all configured playbooks")
    list_pb_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    list_pb_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    list_pb_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    list_pb_parser.add_argument("--playbook-types", required=True, help="Comma-separated types (e.g. REGULAR,NESTED)")

    # fetch_alert_data
    fetch_alert_parser = playbooks_subparsers.add_parser("fetch-alert-data", help="Retrieves a comprehensive profile of a specific SIEM alert")
    fetch_alert_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    fetch_alert_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    fetch_alert_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    fetch_alert_parser.add_argument("--siem-alert-id", required=True, help="The SIEM alert ID to fetch data for")

    # fetch_enrichment_actions
    fetch_enrichment_parser = playbooks_subparsers.add_parser("fetch-enrichment-actions", help="Retrieves a curated list of SOAR integration actions available for enriching a specific SIEM alert")
    fetch_enrichment_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    fetch_enrichment_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    fetch_enrichment_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    fetch_enrichment_parser.add_argument("--siem-alert-id", required=True, help="The SIEM alert ID")

    # execute_actions
    execute_actions_parser = playbooks_subparsers.add_parser("execute-actions", help="Executes one or more enrichment actions on a specific SIEM alert")
    execute_actions_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    execute_actions_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    execute_actions_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    execute_actions_parser.add_argument("--siem-alert-id", required=True, help="The SIEM alert ID")
    execute_actions_parser.add_argument("--actions", required=True, help="JSON string of actions to execute")

def execute_playbooks_command(args):
    """Routes the command to the appropriate MCP tool call."""
    if args.playbook_command == "list-instances":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "caseId": args.case_id,
            "alertGroupIdentifier": args.alert_group_identifier
        }
        return call_mcp_tool(args.project_id, args.region, "list_playbook_instances", arguments)
        
    elif args.playbook_command == "list":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "playbookTypes": args.playbook_types.split(',')
        }
        return call_mcp_tool(args.project_id, args.region, "list_playbooks", arguments)

    elif args.playbook_command == "fetch-alert-data":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "siemAlertId": args.siem_alert_id
        }
        return call_mcp_tool(args.project_id, args.region, "fetch_alert_data", arguments)

    elif args.playbook_command == "fetch-enrichment-actions":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "siemAlertId": args.siem_alert_id
        }
        return call_mcp_tool(args.project_id, args.region, "fetch_enrichment_actions", arguments)

    elif args.playbook_command == "execute-actions":
        try:
            actions_list = json.loads(args.actions)
        except json.JSONDecodeError:
            print("Error: --actions must be a valid JSON array.", file=sys.stderr)
            sys.exit(1)

        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "siemAlertId": args.siem_alert_id,
            "actions": actions_list
        }
        return call_mcp_tool(args.project_id, args.region, "execute_actions", arguments)

    else:
        raise RuntimeError(f"Unhandled command '{args.playbook_command}'")
