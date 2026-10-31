---
name: secops-soar-dev
description: >-
  Develop, build, test, and deploy Google SecOps (Chronicle) SOAR custom integrations,
  actions, scheduled jobs, HTML widgets, and playbooks (including Reaction Triggers)
  using the Content Hub specification, mp CLI utility, Workload Identity Federation,
  and native Vertex AI / Gemini tool grounding.
---

# Google SecOps SOAR Integration & Playbook Development Skill (`secops-soar-dev`)

This skill provides an end-to-end operational guide, troubleshooting procedures, and development workflows for authoring, testing, packaging, and deploying Google SecOps (Chronicle) SOAR custom integrations, actions, scheduled jobs, HTML widgets, and playbooks using the modern Chronicle Content Hub architecture and the `mp` CLI utility.

---

## 🎯 When to Activate This Skill

Activate this skill when:
- Creating, modifying, or debugging Google SecOps SOAR custom integrations, actions, scheduled jobs (`jobs/`), or custom HTML widgets (`widgets/`).
- Authoring, inspecting, or updating SOAR Playbooks (`CASE` vs. `ALERT` scope, Reaction Triggers such as `CASE_TAG_ADDED`, and in-place Case Overview widget re-runs).
- Building, validating, packaging, or uploading integrations using the `mp` CLI utility (`content-hub/packages/mp`).
- Configuring or troubleshooting authentication (Workload Identity Federation, GCP Service Account impersonation, or Gemini API keys).
- Implementing native Gemini / Vertex AI agent features (Google Search Grounding, Code Execution sandbox, Memory Banks, or MCP servers) or Chronicle SIEM <-> SOAR entity/detection correlation workflows.
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

### 3. Tenant Configuration (Environment Variables or .env)
When targeting a Chronicle SOAR tenant, configure the tenant connection parameters using environment variables or a `.env` file in the project root:

| Parameter | Environment Variable | Description | Example |
| :--- | :--- | :--- | :--- |
| **Customer ID** | `SECOPS_CUSTOMER_ID` | Chronicle customer UUID | `00000000-0000-0000-0000-000000000000` |
| **Project ID** | `SECOPS_PROJECT_ID` | GCP Project ID hosting Chronicle instance | `my-chronicle-project` |
| **Region** | `SECOPS_REGION` | Chronicle instance region (`us`, `europe-west3`, etc.) | `us` |

These can be set in your shell environment:
```bash
export SECOPS_CUSTOMER_ID="<your-customer-uuid>"
export SECOPS_PROJECT_ID="<your-project-id>"
export SECOPS_REGION="us"
```
Or added to a local `.env` file:
```ini
SECOPS_CUSTOMER_ID=your-customer-uuid
SECOPS_PROJECT_ID=your-project-id
SECOPS_REGION=us
```

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
├── jobs/                  # Optional scheduled SOAR jobs (compiled to Jobs/ by mp build)
│   ├── <job_name>.py      # SiemplifyJob Python script
│   └── <job_name>.yaml    # Job schedule parameters and defaults
├── core/                  # Core managers, client abstractions, and bundled data files
│   ├── __init__.py
│   ├── <ManagerName>.py
│   └── <catalog>.json     # Optional static catalogs/prompts (packaged into Managers/)
├── widgets/               # Optional custom HTML/JS Result View widgets
│   ├── <widget_name>.html # HTML/CSS/JS template for the SOAR Case Wall / Overview
│   └── <widget_name>.yaml # Widget definition, scope (alert/case), and sizing
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
    customer_id: "<your-customer-uuid>"
    project_id: "<your-gcp-project-id>"
    region: "us"
    env: prod
current_tenant: default
```

To configure via the `mp` CLI using your environment variables or explicit parameters:
```bash
mp config set \
  --customer-id "${SECOPS_CUSTOMER_ID:-<your-customer-uuid>}" \
  --project-id "${SECOPS_PROJECT_ID:-<your-gcp-project-id>}" \
  --region "${SECOPS_REGION:-us}"
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

### 4. Bundling Static Assets & Runtime Path Resolution in `mp build`
When `mp build integration <name> --custom` packages an integration into a `.zip` archive, it restructures the source directory layout:
- `core/` is flattened and renamed to `Managers/` at the root of the built archive.
- `actions/` is compiled into `ActionsScripts/` and `ActionsDefinitions/`.
- `jobs/` is compiled into `Jobs/` and `JobsDefinitions/`.

