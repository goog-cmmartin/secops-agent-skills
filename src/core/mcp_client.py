import requests
import uuid
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from .auth import get_auth_headers

def _is_transient_error(exception):
    """Return True if the exception is a transient network or HTTP error."""
    if isinstance(exception, requests.exceptions.HTTPError):
        return exception.response is not None and exception.response.status_code in (429, 500, 502, 503, 504)
    if isinstance(exception, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
        return True
    return False

@retry(
    retry=retry_if_exception(_is_transient_error),
    stop=stop_after_attempt(4),  # Initial attempt + 3 retries
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def _make_request(mcp_endpoint, headers, payload):
    response = requests.post(mcp_endpoint, headers=headers, json=payload)
    response.raise_for_status()
    return response

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
        "id": str(uuid.uuid4())
    }
    
    mcp_endpoint = f"https://{region}-chronicle.googleapis.com/mcp"
    
    try:
        response = _make_request(mcp_endpoint, headers, payload)
        
        result = response.json()
        if "error" in result:
            raise RuntimeError(f"MCP API Error: {result['error']}")
            
        return result
    except requests.exceptions.RequestException as e:
        error_msg = f"API request failed: {e}"
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f"\nResponse content: {e.response.text}"
        raise RuntimeError(error_msg) from e
