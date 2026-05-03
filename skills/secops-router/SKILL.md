---
name: secops-router
description: The primary router to discover Google SecOps capabilities.
---
# Google SecOps Capabilities Index

This provides a local CLI to interact with Google SecOps (Chronicle) via the MCP API.

### 🧭 Routing

When requested to perform a SecOps task, use the `skill` tool to load the corresponding persona file below to learn the correct commands and schema.

- **Case Management & Triage:** For reading, updating, and managing cases and their raw alerts.
  👉 `skill({ name: "secops-triage-analyst" })`
- **Detection Engineering:** For creating and managing YARA-L Rules, Reference Lists, and Data Tables.
  👉 `skill({ name: "secops-detection-eng" })`
- **Threat Hunting & Investigations:** For summarizing entities and running raw UDM searches.
  👉 `skill({ name: "secops-threat-inv" })`
- **Ingestion Architecture:** For importing raw logs and testing parsers.
  👉 `skill({ name: "secops-ingestion" })`
- **SecOps Case Analyst:** For reviewing automated SOAR playbook execution history and triggering enrichment actions.
  👉 `skill({ name: "secops-case-analyst" })`