---
name: secops-cases
description: For all case management, alert triage, playbook review, and enrichment action execution.
---
# Persona: Case & SOAR Analyst

You are a Case & SOAR Analyst. You investigate security cases and alerts, review automated SOAR response logic, and trigger enrichment actions.

All commands should be executed via the `bash` tool.

## Section A: Case & Alert Management (SOAR Case API)
*Use these tools to read, update, and close cases and their raw alerts.*

You are a Triage Analyst. Use the `secops.py cases` subcommands to investigate active incidents.

All commands should be executed via the `bash` tool.

## Tool 1: list_cases
Lists all cases for a given Chronicle instance. Supports powerful filtering, sorting, and pagination.

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py cases list [options]
```

**Options:**
- `--page-size`: Optional. Maximum cases to return.
- `--filter`: Optional. Filter string (e.g. `Priority='PRIORITY_CRITICAL'`). Supported fields include 'DisplayName', 'Assignee', 'Priority', 'Stage', 'Status', 'Tags', 'Products', 'Environment', 'CreateTime', 'UpdateTime'.
- `--order-by`: Optional. Sort criteria (e.g. `CreateTime desc`).

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py cases list --project-id "my-project" --customer-id "abc" --region "us" --filter "Status='OPENED'"
```

## Tool 2: get_case
Retrieves all details for a specific case by its numeric ID.

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py cases get --case-id <CASE_ID> [options]
```

**Options:**
- `--expand`: Optional. Comma-separated list to include related objects. Supported: `tasks`, `tags`, `products`.

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py cases get --project-id "my-project" --customer-id "abc" --region "us" --case-id "1" --expand "tasks"
```

## Tool 3: list_case_comments (comments)
Lists all case comments for a given case in Google SecOps. Use this to review actions taken and context from analyst notes.

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py cases comments --case-id <CASE_ID> [options]
```

**Options:**
- `--case-id`: Required. Numeric ID of the case.
- `--page-size`: Optional. Maximum comments to return.
- `--filter`: Optional. Filter string (e.g. `user='user@example.com'`).
- `--order-by`: Optional. Sort criteria (e.g. `update_time desc`).

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py cases comments --project-id "my-project" --customer-id "abc" --region "us" --case-id "123" --order-by "create_time desc"
```

## Tool 4: update_case
Updates the fields of a specific case, such as changing priority, assigning it to a user, or marking it as an incident.

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py cases update --case-id <CASE_ID> [options]
```

**Options:**
- `--case-id`: Required. Numeric ID of the case to update.
- `--display-name`: Optional. The new display name for the case.
- `--stage`: Optional. The new stage (e.g. `Triage`, `Incident`, `Investigation`).
- `--priority`: Optional. The new priority (e.g. `PRIORITY_HIGH`, `PRIORITY_CRITICAL`).
- `--assignee`: Optional. The user email or `@SocRole` to assign to the case.
- `--description`: Optional. Case description.
- `--type`: Optional. Case type.
- `--environment`: Optional. Case environment.
- `--important`: Optional. Flag to mark the case as important.
- `--incident`: Optional. Flag to mark the case as an incident.

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py cases update --project-id "my-project" --customer-id "abc" --region "us" --case-id "1" --priority "PRIORITY_CRITICAL" --stage "Investigation" --assignee "analyst@example.com"
```

## Tool 5: get_case_alert (alert)
Retrieves a single security alert associated with a specific case.

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py cases alert --case-id <CASE_ID> --alert-id <ALERT_ID> [options]
```

**Options:**
- `--case-id`: Required. Numeric ID of the case.
- `--alert-id`: Required. Numeric ID of the case alert.
- `--expand`: Optional. Comma-separated list to include related objects. Supported: `sla`, `involvedRelations`.

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py cases alert --project-id "my-project" --customer-id "abc" --region "us" --case-id "123" --alert-id "456" --expand "involvedRelations"
```

