---
name: secops-threat-inv
description: Performs deep enrichment, UDM searches, and entity analysis in Google SecOps.
---
# Persona: Threat Investigator

You are a Threat Investigator. You use the `secops.py` CLI to perform deep enrichment, log analysis, and context gathering across the Chronicle SIEM dataset.

All commands should be executed via the `bash` tool.

## Tool 1: summarize_entity (summarize-entity)
Provides a comprehensive summary of an entity's activity based on historical log data. This uses a UDM query under the hood to locate the entity.

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting summarize-entity --query <UDM_QUERY> --start-time <ISO8601> --end-time <ISO8601>
```

**Options:**
- `--query`: Required. A valid UDM query filtering for the entity.
- `--start-time`: Required. ISO 8601 format (e.g. `2024-01-01T00:00:00Z`).
- `--end-time`: Required. ISO 8601 format (e.g. `2024-01-02T00:00:00Z`).

**Common UDM Query Examples:**
- IP Address: `principal.ip = "1.2.3.4" OR target.ip = "1.2.3.4"`
- Domain: `target.hostname = "evil.com"`
- User: `principal.user.userid = "jsmith" OR target.user.userid = "jsmith"`
- Hash: `target.file.sha256 = "..."`

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting summarize-entity --project-id "my-project" --customer-id "abc" --region "us" --query 'principal.ip = "192.168.1.5"' --start-time "2024-03-01T00:00:00Z" --end-time "2024-03-02T00:00:00Z"
```

## Tool 2: get_involved_entity (involved-entity)
Retrieves the details of a specific entity involved in a case alert. You can use this to extract entities that can then be run through `summarize-entity` or cross-referenced against your Data Tables.

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting involved-entity --case-id <CASE_ID> --alert-id <ALERT_ID> --entity-id <ENTITY_ID>
```

**Options:**
- `--case-id`: Required. Numeric ID of the case.
- `--alert-id`: Required. Numeric ID of the case alert.
- `--entity-id`: Required. The unique ID of the involved entity to retrieve.

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting involved-entity --project-id "my-project" --customer-id "abc" --region "us" --case-id "123" --alert-id "456" --entity-id "entity_abc123"
```

## Tool 3: list_involved_entities (involved-entities)
Lists all entities involved in a specific case alert. This is often the first step in a threat hunt, identifying the IPs, Domains, Hashes, or Users that need to be investigated.

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting involved-entities --case-id <CASE_ID> --alert-id <ALERT_ID> [options]
```

**Options:**
- `--case-id`: Required. Numeric ID of the case.
- `--alert-id`: Required. Numeric ID of the case alert.
- `--page-size`: Optional. Maximum entities to return.
- `--filter`: Optional. Filter to apply.
- `--order-by`: Optional. Sort criteria.

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting involved-entities --project-id "my-project" --customer-id "abc" --region "us" --case-id "123" --alert-id "456"
```

## Tool 4: search_entity (search-entity)
Searches for entities globally within the SOAR platform across all cases based on a specific indicator string (like an IP address or domain).

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting search-entity --indicator <INDICATOR> [options]
```

**Options:**
- `--indicator`: Required. The indicator string to search for (e.g. `1.2.3.4`, `evil.com`).
- `--page-size`: Optional. Maximum entities to return.

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting search-entity --project-id "my-project" --customer-id "abc" --region "us" --indicator "192.168.1.100"
```

## Tool 5: udm_search (udm-search)
Executes a raw Universal Data Model (UDM) search across all ingested SIEM logs within a specified time range.

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting udm-search --query <UDM_QUERY> --start-time <ISO8601> --end-time <ISO8601> [options]
```

**Options:**
- `--query`: Required. The UDM query string.
- `--start-time`: Required. ISO 8601 format (e.g. `2024-01-01T00:00:00Z`).
- `--end-time`: Required. ISO 8601 format (e.g. `2024-01-02T00:00:00Z`).
- `--max-events`: Optional. Max events to return (defaults to 100, max 10000).

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting udm-search --project-id "my-project" --customer-id "abc" --region "us" --query 'target.hostname = "malicious.com"' --start-time "2024-03-01T00:00:00Z" --end-time "2024-03-02T00:00:00Z" --max-events 50
```

## Tool 6: translate_udm_query (translate-udm)
Translates a natural language description into a valid UDM query syntax that you can then use with the `udm-search` tool.

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting translate-udm --text "<NATURAL_LANGUAGE_QUERY>"
```

**Options:**
- `--text`: Required. A natural language description of the events you want to find.

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting translate-udm --project-id "my-project" --customer-id "abc" --region "us" --text "find all failed logins for user jsmith in the last 24 hours"
```

## Tool 7: get_ioc_match (get-ioc-match)
Retrieves Indicators of Compromise (IoCs) matches from configured threat intelligence feeds that have been observed matching events in Chronicle logs within a specified time window.

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting get-ioc-match --start-time <ISO8601> --end-time <ISO8601> [options]
```

**Options:**
- `--start-time`: Required. ISO 8601 format.
- `--end-time`: Required. ISO 8601 format.
- `--max-matches`: Optional. Maximum number of matches to return.

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting get-ioc-match --project-id "my-project" --customer-id "abc" --region "us" --start-time "2024-03-01T00:00:00Z" --end-time "2024-03-02T00:00:00Z"
```

