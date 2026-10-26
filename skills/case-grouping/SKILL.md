---
name: case-grouping
description: >-
  Inspect Chronicle SecOps cases, extract involved entities across alerts,
  calculate cross-case indicator overlap, and recommend or execute case merging.
---

# SOAR Alert-to-Case Grouping & Merging Skill

This skill provides an automated, entity-driven workflow for grouping and consolidating security cases in Google Security Operations (Chronicle SOAR). When multiple alerts or cases share high-fidelity indicators (such as IP addresses, compromised user identities, hostnames, domains, or file hashes), this skill correlates the cases and merges them into a primary investigation container.

---

## When to Activate This Skill

Activate this skill when:
- The user requests to group, correlate, or merge duplicate or related SOAR cases.
- The user asks whether any open cases share overlapping entities, assets, or IOCs.
- The user wants to scan recent cases for common indicators (e.g. `/group-cases [count]`).
- Triage reveals that an incoming alert belongs to an ongoing incident already tracked in another case.

---

## Workflow Steps

### Step 1: Scan Active Cases
Query the latest open cases using the Chronicle MCP server or REST API:
```python
cases = await list_cases(page_size=count, filter_expr='status = "OPENED"')
```

### Step 2: Retrieve Alerts for Each Case
For each candidate case ID, list the associated alerts:
```python
alerts = await list_case_alerts(case_id=case_id)
```

### Step 3: Extract & Normalize Involved Entities
For each alert, extract the associated entities:
```python
entities = await list_involved_entities(case_id=case_id, case_alert_id=alert_id)
```
Focus on high-fidelity entity types:
- `ADDRESS`: IP addresses (e.g., `149.40.62.32`)
- `USERUNIQNAME`: User accounts, emails, and IAM ARNs (e.g., `CASTOR.TROY@WIZUNIVERSITY.COM`)
- `HOSTNAME`: Workstations, servers, instance IDs (e.g., `DESKTOP-TROY-WIZ`)
- `DESTINATIONURL` / `DOMAIN`: C2 endpoints, phishing URLs
- `FILEHASH`: MD5, SHA256 hashes

Filter out generic metadata values (`OUTCOME`, `UNKNOWN`, `TRUE`, `FALSE`).

### Step 4: Compute Entity Overlap & Graph Clustering
1. Index entities by `(type, normalized_value) -> set(case_ids)`.
2. For each pair of cases sharing one or more entities, calculate the overlap score.
3. Form connected components to find multi-case clusters.
4. Also verify intra-case multi-alert correlation (cases that already have multiple correlated alerts).

### Step 5: Merge Cases (Dry-Run or Execution)
To merge the cases into a primary target case:
- Call the `execute_manual_action` or `update_case` MCP tools or underlying Chronicle REST API:
  `POST /v1beta/projects/{project}/locations/{region}/instances/{instance}/cases:merge`
  Payload:
  ```json
  {
    "casesIds": [108080, 108079],
    "caseToMergeWith": 108080
  }
  ```

---

## CLI & Standalone Usage

Run the built-in case grouping script:
```bash
# Preview overlaps (dry run)
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/skills/case-grouping/scripts/group_cases.py --count 10

# Execute merge on overlapping clusters
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/skills/case-grouping/scripts/group_cases.py --count 10 --merge
```

In chat:
```text
"Scan our last 10 open cases in Chronicle SOAR and check if any share overlapping entities or should be merged."
```