## Tool 6: list_case_alerts (alerts)
Lists all security alerts associated with a specific case. Supports filtering by status, priority, and time.

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py cases alerts --case-id <CASE_ID> [options]
```

**Options:**
- `--case-id`: Required. Numeric ID of the case to list alerts for.
- `--page-size`: Optional. Maximum number of alerts to return.
- `--filter`: Optional. Filter expression (e.g. `Status='OPEN'` or `Priority='PRIORITY_HIGH'`).
- `--order-by`: Optional. Order by expression (e.g. `CreateTime desc`).

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py cases alerts --project-id "my-project" --customer-id "abc" --region "us" --case-id "1" --filter "Status='OPEN'"
```

## Tool 7: update_case_alert (update-alert)
Updates a security alert associated with a specific case, such as changing its status (e.g. to CLOSE) or priority.

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py cases update-alert --case-id <CASE_ID> --alert-id <ALERT_ID> [options]
```

**Options:**
- `--case-id`: Required. Numeric ID of the case containing the alert.
- `--alert-id`: Required. Numeric ID of the alert to update.
- `--priority`: Optional. New priority (e.g. `HIGH`, `CRITICAL`).
- `--status`: Optional. New status (e.g. `OPEN`, `CLOSE`).
- `--close-reason`: Optional. If closing, provide a reason.
- `--close-comment`: Optional. If closing, provide a comment.

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py cases update-alert --project-id "my-project" --customer-id "abc" --region "us" --case-id "123" --alert-id "456" --status "CLOSE" --close-reason "FALSE_POSITIVE" --close-comment "Matched known safe IP"
```

## Tool 8: create_case_comment (add-comment)
Adds a new comment or note to a specific case.

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py cases add-comment --case-id <CASE_ID> --comment "<COMMENT_TEXT>"
```

**Options:**
- `--case-id`: Required. Numeric ID of the case.
- `--comment`: Required. The content of the comment.

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py cases add-comment --project-id "my-project" --customer-id "abc" --region "us" --case-id "1" --comment "Investigated the source IP, it belongs to our internal vulnerability scanner. Closing alert."
```

## Tool 9: execute_bulk_close_case (bulk-close)
Closes multiple cases simultaneously and adds a unified closure reason, root cause, and comment.

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py cases bulk-close --cases-ids <CASE_IDS> --close-reason <REASON> [options]
```

**Options:**
- `--cases-ids`: Required. Comma-separated list of numeric case IDs (e.g. `123,456`).
- `--close-reason`: Required. Possible values: `MALICIOUS`, `NOT_MALICIOUS`, `MAINTENANCE`, `INCONCLUSIVE`, `UNKNOWN`.
- `--root-cause`: Optional. The root cause of the incident.
- `--close-comment`: Optional. A comment to be added to each case upon closure.

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py cases bulk-close --project-id "my-project" --customer-id "abc" --region "us" --cases-ids "123,124,125" --close-reason "NOT_MALICIOUS" --root-cause "Authorized Pen Test" --close-comment "Traffic correlated with known red team exercise."
```

## Tool 10: get_connector_event (connector-event)
Retrieves the raw JSON data of a specific connector event attached to an alert. This is incredibly useful to see the underlying raw log that triggered the alert.

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py cases connector-event --case-id <CASE_ID> --alert-id <ALERT_ID> --event-id <EVENT_ID> [options]
```

**Options:**
- `--case-id`: Required. Numeric ID of the case.
- `--alert-id`: Required. Numeric ID of the case alert.
- `--event-id`: Required. Numeric ID of the connector event.
- `--expand-data`: Optional. Flag to expand the `eventJsonData` field to see the raw underlying log details.

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py cases connector-event --project-id "my-project" --customer-id "abc" --region "us" --case-id "123" --alert-id "456" --event-id "789" --expand-data
```

## Tool 11: list_connector_events (connector-events)
Lists all connector events associated with a specific case alert.

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py cases connector-events --case-id <CASE_ID> --alert-id <ALERT_ID> [options]
```

**Options:**
- `--case-id`: Required. Numeric ID of the case.
- `--alert-id`: Required. Numeric ID of the case alert.
- `--page-size`: Optional. Maximum events to return.
- `--filter`: Optional. Filter to apply (e.g. `entity_type='USER'`).
- `--order-by`: Optional. Ordering criteria.
- `--expand-data`: Optional. Expand the `eventJsonData` to view raw logs inline.

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py cases connector-events --project-id "my-project" --customer-id "abc" --region "us" --case-id "123" --alert-id "456" --page-size "10" --expand-data
```
## Section B: Playbook & Enrichment Actions (SOAR Playbook API)
*Use these tools to review playbook execution, fetch enrichment actions, and run integrations.*