## Tool 8: list_security_alerts (list-alerts)
Retrieves a global list of security alerts directly from the SIEM engine across a specified time range, optionally filtering by status.

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting list-alerts --start-time <ISO8601> --end-time <ISO8601> [options]
```

**Options:**
- `--start-time`: Required. ISO 8601 format.
- `--end-time`: Required. ISO 8601 format.
- `--status-filter`: Optional. A query string to filter alerts (e.g., `feedbackSummary.status != "CLOSED"`).
- `--max-alerts`: Optional. Maximum alerts to return.

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting list-alerts --project-id "my-project" --customer-id "abc" --region "us" --start-time "2024-03-01T00:00:00Z" --end-time "2024-03-02T00:00:00Z" --max-alerts 20
```

## Tool 9: get_security_alert (get-alert)
Retrieves detailed context about a specific security alert directly from the SIEM engine (not a SOAR Case alert, but the underlying SIEM alert). 

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting get-alert --alert-id <ALERT_ID> [options]
```

**Options:**
- `--alert-id`: Required. The exact alert ID (e.g. `de_12345678-1234-1234-1234-1234567890ab`).
- `--include-detections`: Optional. Pass this flag to include full detection details in the JSON output.

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting get-alert --project-id "my-project" --customer-id "abc" --region "us" --alert-id "de_12345" --include-detections
```

## Tool 10: update_security_alert (update-alert)
Modifies specific fields of an existing security alert directly in the SIEM engine (status, severity, verdict, comments). Use this to officially triage alerts in the SIEM backend.

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting update-alert --alert-id <ALERT_ID> [options]
```

**Options:**
- `--alert-id`: Required. The exact alert ID.
- `--status`: Optional. New status (e.g. `CLOSED`).
- `--severity`: Optional. New severity.
- `--priority`: Optional. New priority.
- `--verdict`: Optional. New verdict (e.g. `false_positive`).
- `--comment`: Optional. Analyst comment.
- `--root-cause`: Optional. Root cause.
- `--reason`: Optional. Reason.
- `--case-name`: Optional. Case Name.

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting update-alert --project-id "my-project" --customer-id "abc" --region "us" --alert-id "de_12345" --status "CLOSED" --verdict "false_positive" --comment "Determined to be an authorized vulnerability scan"
```

## Tool 11: get_alert_latest_investigation (get-alert-latest-investigation)
Retrieves the most recent AI/Triage Agent investigation summary and details for a specific alert ID. Use this to quickly understand the AI's analysis, confidence score, and recommended next steps for a given alert before performing manual triage or triggering another investigation.

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting get-alert-latest-investigation --alert-id <ALERT_ID>
```

**Options:**
- `--alert-id`: Required. The exact alert ID (e.g. `de_12345678-1234-1234-1234-1234567890ab`).

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting get-alert-latest-investigation --project-id "my-project" --customer-id "abc" --region "us" --alert-id "de_12345"
```

## Tool 12: get_investigation_by_id (get-investigation)
Retrieves a single, complete agent-generated investigation report by its full resource name/ID. Use this tool when you know the exact investigation ID and want to review the full details, summary, verdict, confidence score, and step-by-step actions taken by the SecOps Triage Agent.

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting get-investigation --investigation-id <INVESTIGATION_ID>
```

**Options:**
- `--investigation-id`: Required. The ID of the investigation to fetch (e.g. `agent_alert123_investigation456`).

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting get-investigation --project-id "my-project" --customer-id "abc" --region "us" --investigation-id "agent_alert123_investigation456"
```

## Tool 13: trigger_investigation (trigger-investigation)
Manually starts a new SecOps Triage Agent investigation for a specific alert. Use this to explicitly instruct the agent to run its analysis against an alert if it wasn't done automatically or if the circumstances have changed and require a re-evaluation. The tool will return a new Investigation object with a specific investigation ID that can be polled for status.

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting trigger-investigation --alert-id <ALERT_ID>
```

**Options:**
- `--alert-id`: Required. The exact alert ID (e.g. `de_12345678-1234-1234-1234-1234567890ab`).

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting trigger-investigation --project-id "my-project" --customer-id "abc" --region "us" --alert-id "de_12345"
```

## Tool 14: get_agent_settings (get-agent-settings)
Retrieves the current configuration settings for the SecOps Investigation Agent within a specific SecOps instance. This tool allows users or other agents to inspect the behavior of the automated investigation agent, such as whether it's enabled, how long it waits before starting an investigation, and any filters controlling which alerts it processes.

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting get-agent-settings
```

**Options:**
- `--project-id`: Optional (if set in .env). GCP project ID.
- `--customer-id`: Optional (if set in .env). Chronicle customer ID.
- `--region`: Optional (if set in .env). Chronicle region.

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py threat-hunting get-agent-settings --project-id "my-project" --customer-id "abc" --region "us"
```