To bundle static data files (e.g., `.json` scenario catalogs, `.txt` schema guides, or prompt templates) without external cloud storage or runtime network calls:
1. Place the static files directly inside `core/` alongside your Manager class (e.g., `core/logjammer_catalog.json` or `core/secops_udm_guide.txt`). `mp build` automatically copies all files in `core/` into `Managers/`.
2. Resolve the file path dynamically using `Path(__file__).resolve().parent` with fallback checks so it works identically in both local `pytest` (`core/`) and the deployed SOAR container (`Managers/`):
   ```python
   from pathlib import Path

   def _resolve_asset_path(filename: str) -> Path:
       base_dir = Path(__file__).resolve().parent
       candidates = [
           base_dir / filename,
           base_dir.parent / "core" / filename,
           base_dir.parent / "Managers" / filename,
       ]
       for candidate in candidates:
           if candidate.exists():
               return candidate
       raise FileNotFoundError(f"Bundled asset '{filename}' not found in {candidates}")
   ```

### 5. ASCII Sanitization of Output Messages (`siemplify.end`)
Legacy SOAR runner serialization (`siemplify.end(output_message, result_value, execution_state)`) can raise `UnicodeEncodeError` if an unhandled exception string or API response contains non-ASCII characters (such as `—`, smart quotes, or emoji). Always sanitize exception and status strings before passing them to `siemplify.end`:
```python
import unicodedata

def _safe_ascii(text: str) -> str:
    return unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
```

---

## ⏱️ Scheduled SOAR Jobs (`jobs/*.py` & `jobs/*.yaml`)

Scheduled Jobs run periodically on the SOAR background scheduler (e.g., to inject continuous synthetic telemetry, poll external feeds, or perform recurring health/housekeeping tasks).

### 1. Job YAML Definition (`jobs/<job_name>.yaml`)
Note that `jobs/*.yaml` uses string parameter types (`string`, `boolean`, `int`) rather than numeric enum IDs:
```yaml
creator: Admin
description: Continuously injects realistic synthetic baseline noise into Google SecOps SIEM.
integration: LogJammer
name: LogJammer Continuous Noise Generator
parameters:
  - default_value: "https://us-chronicle.googleapis.com"
    description: "Chronicle Ingestion API endpoint."
    is_mandatory: true
    name: API Root
    type: string
  - default_value: "300"
    description: "Total events to emit per scheduled job run."
    is_mandatory: true
    name: Events Per Run
    type: string
  - default_value: true
    description: "Verify SSL certificates."
    is_mandatory: false
    name: Verify SSL
    type: boolean
```

### 2. Job Python Implementation (`jobs/<job_name>.py`)
- Use `from SiemplifyJob import SiemplifyJob`.
- In Python 3.11 runner containers, always fall back to `siemplify.parameters` dict if `siemplify.extract_job_param()` returns `None`.
- Persist job state across runs using `siemplify.fetch_timestamp()` / `siemplify.save_timestamp()` or `siemplify.get_scoped_job_context_property()` / `siemplify.set_scoped_job_context_property()`.

```python
from SiemplifyJob import SiemplifyJob

SCRIPT_NAME = "LogJammer Continuous Noise Generator"

def _get_param(siemplify: SiemplifyJob, name: str, default=None, is_mandatory: bool = False):
    try:
        val = siemplify.extract_job_param(param_name=name, default_value=default, is_mandatory=is_mandatory)
        if val is not None:
            return val
    except Exception:
        pass
    raw_params = getattr(siemplify, "parameters", {}) or {}
    return raw_params.get(name, default)

def main():
    siemplify = SiemplifyJob()
    siemplify.script_name = SCRIPT_NAME
    try:
        api_root = _get_param(siemplify, "API Root", "https://us-chronicle.googleapis.com", True)
        # Execute scheduled job logic...
        siemplify.LOGGER.info("Successfully completed job iteration.")
    except Exception as e:
        siemplify.LOGGER.error(f"Job failed: {e}")
        raise
    finally:
        siemplify.end_script()

if __name__ == "__main__":
    main()
```

---

## 🎨 Custom HTML Widgets (`widgets/*.html` & `widgets/*.yaml`)

Custom HTML widgets render rich interactive visualizations on the **Case Overview** tab (`scope: case` or `widget_definition_scope: both`) and the **Playbook Step Result View**.

### 1. Widget YAML Schema (`widgets/<widget_name>.yaml`)
```yaml
action_identifier: Correlate Case Entities
condition_group:
  conditions: []
  logical_operator: and
data_definition:
  html_height: 680
  safe_rendering: false
  type: html
  widget_definition_scope: both
default_size: full_width
description: Renders an interactive Case Entity Correlation Summary & UDM Breakdown.
integration: SecOpsSDKEngine
scope: case
title: Case Entity Correlation
type: html
```

