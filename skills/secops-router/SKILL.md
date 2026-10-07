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
- **Natural Language to GoogleSQL & Chronicle Dashboards:** For authoring and validating GoogleSQL and GoogleSQL Pipe Syntax queries for UDM events, context graph, and ingestion telemetry.
  👉 `skill({ name: "secops-nl2sql" })`
- **Log Volume & Ingestion Tuning:** For two-stage ingestion volume analysis, `metadata.event_type` routed dimensional drill-downs, and quantifying GB savings for EDR/collector exclusions vs. single-host outliers.
  👉 `skill({ name: "secops-log-tuning" })`
- **OTTL & Bindplane Collector Pipelines:** For authoring and validating OpenTelemetry Transformation Language (OTTL) filter conditions and transform statements, and inspecting or managing Bindplane processors and configurations via the Bindplane REST API.
  👉 `skill({ name: "secops-ottl" })`