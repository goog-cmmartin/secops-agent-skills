import requests
import sys
from .auth import get_auth_headers

def call_mcp_tool(project_id, region, tool_name, arguments):
    """Makes the HTTP JSON-RPC POST request to the Chronicle MCP endpoint."""
    headers = get_auth_headers(project_id)
    
    payload = {
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        },
        "jsonrpc": "2.0",
        "id": 1
    }
    
    mcp_endpoint = f"https://{region}-chronicle.googleapis.com/mcp"
    
    try:
        response = requests.post(mcp_endpoint, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}", file=sys.stderr)
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response content: {e.response.text}", file=sys.stderr)
        sys.exit(1)