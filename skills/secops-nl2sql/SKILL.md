---
name: secops-nl2sql
description: >-
  Converts natural language questions, YARA-L 2.0 queries, Sysmon/EDR XML configs,
  or BigQuery SQL into valid, optimized Google SecOps GoogleSQL and GoogleSQL Pipe Syntax (|>)
  queries for Native Dashboards, UDM Search, and SecOps Data Lake analytics.
---

# SecOps Natural Language to GoogleSQL / PipedSQL Skill

This skill guides the agent in authoring, optimizing, and self-validating GoogleSQL and GoogleSQL Pipe Syntax (`|>`) queries for Google SecOps Chronicle endpoints.

---

## Workflow Steps

### Step 1: Identify the Target Table and Time Filter
Determine the target dataset based on the user's intent:
1. **Raw Security Events (`events`):** Used for UDM event triage, actor/target investigations, network flow analysis, and process creation.
   * *Mandatory Filter:* `TIMESTAMP_SECONDS(metadata.event_timestamp.seconds) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL ...)`
2. **Context & Entity Graph (`graph`):** Used for asset metadata, IOC context, and entity source audits.
   * *Mandatory Filter:* `TIMESTAMP_SECONDS(metadata.collected_timestamp.seconds) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL ...)`
3. **Pipeline Ingestion Telemetry (`ingestion`):** Used for volume, log counts, parser error rates, and log tuning analytics.
   * *Mandatory Filter:* `TIMESTAMP_SECONDS(start_time) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL ...)`

---

### Step 2: Apply Chronicle Engine Invariants

Before drafting SQL, review the quirks in [chronicle_sql_quirks.md](./references/chronicle_sql_quirks.md):
1. **Protobuf `NULLIF` Rule:** Wrap all string filters and `COALESCE` statements in `NULLIF(col, '')` because unset protobuf strings default to `""`, not `NULL`.
2. **Safe Array Indexing:** Use `array_field[SAFE_OFFSET(0)]` instead of expensive correlated subqueries `(SELECT x FROM UNNEST(...) LIMIT 1)`.
3. **Ingestion Metric Sparsity:** Never filter `WHERE log_volume > 0` if calculating `log_count` or `avg_bytes_per_log`—`log_volume` and `log_count` are stored in separate rows.
4. **Native Dashboard Constraints:**
   * Never issue `SELECT * FROM ingestion` (unprojected table scans are forbidden).
   * Do not use `APPROX_QUANTILES` in Native Dashboards; use `PERCENT_RANK()` or `NTILE` with `MIN(IF(...))` as detailed in [piped_sql_patterns.md](./references/piped_sql_patterns.md).

---

### Step 3: Check UDM Field Mappings & Protos

1. Consult [udm_field_mappings.md](./references/udm_field_mappings.md) for standard Sysmon, Network, and Identity fields.
2. For obscure, nested, or repeated/array fields, inspect the authoritative local protobuf definitions in [proto_reference.md](./references/proto_reference.md) using the lookup helper:
   ```bash
   <PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/skills/secops-nl2sql/scripts/lookup_udm_field.py "<field_name>"
   ```
   * Identifies whether a field is a scalar (`string`) or array (`repeated`), dictating whether to use `SAFE_OFFSET(0)` / `UNNEST` or direct access.
3. **Windows Paths:** Always use `LOWER(...)` and raw string literals `r'c:\windows\...'` to avoid escape sequence errors.

---

### Step 4: Self-Validate the Query

Always validate the generated query before returning it to the user by invoking the built-in validation script:

```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/skills/secops-nl2sql/scripts/validate_sql.py "<GENERATED_QUERY>"
```

* If the script returns `STATUS: VALID`, proceed to deliver the query.
* If the script returns `STATUS: INVALID`, inspect the compiler error and line number, refine the query syntax, and re-validate until it passes.

---

### Step 5: Deliver the Solution

When responding to the user:
1. Provide the **GoogleSQL Pipe Syntax (`|>`)** query (preferred for Native Dashboards and modular readability).
2. Provide the **Standard GoogleSQL** query if relevant.
3. If applicable, highlight actionable security or log-tuning insights revealed by the query (e.g., high-frequency lease updates, noisy parent binaries).
