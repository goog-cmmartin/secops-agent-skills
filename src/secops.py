import argparse
import json
import sys
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from commands.cases import setup_cases_parser, execute_cases_command
from commands.data_tables import setup_data_tables_parser, execute_data_tables_command
from commands.threat_hunting import setup_threat_hunting_parser, execute_threat_hunting_command
from commands.ingestion import setup_ingestion_parser, execute_ingestion_command
from commands.playbooks import setup_playbooks_parser, execute_playbooks_command
from commands.detection_engineering import setup_detection_engineering_parser, execute_detection_engineering_command

def main():
    parser = argparse.ArgumentParser(description="Google SecOps Agent CLI")
    subparsers = parser.add_subparsers(dest="domain", required=True)
    
    # Register command domains
    setup_cases_parser(subparsers)
    setup_data_tables_parser(subparsers)
    setup_threat_hunting_parser(subparsers)
    setup_ingestion_parser(subparsers)
    setup_playbooks_parser(subparsers)
    setup_detection_engineering_parser(subparsers)
    
    args = parser.parse_args()
    
    # Validate required credentials for commands that define them
    has_project = hasattr(args, 'project_id')
    has_customer = hasattr(args, 'customer_id')
    has_region = hasattr(args, 'region')
    
    if has_project or has_customer or has_region:
        if not getattr(args, 'project_id', None) or not getattr(args, 'customer_id', None) or not getattr(args, 'region', None):
            print("Error: Missing required configuration.", file=sys.stderr)
            print("Please provide --project-id, --customer-id, and --region as CLI arguments,", file=sys.stderr)
            print("or set SECOPS_PROJECT_ID, SECOPS_CUSTOMER_ID, and SECOPS_REGION in your .env file.", file=sys.stderr)
            sys.exit(1)

    # Route execution to the correct domain handler
    try:
        if args.domain == "cases":
            result = execute_cases_command(args)
            print(json.dumps(result, indent=2))
        elif args.domain == "data-tables":
            result = execute_data_tables_command(args)
            print(json.dumps(result, indent=2))
        elif args.domain == "threat-hunting":
            result = execute_threat_hunting_command(args)
            print(json.dumps(result, indent=2))
        elif args.domain == "ingestion":
            result = execute_ingestion_command(args)
            print(json.dumps(result, indent=2))
        elif args.domain == "playbooks":
            result = execute_playbooks_command(args)
            print(json.dumps(result, indent=2))
        elif args.domain == "detection":
            result = execute_detection_engineering_command(args)
            print(json.dumps(result, indent=2))
        else:
            parser.print_help()
            sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()