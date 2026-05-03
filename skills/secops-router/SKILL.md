---
name: secops-router
description: The primary router to discover Google SecOps capabilities.
---
# Google SecOps Capabilities Index

This provides a local CLI to interact with Google SecOps (Chronicle) via the MCP API.

### 🧭 Routing

When requested to perform a SecOps task, use the `skill` tool to load the corresponding persona file below to learn the correct commands and schema.

- **Cases, Alerts & SOAR Enrichment:** For all case management, alert triage, playbook review, and enrichment action execution.
  👉 `skill({ name: "secops-cases" })`
- **Detection Engineering:** For creating and managing YARA-L Rules, Reference Lists, and Data Tables.
  👉 `skill({ name: "secops-detection-eng" })`
- **Threat Hunting & Investigations:** For summarizing entities and running raw UDM searches.
  👉 `skill({ name: "secops-threat-inv" })`
- **Ingestion Architecture:** For importing raw logs and testing parsers.
  👉 `skill({ name: "secops-ingestion" })`