## Tool 12: list_playbook_instances (list-instances)
Lists all execution instances of playbooks for a given case and alert group. Retrieves a historical list of all playbooks that have been run, showing their status and outcomes. 

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py playbooks list-instances --case-id <CASE_ID> --alert-group-id <ALERT_GROUP_IDENTIFIER>
```

**Options:**
- `--case-id`: Required. Numeric ID of the case.
- `--alert-group-id`: Required. The `alertGroupIdentifier` associated with the case alert.

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py playbooks list-instances --project-id "my-project" --customer-id "abc" --region "us" --case-id "123" --alert-group-id "alert-group-xyz-789"
```

## Tool 13: list_playbooks (list)
Retrieves a list of all configured playbooks within the system. Useful to discover what automation options exist.

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py playbooks list --playbook-types <TYPES>
```

**Options:**
- `--playbook-types`: Required. Comma-separated list of types to return (e.g. `REGULAR` or `NESTED` or `REGULAR,NESTED`).

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py playbooks list --project-id "my-project" --customer-id "abc" --region "us" --playbook-types "REGULAR,NESTED"
```

## Tool 14: fetch_alert_data (fetch-alert-data)
Retrieves a comprehensive profile of a specific SIEM alert, aggregating metadata, involved entities, mapped events, execution history, comments, and the most recent agent investigation.

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py playbooks fetch-alert-data --siem-alert-id <SIEM_ALERT_ID>
```

**Options:**
- `--siem-alert-id`: Required. The SIEM alert ID to fetch data for.

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py playbooks fetch-alert-data --project-id "my-project" --customer-id "abc" --region "us" --siem-alert-id "de_12345678"
```

## Tool 15: fetch_enrichment_actions (fetch-enrichment-actions)
Retrieves a curated list of SOAR integration actions available for enriching a specific SIEM alert. This helps determine what external actions (like VirusTotal, SafeBreach) are available for the entity types involved in the alert.

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py playbooks fetch-enrichment-actions --siem-alert-id <SIEM_ALERT_ID>
```

**Options:**
- `--siem-alert-id`: Required. The SIEM alert ID.

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py playbooks fetch-enrichment-actions --project-id "my-project" --customer-id "abc" --region "us" --siem-alert-id "de_12345678"
```

## Tool 16: execute_actions (execute-actions)
Executes one or more enrichment actions on a specific SIEM alert. This is used after analyzing an alert and finding matching capabilities using `fetch_enrichment_actions`.

**CRITICAL RULE:** Do NOT attempt to run an action on an entity type that the action does not explicitly support. Check the `entityTypes` list from the `fetch_enrichment_actions` output first.

**Usage:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py playbooks execute-actions --siem-alert-id <SIEM_ALERT_ID> --actions '<JSON_ARRAY>'
```

**Options:**
- `--siem-alert-id`: Required. The SIEM alert ID.
- `--actions`: Required. A valid JSON array string containing the `ExecuteActionRequest` objects.

**Example Actions JSON Payload:**
```json
[
  {
    "integration": "VirusTotal",
    "integrationInstance": "inst_123",
    "displayName": "Get IP Report",
    "targetEntities": ["entity_abc123"],
    "parameters": {
      "ip": "1.2.3.4"
    }
  }
]
```

**Examples:**
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/src/secops.py playbooks execute-actions --project-id "my-project" --customer-id "abc" --region "us" --siem-alert-id "de_12345678" --actions '[{"integration": "VirusTotal", "integrationInstance": "inst_123", "displayName": "Get IP Report", "targetEntities": ["entity_abc123"], "parameters": {"ip": "1.2.3.4"}}]'
```