### 2. Dynamic Dark/Light Theme Synchronization in SOAR Iframes
SOAR renders custom HTML widgets inside sandboxed `<iframe>` elements. Hardcoding dark-only or light-only backgrounds causes jarring visual contrast when analysts toggle between Dark and Light mode in the Chronicle UI.
- Define all surface, text, border, and badge colors using `--soar-*` CSS custom properties (`:root[data-theme="dark"]` and `:root[data-theme="light"]`).
- Implement a 3-tier theme detection script on load (and via `MutationObserver` on `window.parent.document.documentElement` when accessible):
  1. **Parent DOM / Computed Luminance**: Inspect `window.parent.document.body` (or `window.top.document.body`) computed `backgroundColor` RGB luminance ($L = 0.299R + 0.587G + 0.114B$; if $L > 140$, apply `light`, else `dark`).
  2. **OS / Browser Media Query**: Check `window.matchMedia('(prefers-color-scheme: light)').matches`.
  3. **Manual Toggle Fallback**: Include a subtle theme toggle button in the widget header so the analyst can always override the theme.

---

## 🔄 Playbook Engineering, Scope (`CASE` vs. `ALERT`), & Reaction Triggers

### 1. Chronicle Legacy Playbooks REST API Endpoints
Playbooks and live execution instances can be inspected and modified programmatically via the Chronicle REST API (`https://<region>-chronicle.googleapis.com/v1alpha/projects/<project_id>/locations/<region>/instances/<customer_id>/legacyPlaybooks:...`):
- **List Playbook Cards**: `POST .../legacyPlaybooks:legacyGetWorkflowMenuCardsWithEnvFilter`
- **Fetch Full Playbook Definition**: `POST .../legacyPlaybooks:legacyGetWorkflowFullInfoWithEnvFilterByIdentifier` (`{"identifier": "<WORKFLOW_UUID>"}`)
- **Save Playbook Definition**: `POST .../legacyPlaybooks:legacySaveWorkflowDefinitions` (`{"workflows": [<FULL_WORKFLOW_OBJECT>]}`)
- **List Playbook Runs on a Case**: `POST .../legacyPlaybooks:legacyGetWorkflowInstancesCards` (`{"caseId": <CASE_ID>}`)
- **Fetch Step-by-Step Execution Logs**: `POST .../legacyPlaybooks:legacyGetWorkflowInstance` (`{"id": <INSTANCE_ID>, "caseId": <CASE_ID>, "indicatorIdentifier": "<ALERT_IDENTIFIER>", "shouldFetchSteps": true}`)

### 2. Critical Rules for `legacySaveWorkflowDefinitions`
1. **`creator` Must Be a Valid SOAR User UUID**: Never pass an email address or `"System"` in the `creator` field when saving a playbook via the API — the SOAR backend validates `creator` against the internal user table and will fail or corrupt the card if it is not a valid UUID (query `/legacySoarUsers` first to obtain a valid UUID).
2. **Preserve Folder Placement (`categoryName` & `categoryId`)**: Always include both `"categoryName"` (e.g., `"GSA"`) and `"categoryId"` (e.g., `9`) on the workflow payload so the playbook remains in its designated folder.
3. **Never Save While a Run Is `IN_PROGRESS`**: Saving a playbook via `legacySaveWorkflowDefinitions` mints a **new `identifier` UUID snapshot** while keeping `originalPlaybookIdentifier` constant. Saving while an instance is actively executing (`status: "IN_PROGRESS"`) can orphan pending steps on the old revision UUID.

### 3. `CASE` vs. `ALERT` Scope & In-Place Case Playbook Re-runs (Pattern A)
- **Why Scope Matters**: Widgets placed on the **Case Overview** tab require actions executed inside a **`CASE`-scoped** playbook (`scope: "CASE"`). However, standard `CASE_DATA` triggers only fire **once** when the case is initially created.
- **The Post-Ingestion Replay Challenge**: When an `ALERT`-scoped playbook (such as `LogJammer`) replays synthetic logs into Chronicle after case creation, new detections arrive ~2–3 minutes later. A standard `CASE_DATA` playbook has already finished and will not include those post-replay detections.
- **Solution — Reaction Trigger Pattern A (`CASE_TAG_ADDED` + Tag Cycle)**:
  Use a **`CASE_TAG_ADDED`** reaction trigger so the `CASE`-scoped playbook re-executes **in-place** (`#1` -> `#2`, `runCount: "2"`) and refreshes the Case Overview HTML widgets directly:
  1. **Initial Case Playbook (`Case Ingestion`, `scope: "CASE"`, `trigger.type: "CASE_DATA"`)**:
     Runs initial case setup and executes `Siemplify_Case Tag` (`Tag: "Run_Case_Correlation"`).
  2. **Correlation Case Playbook (`Case Correlate Case Entities`, `scope: "CASE"`, `trigger.type: "CASE_TAG_ADDED"`)**:
     - Configured with trigger value `"Run_Case_Correlation"`, `executionMode: "QUEUED"`, and `maxReactionDepth: 5`.
     - **Important**: Ensure `trigger.conditions` and `trigger.reactionConditions` are empty (`[]`). Do **not** leave stale `CASE_DATA` conditions (like `[Event.alert_type]` or `[trigger.to_state]`) inside a `CASE_TAG_ADDED` trigger, or the reaction trigger will silently evaluate to `false`!
     - Runs `Correlate Case Entities`, `Correlate Silent Detections`, and `GoogleADK_Run ADK Agent`.
     - **Final Step (`Siemplify_Remove Tag`)**: Removes the `"Run_Case_Correlation"` tag from the case so the tag can be re-applied later.
  3. **Alert-Level Replay Playbook (`LogJammer`, `scope: "ALERT"`)**:
     - Replays scenario telemetry into Chronicle (`LogJammer_Execute Attack Scenario`).
     - Waits for Chronicle's streaming YARA-L detection engine (`Tools_Delay Playbook V2`, e.g., 3 minutes).
     - Calls `Siemplify_Case Tag` (`Tag: "Run_Case_Correlation"`), which re-triggers `Case Correlate Case Entities` in-place (`#2`) to capture the newly generated detections and update the Case Overview HTML widgets.

