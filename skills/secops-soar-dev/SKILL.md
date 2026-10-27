---
name: secops-soar-dev
description: >-
  Develop, build, test, and deploy Google SecOps (Chronicle) SOAR custom integrations
  using the Content Hub specification, mp CLI utility, Workload Identity Federation,
  and native Vertex AI / Gemini tool grounding.
---

# Google SecOps SOAR Integration Development Skill (`secops-soar-dev`)

This skill provides an end-to-end operational guide, troubleshooting procedures, and development workflows for authoring, testing, packaging, and deploying Google SecOps (Chronicle) SOAR custom integrations using the modern Chronicle Content Hub architecture and the `mp` CLI utility.

---

## 🎯 When to Activate This Skill

Activate this skill when:
- Creating, modifying, or debugging Google SecOps SOAR custom integrations or actions.
- Building, packaging, or uploading integrations using the `mp` CLI utility (`content-hub/packages/mp`).
- Configuring or troubleshooting authentication (Workload Identity Federation, GCP Service Account impersonation, or Gemini API keys).
- Implementing native Gemini / Vertex AI agent features (Google Search Grounding, Code Execution sandbox, Memory Banks, or MCP servers).
- Packaging integrations for distribution via the Chronicle Web UI (`dist/<Name>.zip`) or syncing with GitHub repositories.

---

## 🛠️ Environment & Prerequisites

