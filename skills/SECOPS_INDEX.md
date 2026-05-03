# Google SecOps Capabilities Index

This project provides a local CLI (`secops.py`) to interact with Google SecOps (Chronicle) via the MCP API.

### 🤖 CRITICAL INSTRUCTIONS FOR AI AGENTS

1. **Path Resolution:** Replace `<PATH_TO_SECOPS_SKILLS>` with the absolute path to this repository root (e.g., use `pwd` to discover it) before executing any commands or reading the files below.
2. **Python Environment:** This project requires external dependencies. **Do not use the global `python3` command.** You MUST use the virtual environment's Python binary: `<PATH_TO_SECOPS_SKILLS>/venv/bin/python`.
3. **First-Time Setup:** If the `venv` directory does not exist, you must create it and install dependencies first:
   ```bash
   cd <PATH_TO_SECOPS_SKILLS>
   python3 -m venv venv
   venv/bin/python -m pip install -r requirements.txt
   ```

### 🧭 Routing

When requested to perform a SecOps task, use the `read` tool to look at the corresponding persona file below to learn the correct commands and schema.

- **Case Management & Triage:** For reading, updating, and managing cases and their raw alerts.
  👉 Read: `<PATH_TO_SECOPS_SKILLS>/skills/triage_analyst.md`
- **Detection Engineering:** (Creating and managing Reference Lists, Rules, and Data Tables)
  👉 Read: `<PATH_TO_SECOPS_SKILLS>/skills/detection_engineer.md`
- **Threat Hunting & Investigations:** (Summarizing entities, running raw UDM searches)
  👉 Read: `<PATH_TO_SECOPS_SKILLS>/skills/threat_investigator.md`
- **Ingestion Architecture:** (Importing raw logs, testing parsers)
  👉 Read: `<PATH_TO_SECOPS_SKILLS>/skills/ingestion_architect.md`
- **SecOps Case Analyst:** For reviewing automated SOAR playbook execution history and triggering enrichment actions.
  👉 Read: `<PATH_TO_SECOPS_SKILLS>/skills/secops_case_analyst.md`