---

## 🔍 Chronicle SIEM ↔ SOAR Entity & Detection Correlation Patterns

### 1. Inferring True Entity Types from SOAR `GENERICENTITY`
Chronicle SOAR Case and Alert cards frequently classify extracted entities (including IP addresses, AWS IAM ARNs, and hostnames) under the catch-all `GENERICENTITY` type (`entity_type == "GENERICENTITY"`). If an integration relies strictly on SOAR's `entity_type` to select a UDM search template, valid entities will be skipped or searched against the wrong UDM fields.
**Always run value-based regex/heuristic inference before falling back to SOAR's raw `entity_type`:**
- **IPv4 / IPv6 regex** -> `ADDRESS` (`ip = "{val}" OR principal.ip = "{val}" OR target.ip = "{val}" OR src.ip = "{val}"`)
- **AWS ARN (`^arn:aws[-a-z0-9]*:`) or Email (`@`)** -> `USER` (`principal.user.userid`, `target.user.userid`, `principal.user.email_addresses`, `target.user.email_addresses`, `principal.user.product_object_id`)
- **MD5 (32 hex) / SHA1 (40 hex) / SHA256 (64 hex)** -> `FILEHASH` (`target.file.sha256`, `target.file.md5`, `principal.process.file.sha256`)
- **FQDN / Hostname pattern** -> `HOSTNAME` (also strip domain suffix to query both `{fqdn}` and `{short_hostname}` across `principal.hostname`, `target.hostname`, and `principal.asset.hostname`)

### 2. Distinguishing YARA-L Detections (`ALERTING` vs. `NOT_ALERTING`) from Raw UDM Events
When querying Chronicle via `udm_search` (`legacySearchCustomerEvents`) or `list_detections`:
- **Alerting YARA-L Detections (`alertState: "ALERTING"`)**: Custom or curated YARA-L rules configured to generate alerts in Chronicle Cases.
- **Silent YARA-L Detections (`alertState: "NOT_ALERTING"`)**: YARA-L rules that matched UDM events in the background without generating a standalone SOAR alert. Note that in `legacySearchCustomerEvents`, detection metadata can appear in either per-event `ev["detections"]` or the top-level stream `detections` array (where `ruleId` begins with `ru_` or `ur_`).
- **Parser `securityResult` Annotations vs. YARA-L Detections**: Windows EventLog / Sysmon parsers populate `udm.securityResult` with EventID descriptions (e.g., `"A user was added to a security-enabled global group"`). These are **parser annotations, not YARA-L rule detections** — filter by `ruleId` prefix (`ru_` / `ur_`) or explicit `alertState` when correlating silent YARA-L rules.
- **Unalerted Precursor UDM Events (`detections: None`)**: Critical attacker actions (such as a `certutil.exe -decode` webshell drop or `whoami /all` reconnaissance) may not trigger *any* YARA-L rule (neither `ALERTING` nor `NOT_ALERTING`). Always pair `correlate_silent_detections` with a chronological `search_udm_events` pivot on the host/user around the alert timestamp so the AI analyst or playbook uncovers unalerted precursor activity.

### 3. Dynamic Lookahead Window for Replayed Detections
When correlating detections around a case's reference timestamp (`ref_time`), always extend the upper bound of the search window to `max(ref_time + 2h, datetime.now(timezone.utc) + 15m)`. Because replayed logs (e.g., from `LogJammer`) are ingested at current wall-clock time *after* the initial alert timestamp, capping `end_time` strictly at `ref_time + 2h` can miss newly replayed detections if the original alert had an older timestamp.

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
