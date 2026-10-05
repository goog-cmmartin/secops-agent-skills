# SecOps Protocol Buffers Reference

The local protos stored in `resources/protos/` are the authoritative source definitions for Google SecOps / Backstory telemetry models.

---

## Key Proto Files

| Proto File | Core Messages | Description |
| :--- | :--- | :--- |
| **`udm.proto`** | `Event`, `Noun`, `Process`, `File`, `Network`, `User`, `SecurityResult` | Defines the Universal Data Model schema backing the `events` and `graph` tables. |
| **`ingestion.proto`** | `IngestionMetric`, `DataValidationResult` | Defines ingestion pipeline metrics backing the `ingestion` table. |
| **`chronicle_api.proto`** | `SearchRequest`, `SearchResponse`, `Rule` | Definitions for Chronicle backend search and rules execution. |
| **`rule.proto` / `ruleset.proto`** | `Rule`, `RuleExecutionError` | YARA-L 2.0 rule definitions and rule compilation metadata. |
| **`case.proto` / `playbook.proto`** | `Case`, `Alert`, `Playbook` | SOAR entity models and alert management. |

---

## Using the Proto Inspector Script

When writing SQL and uncertain if a UDM field is singular (`string`) or repeated (`repeated string[]`):

```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/skills/secops-nl2sql/scripts/lookup_udm_field.py "<field_or_message_name>"
```

### Examples:

1. **Check if a field is an array or string:**
   ```bash
   <PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/skills/secops-nl2sql/scripts/lookup_udm_field.py "email_addresses"
   ```
   *Output:*
   ```text
   [udm.proto:2184] in Message: User
     > repeated string email_addresses = 4;
   ```
   *Action:* Since it is `repeated string`, use `UNNEST(principal.user.email_addresses)` or `principal.user.email_addresses[SAFE_OFFSET(0)]` in SQL.

2. **Check Process fields:**
   ```bash
   <PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/skills/secops-nl2sql/scripts/lookup_udm_field.py "parent_process"
   ```

3. **Check Ingestion metric fields:**
   ```bash
   <PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/skills/secops-nl2sql/scripts/lookup_udm_field.py "log_volume"
   ```
