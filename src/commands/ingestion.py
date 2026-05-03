import os
import json
import sys
from core.mcp_client import call_mcp_tool

def setup_ingestion_parser(subparsers):
    """Sets up the argparse subcommands for the 'ingestion' domain."""
    ingest_parser = subparsers.add_parser("ingestion", help="Manage data ingestion and parsing")
    ingest_subparsers = ingest_parser.add_subparsers(dest="ingest_command", required=True)

    # import_logs
    import_parser = ingest_subparsers.add_parser("import-logs", help="Import raw logs into Chronicle")
    import_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    import_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    import_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    import_parser.add_argument("--log-type", required=True, help="Chronicle log type identifier (e.g. OKTA)")
    import_parser.add_argument("--forwarder-id", required=True, help="Custom forwarder ID")
    import_parser.add_argument("--logs", required=True, help="JSON string representing a list of raw log strings")

    # list_feeds
    list_feeds_parser = ingest_subparsers.add_parser("list-feeds", help="List all configured data feeds")
    list_feeds_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    list_feeds_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    list_feeds_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")

    # get_feed
    get_feed_parser = ingest_subparsers.add_parser("get-feed", help="Get details for a specific data feed")
    get_feed_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    get_feed_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    get_feed_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    get_feed_parser.add_argument("--feed-id", required=True, help="The unique ID of the feed")

    # enable_feed
    enable_feed_parser = ingest_subparsers.add_parser("enable-feed", help="Enable a specific data feed")
    enable_feed_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    enable_feed_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    enable_feed_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    enable_feed_parser.add_argument("--feed-id", required=True, help="The unique ID of the feed to enable")

    # disable_feed
    disable_feed_parser = ingest_subparsers.add_parser("disable-feed", help="Disable a specific data feed")
    disable_feed_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    disable_feed_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    disable_feed_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    disable_feed_parser.add_argument("--feed-id", required=True, help="The unique ID of the feed to disable")

    # delete_feed
    delete_feed_parser = ingest_subparsers.add_parser("delete-feed", help="Delete a specific data feed")
    delete_feed_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    delete_feed_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    delete_feed_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    delete_feed_parser.add_argument("--feed-id", required=True, help="The unique ID of the feed to delete")

    # create_feed
    create_feed_parser = ingest_subparsers.add_parser("create-feed", help="Create a new data feed")
    create_feed_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    create_feed_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    create_feed_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    create_feed_parser.add_argument("--feed-json", required=True, help="JSON string representing the Feed configuration object")

    # update_feed
    update_feed_parser = ingest_subparsers.add_parser("update-feed", help="Update an existing data feed")
    update_feed_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    update_feed_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    update_feed_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    update_feed_parser.add_argument("--feed-id", required=True, help="The unique ID of the feed to update")
    update_feed_parser.add_argument("--feed-json", required=True, help="JSON string representing the updated Feed object")
    update_feed_parser.add_argument("--update-mask", required=True, help="Comma-separated list of fields to update (e.g. displayName,details.httpSettings)")

    # generate_feed_secret
    generate_secret_parser = ingest_subparsers.add_parser("generate-secret", help="Generate authentication secret for a feed")
    generate_secret_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    generate_secret_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    generate_secret_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    generate_secret_parser.add_argument("--feed-id", required=True, help="The unique ID of the feed")

    # list_integrations
    list_int_parser = ingest_subparsers.add_parser("list-integrations", help="List available integrations")
    list_int_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    list_int_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    list_int_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    list_int_parser.add_argument("--page-size", type=int, help="Maximum number of integrations to return")
    list_int_parser.add_argument("--filter", help="Filter string (e.g. Type, Custom)")
    list_int_parser.add_argument("--order-by", help="Comma-separated sort order")

    # list_integration_actions
    list_int_act_parser = ingest_subparsers.add_parser("list-integration-actions", help="List actions for a specific integration")
    list_int_act_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    list_int_act_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    list_int_act_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    list_int_act_parser.add_argument("--integration-id", required=True, help="ID of the integration (or '-' for all)")
    list_int_act_parser.add_argument("--page-size", type=int, help="Maximum number of actions to return")
    list_int_act_parser.add_argument("--filter", help="Filter string (e.g. DisplayName)")
    list_int_act_parser.add_argument("--order-by", help="Comma-separated sort order")

    # list_integration_instances
    list_int_inst_parser = ingest_subparsers.add_parser("list-integration-instances", help="List instances for a specific integration")
    list_int_inst_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    list_int_inst_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    list_int_inst_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    list_int_inst_parser.add_argument("--integration-id", required=True, help="ID of the integration (or '-' for all)")
    list_int_inst_parser.add_argument("--page-size", type=int, help="Maximum number of instances to return")
    list_int_inst_parser.add_argument("--filter", help="Filter string")
    list_int_inst_parser.add_argument("--order-by", help="Comma-separated sort order")

    # get_parser
    get_parser_parser = ingest_subparsers.add_parser("get-parser", help="Get details of a specific parser")
    get_parser_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    get_parser_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    get_parser_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    get_parser_parser.add_argument("--log-type", required=True, help="The log type (e.g. OKTA)")
    get_parser_parser.add_argument("--parser-id", required=True, help="The unique ID of the parser (e.g. pa_12345)")

    # run_parser
    run_parser_parser = ingest_subparsers.add_parser("run-parser", help="Run a parser against sample logs to test parsing logic")
    run_parser_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    run_parser_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    run_parser_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    run_parser_parser.add_argument("--log-type", required=True, help="The log type (e.g. OKTA)")
    run_parser_parser.add_argument("--parser-code", required=True, help="Plain text parser configuration code to test")
    run_parser_parser.add_argument("--sample-logs", required=True, help="JSON array string of sample log entries")
    run_parser_parser.add_argument("--parser-extension-code", help="Additional parser extension code if needed")
    run_parser_parser.add_argument("--statedump-allowed", action="store_true", help="Allow statedump filters in the parser")

    # activate_parser
    activate_parser_parser = ingest_subparsers.add_parser("activate-parser", help="Activate a parser for a specific log type")
    activate_parser_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    activate_parser_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    activate_parser_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    activate_parser_parser.add_argument("--log-type", required=True, help="The log type (e.g. CUSTOM_APP)")
    activate_parser_parser.add_argument("--parser-id", required=True, help="The unique ID of the parser to activate")

    # create_parser
    create_parser_parser = ingest_subparsers.add_parser("create-parser", help="Create a new custom parser")
    create_parser_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    create_parser_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    create_parser_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    create_parser_parser.add_argument("--log-type", required=True, help="The log type (e.g. CUSTOM_APP)")
    create_parser_parser.add_argument("--parser-code", required=True, help="Plain text parser configuration code (Logstash format)")
    create_parser_parser.add_argument("--validated", action="store_true", help="Set validatedOnEmptyLogs to true")

    # deactivate_parser
    deactivate_parser_parser = ingest_subparsers.add_parser("deactivate-parser", help="Deactivate a parser for a specific log type")
    deactivate_parser_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    deactivate_parser_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    deactivate_parser_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    deactivate_parser_parser.add_argument("--log-type", required=True, help="The log type (e.g. CUSTOM_APP)")
    deactivate_parser_parser.add_argument("--parser-id", required=True, help="The unique ID of the parser to deactivate")

    # list_parsers
    list_parsers_parser = ingest_subparsers.add_parser("list-parsers", help="List parsers for a given log type")
    list_parsers_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    list_parsers_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    list_parsers_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    list_parsers_parser.add_argument("--log-type", help="The log type (use '-' for all)")
    list_parsers_parser.add_argument("--page-size", type=int, help="Maximum number of parsers to return")
    list_parsers_parser.add_argument("--filter", help="A filter to apply to the list of parsers")

    # list_log_types
    list_log_types_parser = ingest_subparsers.add_parser("list-log-types", help="List available log types")
    list_log_types_parser.add_argument("--project-id", default=os.environ.get("SECOPS_PROJECT_ID"), help="GCP project ID")
    list_log_types_parser.add_argument("--customer-id", default=os.environ.get("SECOPS_CUSTOMER_ID"), help="Chronicle customer ID")
    list_log_types_parser.add_argument("--region", default=os.environ.get("SECOPS_REGION"), help="Chronicle region")
    list_log_types_parser.add_argument("--page-size", type=int, help="Maximum log types to return")
    list_log_types_parser.add_argument("--filter", help="A filter to apply")