### 1. Workspace Layout
The standard development workspace (`secops_soar_dev_env`) contains:
- `integrations/<integration_name>/`: Source code and definitions for individual integrations.
- `content-hub/`: Clone of [chronicle/content-hub](https://github.com/chronicle/content-hub.git).
- `content-hub/packages/mp/`: The Chronicle Marketplace CLI (`mp`).
- `.venv/`: Virtual environment with Python 3.11, `mp`, `pytest`, `google-genai`, and dependency builders installed.

### 2. Network & Proxy Handling
In environments with intercepting HTTP proxies, direct API calls to Google APIs (`us-chronicle.googleapis.com`, Vertex AI, GitHub) will fail if proxy environment variables are set.
**Always strip proxy variables when executing network commands:**
```bash
env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY <COMMAND>
```
*Note: Run network commands with sandbox bypass enabled when making live external calls.*

### 3. Tenant Global Parameters
When targeting the user's Chronicle SOAR tenant, consistently use these parameters:
- **Customer ID**: `a556547c-1cff-43ef-a2e4-cf5b12a865df`
- **Region**: `us`
- **Project ID**: `sdl-preview-americas`

---

## 📦 Content Hub Integration Architecture

All modern integrations follow the Google Chronicle Content Hub format:

```text
integrations/<integration_name>/
├── definition.yaml        # Master manifest: parameters, categories, icon paths, version
├── pyproject.toml         # Dependencies, Python version requirements, package metadata
├── release_notes.yaml     # Release history and versioned changelogs
├── uv.lock                # Deterministic dependency lockfile
├── .python-version        # Target runtime (typically "3.11")
├── actions/               # Action Python entrypoints and corresponding YAML specs
│   ├── <action_name>.py   # Python execution script
│   └── <action_name>.yaml # Action parameters, output schema, and UI display settings
├── core/                  # Core managers, client abstractions, and business logic
│   ├── __init__.py
│   └── <ManagerName>.py
├── widgets/               # Optional custom HTML/JS Result View widgets
│   ├── <widget_name>.html # HTML/CSS/JS template for the SOAR Case Wall
│   └── <widget_name>.yaml # Widget definition and parameter mapping
├── resources/             # Official branding assets
│   ├── logo.svg           # High-resolution vector logo
│   └── image.png          # PNG fallback icon (e.g. 128x128)
└── tests/                 # Unit test suite
    ├── __init__.py
    ├── test_actions.py
    └── test_manager.py
```

### Key Manifest Files

#### `definition.yaml`
```yaml
api_version: "2.0"
identifier: GoogleADK
name: "GoogleADK"
description: "Integration description..."
categories:
  - "Artificial Intelligence"
author: "Author Name"
version: 2.1
python_version: "3.11"
is_custom: true
svg_logo_path: resources/logo.svg
image_path: resources/image.png
parameters:
  - name: "Gemini API Key"
    type: 1   # 1 = Password / Secret, 0 = String, 2 = Boolean
    mandatory: false
    description: "Gemini API Key..."
```

#### `pyproject.toml`
```toml
[project]
name = "soar-integration-google-adk"
version = "2.1"
description = "GoogleADK Integration for Google SecOps SOAR"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "google-genai>=1.0.0",
    "google-auth>=2.20.0",
]
```

#### `release_notes.yaml`
```yaml
- description: "Release changelog entry..."
  version: 2.1
  item_name: "GoogleADK"
  item_type: "Integration"
  new: false
  deprecated: false
  regressive: false
  removed: false
  publish_time: "2026-10-26"
```

---

## ⚡ The `mp` CLI Utility Workflows

The `mp` utility manages building, packaging, restructuring, and pushing custom integrations directly to Chronicle SOAR instances.

### 1. Configuration & Authentication
The CLI configuration is stored at `~/.config/mp/config.yaml` (or via `$XDG_CONFIG_HOME/mp/config.yaml`):

```yaml
tenants:
  default:
    customer_id: a556547c-1cff-43ef-a2e4-cf5b12a865df
    project_id: sdl-preview-americas
    region: us
    env: prod
current_tenant: default
```

To configure via CLI:
```bash
mp config set \
  --customer-id a556547c-1cff-43ef-a2e4-cf5b12a865df \
  --project-id sdl-preview-americas \
  --region us
```

### 2. Building an Integration
To validate dependencies, restructure code, vendor wheels, and generate a deployable `.zip` archive:
```bash
env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY \
  XDG_CONFIG_HOME="$(pwd)/.config" .venv/bin/mp build integration <integration_name> --custom
```
The compiled output is saved to:
`content-hub/out/content/response_integrations/custom/<IntegrationName>.zip`

### 3. Deploying / Pushing to Chronicle SOAR
To build and immediately upload the integration to your configured tenant:
```bash
env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY \
  XDG_CONFIG_HOME="$(pwd)/.config" .venv/bin/mp push integration <integration_name> --custom --keep-zip
```
Expected output:
```text
Zipped built integration at .../<IntegrationName>.zip
Upload result: {'integration': '...', 'integrationVersion': '2.1'}
✅ Integration pushed successfully.
```

---

## 🔐 Authentication & Workload Identity Federation (WIF)

In Google Kubernetes Engine (Chronicle SOAR runner containers), integrations can authenticate keylessly via Workload Identity impersonation.

### Token Pre-refresh & Cache Pattern
In `core/<Integration>Manager.py`:
```python
import google.auth
from google.auth.impersonated_credentials import Credentials as ImpersonatedCredentials
from google.auth.transport.requests import Request

def _get_cached_credentials(self):
    if not self.workload_identity_email:
        return None

    source_credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    target_credentials = ImpersonatedCredentials(
        source_credentials=source_credentials,
        target_principal=self.workload_identity_email,
        target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
        lifetime=3600,
    )
    try:
        # Pre-refresh token to validate credentials before initializing clients
        target_credentials.refresh(Request())
        return target_credentials
    except Exception as e:
        self.logger.error(f"Workload Identity token pre-refresh failed: {e}")
        return None
```

### IAM Permission Requirement
The runner identity inside the Chronicle cluster must have the **Service Account Token Creator** (`roles/iam.serviceAccountTokenCreator`) role on the target service account:
```bash
gcloud iam service-accounts add-iam-policy-binding \
  <TARGET_SERVICE_ACCOUNT_EMAIL> \
  --member="serviceAccount:<CHRONICLE_RUNNER_IDENTITY>" \
  --role="roles/iam.serviceAccountTokenCreator" \
  --project=<PROJECT_ID>
```
> [!TIP]
> If a `403 PERMISSION_DENIED` (`iam.serviceAccounts.getAccessToken`) error occurs, open the **IAM Policy Troubleshooter URL** output in the action log. It pinpoints the exact runner principal and provides a direct link to grant the missing role.

---

## ⚠️ Chronicle SOAR Runtime Quirks & Best Practices

### 1. `SiemplifyLogger` Lacks `.warning()`
Chronicle SOAR's runtime logger (`siemplify.LOGGER`) defines `.info()`, `.error()`, and `.debug()`, but **does not have a `.warning()` method**. Calling `siemplify.LOGGER.warning(...)` raises:
`AttributeError: 'SiemplifyLogger' object has no attribute 'warning'`

**Solution:** Always wrap `siemplify.LOGGER` in a `SafeLogger` adapter:
```python
class SafeLogger:
    def __init__(self, logger):
        self._logger = logger

    def info(self, msg: str, *args, **kwargs):
        if hasattr(self._logger, "info"):
            self._logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        # Redirect warning to info to prevent runtime crashes
        if hasattr(self._logger, "warning"):
            self._logger.warning(msg, *args, **kwargs)
        elif hasattr(self._logger, "info"):
            self._logger.info(f"[WARNING] {msg}", *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        if hasattr(self._logger, "error"):
            self._logger.error(msg, *args, **kwargs)
```

### 2. Vertex AI `google-genai` Native Tool Grounding
When calling `client.models.generate_content(...)`, tools **must be passed inside `types.GenerateContentConfig(tools=[...])`**. If omitted, the model runs ungrounded and will answer from outdated pre-training knowledge.

```python
from google.genai import types

client_tools = []

# Real-time Web Search Grounding:
if enable_google_search:
    client_tools.append(types.Tool(google_search=types.GoogleSearch()))

# Built-in Python Code Execution:
if enable_code_execution:
    client_tools.append(types.Tool(code_execution=types.ToolCodeExecution()))

# Custom callable tools:
if custom_tools:
    client_tools.extend(custom_tools)

config = types.GenerateContentConfig(
    system_instruction=instructions,
    max_output_tokens=4096,
    tools=client_tools if client_tools else None,
)

response = client.models.generate_content(
    model=self.model_name,
    contents=prompt,
    config=config,
)
```

### 3. Frontier Model Routing (`global` Location)
Frontier models such as `gemini-3.8-flash` and `gemini-4-argon` require the Vertex AI global endpoint:
```python
if any(frontier in self.model_name.lower() for frontier in ["3.8", "gemini-4", "argon"]):
    effective_location = "global"
else:
    effective_location = self.location or "us-central1"

client = genai.Client(
    vertexai=True,
    project=self.project_id,
    location=effective_location,
    credentials=creds,
)
```

---

## 🚢 Distribution & Git Repository Sync

### Single-Click Web UI Import (`dist/<Name>.zip`)
To allow users and analysts to import integrations without local tooling:
1. Ensure the compiled `.zip` file from `content-hub/out/.../<Name>.zip` is placed in `dist/<Name>.zip`.
2. Ensure `.gitignore` does not exclude the distribution package:
   ```gitignore
   *.zip
   !dist/*.zip
   ```
3. Users can import via **Response** > **Integrations** > **+ Add** > **Import Custom Integration**.

### Syncing to Remote Repositories
```bash
# Add, commit, and push changes to target repo
git add -A
git commit -m "feat: upgrade integration to vX.X with Content Hub architecture"
env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY git push origin main
```

---

## 📋 Standard Integration Release Checklist

1. **Code Changes**: Implement action logic and update core manager classes.
2. **Safe Logging**: Verify all logger calls use `SafeLogger`.
3. **Version Bump**: Increment version number synchronously in:
   - `definition.yaml`
   - `pyproject.toml`
   - `release_notes.yaml`
4. **Unit Tests**: Run test suite (`.venv/bin/pytest integrations/<name>/tests/`).
5. **Build & Package**: Execute `mp build integration <name> --custom`.
6. **Deploy & Verify**: Execute `mp push integration <name> --custom --keep-zip`.
7. **Copy to Dist**: Update `dist/<Name>.zip` for single-click UI import.
8. **Git Push**: Commit and push changes to upstream repository.
