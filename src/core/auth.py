import google.auth
from google.auth.transport.requests import Request

def get_auth_headers(project_id):
    """Fetches ADC credentials and builds the authentication headers."""
    try:
        credentials, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        
        if not credentials.valid:
            credentials.refresh(Request())
            
        return {
            "Authorization": f"Bearer {credentials.token}",
            "x-goog-user-project": project_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    except Exception as e:
        raise RuntimeError(f"Error fetching credentials: {e}") from e