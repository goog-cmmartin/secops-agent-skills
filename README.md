# Google SecOps Agent Skills

A modular skill pack for AI Agents (such as Google Antigravity and OpenCode) interacting with Google SecOps (Chronicle) and Bindplane collector pipelines.

> **Note on SecOps MCP:** Core Chronicle capabilities like case management, alert triage, YARA-L rule management, entity lookup, and basic UDM searches are handled natively by the [Google Cloud SecOps MCP server](https://github.com/google-cloud-secops). This repository provides specialized, domain-expert skills, workflow automation, and validation tooling that extend the agent beyond basic MCP wrapper calls.

## Skills Included

- **`case-grouping`**: Automated entity-driven workflow for grouping and consolidating security cases in Chronicle SOAR. Correlates cross-case indicator overlap (IPs, user identities, hostnames, domains, hashes) and executes or previews case merging.
- **`secops-log-tuning`**: Two-stage data-driven log volume and ingestion tuning analyzer. Joins `ingestion` metrics with `events`, routes by `metadata.event_type` to actor-grouped dimensional drill-downs, and quantifies byte/GB savings for fleet-wide policy exclusions vs. single-host outliers.
- **`secops-nl2sql`**: Converts natural language, YARA-L 2.0 queries, Sysmon/EDR XML configs, or BigQuery SQL into valid, optimized GoogleSQL and GoogleSQL Pipe Syntax (`|>`) queries for Chronicle Native Dashboards, UDM Search, and Data Lake analytics. Includes local protobuf schema references and self-validation against the Chronicle Dashboard Engine.
- **`secops-ottl`**: Authors, validates, and manages OpenTelemetry Transformation Language (OTTL) transform statements and filter conditions for Google SecOps and Bindplane collector pipelines. Includes offline OTTL syntax/state-transition validation and a live Bindplane CLI for auditing pipeline order and deploying processors.
- **`secops-soar-dev`**: End-to-end development, testing, packaging, and deployment workflow for Google SecOps (Chronicle) SOAR custom integrations using the Content Hub specification, `mp` CLI utility, Workload Identity Federation, and native Vertex AI / Gemini tool grounding.


## Installation

Run the installation script for your agent harness. This sets up the Python virtual environment, installs dependencies, and registers the skills into the agent's skills directory.

```bash
cd secops-agent-skills

# For Google Antigravity (~/.gemini/config/skills)
./install_antigravity.sh

# For OpenCode (~/.config/opencode/skills)
./install.sh
```

*(Note: `install_jetski.sh` is maintained as a backward-compatible wrapper that forwards to `install_antigravity.sh`.)*

### Post-Installation Setup

1. Ensure you have active Google Application Default Credentials: 
   ```bash
   gcloud auth application-default login
   ```
2. Edit the `.env` file generated in the repository root with your specific Google SecOps and optional Bindplane details:
   ```ini
   # Google SecOps
   SECOPS_PROJECT_ID=your-gcp-project-id
   SECOPS_CUSTOMER_ID=your-chronicle-customer-uuid
   SECOPS_REGION=us

   # Bindplane (Optional, for secops-ottl)
   BINDPLANE_PROJECT_ID=your-bindplane-project-id
   BINDPLANE_API_KEY=your-bindplane-api-key
   BINDPLANE_API_URL=https://app.bindplane.com/v1
   ```

## Agent Usage

Once installed, your agent will automatically discover these skills:
- **Case Grouping**: *"Scan our last 10 open cases in Chronicle SOAR and check if any share overlapping entities or should be merged."*
- **Log Tuning**: *"Analyze our top noisy log types in Chronicle over the last 7 days and recommend exclusions."*
- **GoogleSQL / PipedSQL**: *"Write a GoogleSQL Pipe query to aggregate process creation events by parent binary and count distinct users."*
- **OTTL & Bindplane**: *"Audit our ZEEK Bindplane pipeline and generate a tuple-pinned OTTL filter for noisy internal DNS queries."*
- **SOAR Custom Integrations**: *"Use the secops-soar-dev skill to build, test, and deploy our GoogleADK integration with the mp CLI."*