def execute_ingestion_command(args):
    """Routes the command to the appropriate MCP tool call."""
    if args.ingest_command == "import-logs":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "logType": args.log_type,
            "forwarderId": args.forwarder_id
        }
        
        try:
            logs = json.loads(args.logs)
            if not isinstance(logs, list):
                raise ValueError("--logs must be a JSON array of strings")
            arguments["logs"] = logs
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing --logs: {e}", file=sys.stderr)
            sys.exit(1)
            
        return call_mcp_tool(args.project_id, args.region, "import_logs", arguments)

    elif args.ingest_command == "list-feeds":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region
        }
        return call_mcp_tool(args.project_id, args.region, "list_feeds", arguments)

    elif args.ingest_command == "create-parser":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "logType": args.log_type,
            "parserCode": args.parser_code
        }
        if getattr(args, 'validated', False): arguments["validatedOnEmptyLogs"] = True
        return call_mcp_tool(args.project_id, args.region, "create_parser", arguments)

    elif args.ingest_command == "list-log-types":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region
        }
        if getattr(args, 'page_size', None): arguments["pageSize"] = args.page_size
        if getattr(args, 'filter', None): arguments["filter"] = args.filter
        return call_mcp_tool(args.project_id, args.region, "list_log_types", arguments)

    elif args.ingest_command == "list-parsers":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region
        }
        if getattr(args, 'log_type', None): arguments["logType"] = args.log_type
        if getattr(args, 'page_size', None): arguments["pageSize"] = args.page_size
        if getattr(args, 'filter', None): arguments["filter"] = args.filter
        return call_mcp_tool(args.project_id, args.region, "list_parsers", arguments)

    elif args.ingest_command == "deactivate-parser":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "logType": args.log_type,
            "parserId": args.parser_id
        }
        return call_mcp_tool(args.project_id, args.region, "deactivate_parser", arguments)

    elif args.ingest_command == "activate-parser":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "logType": args.log_type,
            "parserId": args.parser_id
        }
        return call_mcp_tool(args.project_id, args.region, "activate_parser", arguments)

    elif args.ingest_command == "run-parser":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "logType": args.log_type,
            "parserCode": args.parser_code
        }
        
        if getattr(args, 'parser_extension_code', None): arguments["parserExtensionCode"] = args.parser_extension_code
        if getattr(args, 'statedump_allowed', False): arguments["statedumpAllowed"] = True

        try:
            sample_logs = json.loads(args.sample_logs)
            if not isinstance(sample_logs, list):
                raise ValueError("--sample-logs must be a JSON array of strings")
            arguments["sampleLogs"] = sample_logs
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing --sample-logs: {e}", file=sys.stderr)
            sys.exit(1)
            
        return call_mcp_tool(args.project_id, args.region, "run_parser", arguments)

    elif args.ingest_command == "get-feed":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "feedId": args.feed_id
        }
        return call_mcp_tool(args.project_id, args.region, "get_feed", arguments)

    elif args.ingest_command == "enable-feed":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "feedId": args.feed_id
        }
        return call_mcp_tool(args.project_id, args.region, "enable_feed", arguments)

    elif args.ingest_command == "disable-feed":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "feedId": args.feed_id
        }
        return call_mcp_tool(args.project_id, args.region, "disable_feed", arguments)

    elif args.ingest_command == "create-feed":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region
        }
        try:
            feed_obj = json.loads(args.feed_json)
            arguments["feed"] = feed_obj
        except json.JSONDecodeError:
            print("Error: --feed-json must be a valid JSON object", file=sys.stderr)
            sys.exit(1)
            
        return call_mcp_tool(args.project_id, args.region, "create_feed", arguments)

    elif args.ingest_command == "update-feed":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "feedId": args.feed_id,
            "updateMask": args.update_mask
        }
        try:
            feed_obj = json.loads(args.feed_json)
            arguments["feed"] = feed_obj
        except json.JSONDecodeError:
            print("Error: --feed-json must be a valid JSON object", file=sys.stderr)
            sys.exit(1)
            
        return call_mcp_tool(args.project_id, args.region, "update_feed", arguments)

    elif args.ingest_command == "delete-feed":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "feedId": args.feed_id
        }
        return call_mcp_tool(args.project_id, args.region, "delete_feed", arguments)

    elif args.ingest_command == "get-parser":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "logType": args.log_type,
            "parserId": args.parser_id
        }
        return call_mcp_tool(args.project_id, args.region, "get_parser", arguments)

    elif args.ingest_command == "list-integration-actions":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "integrationId": args.integration_id
        }
        if getattr(args, 'page_size', None): arguments["pageSize"] = args.page_size
        if getattr(args, 'filter', None): arguments["filter"] = args.filter
        if getattr(args, 'order_by', None): arguments["orderBy"] = args.order_by
        return call_mcp_tool(args.project_id, args.region, "list_integration_actions", arguments)

    elif args.ingest_command == "list-integrations":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region
        }
        if getattr(args, 'page_size', None): arguments["pageSize"] = args.page_size
        if getattr(args, 'filter', None): arguments["filter"] = args.filter
        if getattr(args, 'order_by', None): arguments["orderBy"] = args.order_by
        return call_mcp_tool(args.project_id, args.region, "list_integrations", arguments)

    elif args.ingest_command == "generate-secret":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "feedId": args.feed_id
        }
        return call_mcp_tool(args.project_id, args.region, "generate_feed_secret", arguments)

    elif args.ingest_command == "list-integration-instances":
        arguments = {
            "projectId": args.project_id,
            "customerId": args.customer_id,
            "region": args.region,
            "integrationId": args.integration_id
        }
        if getattr(args, 'page_size', None): arguments["pageSize"] = args.page_size
        if getattr(args, 'filter', None): arguments["filter"] = args.filter
        if getattr(args, 'order_by', None): arguments["orderBy"] = args.order_by
        return call_mcp_tool(args.project_id, args.region, "list_integration_instances", arguments)

    else:
        raise RuntimeError(f"Unhandled command '{args.ingest_command}'")
