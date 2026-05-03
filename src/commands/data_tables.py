import os
import json
from core.mcp_client import call_mcp_tool

def setup_data_tables_parser(subparsers):
    """Sets up the argparse subcommands for the 'data-tables' domain."""
    dt_parser = subparsers.add_parser("data-tables", help="Manage SecOps Data Tables")
    dt_subparsers = dt_parser.add_subparsers(dest="dt_command", required=True)

    # create
    create_parser = dt_subparsers.add_parser("create", help="Create a new Data Table")
    create_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    create_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    create_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    create_parser.add_argument("--name", required=True, help="Unique name for the data table")
    create_parser.add_argument("--description", help="Description of the data table")
    create_parser.add_argument("--column-info", required=True, help="JSON string representing column definitions")

    # add_rows
    add_rows_parser = dt_subparsers.add_parser("add-rows", help="Add rows to an existing Data Table")
    add_rows_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    add_rows_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    add_rows_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    add_rows_parser.add_argument("--table-name", required=True, help="Name of the existing data table")
    add_rows_parser.add_argument("--rows", required=True, help="JSON string representing rows (e.g. [{\"values\": [\"a\", \"b\"]}])")

    # list
    list_parser = dt_subparsers.add_parser("list", help="List existing Data Tables")
    list_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    list_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    list_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    list_parser.add_argument("--page-size", type=int, help="Maximum number of data tables to return")

    # list_rows
    list_rows_parser = dt_subparsers.add_parser("list-rows", help="List rows from an existing Data Table")
    list_rows_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    list_rows_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    list_rows_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    list_rows_parser.add_argument("--table-name", required=True, help="Name of the existing data table")
    list_rows_parser.add_argument("--page-size", type=int, help="Maximum number of rows to return")
    list_rows_parser.add_argument("--filter", help="Filter string (case-insensitive substring match)")

    # delete_row
    delete_row_parser = dt_subparsers.add_parser("delete-row", help="Delete a specific row from a Data Table")
    delete_row_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    delete_row_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    delete_row_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    delete_row_parser.add_argument("--table-name", required=True, help="Name of the existing data table")
    delete_row_parser.add_argument("--row-id", required=True, help="The unique ID of the row to delete")

def execute_data_tables_command(args):
    """Routes the command to the appropriate MCP tool call."""
    if args.dt_command == "create":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "name": args.name
        }
        if args.description:
            arguments["description"] = args.description
            
        try:
            columns = json.loads(args.column_info)
            arguments["columnInfo"] = columns
        except json.JSONDecodeError as e:
            raise RuntimeError("Error: --column-info must be a valid JSON array") from e
            
        return call_mcp_tool(args.project_id, args.region, "create_data_table", arguments)

    elif args.dt_command == "list":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region
        }
        if getattr(args, 'page_size', None): arguments["pageSize"] = args.page_size
            
        return call_mcp_tool(args.project_id, args.region, "list_data_tables", arguments)

    elif args.dt_command == "delete-row":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "tableName": args.table_name,
            "rowId": args.row_id
        }
            
        return call_mcp_tool(args.project_id, args.region, "delete_data_table_row", arguments)

    elif args.dt_command == "list-rows":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "tableName": args.table_name
        }
        if getattr(args, 'page_size', None): arguments["pageSize"] = args.page_size
        if getattr(args, 'filter', None): arguments["filter"] = args.filter
            
        return call_mcp_tool(args.project_id, args.region, "list_data_table_rows", arguments)

    elif args.dt_command == "add-rows":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "tableName": args.table_name
        }
        
        try:
            rows = json.loads(args.rows)
            arguments["rows"] = rows
        except json.JSONDecodeError as e:
            raise RuntimeError("Error: --rows must be a valid JSON array") from e
            
        return call_mcp_tool(args.project_id, args.region, "add_rows_to_data_table", arguments)

    else:
        raise RuntimeError(f"Unhandled command '{args.dt_command}'")
