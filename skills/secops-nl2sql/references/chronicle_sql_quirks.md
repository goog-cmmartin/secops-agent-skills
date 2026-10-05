# Google SecOps Chronicle SQL Quirks & Engine Constraints

This reference document outlines the critical operational rules, engine limitations, and quirks when writing SQL for Google SecOps Native Dashboards and UDM Search.

---

## 1. Tables Overview

| Table | Purpose | Primary Time Partition Filter |
| :--- | :--- | :--- |
| **`events`** | Raw UDM events (process, network, auth, user, web) | `TIMESTAMP_SECONDS(metadata.event_timestamp.seconds) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL ...)` |
| **`graph`** | UDM Entity Graph / Context (assets, users, resources) | `TIMESTAMP_SECONDS(metadata.collected_timestamp.seconds) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL ...)` |
| **`ingestion`** | Ingestion pipeline metrics & telemetry (volume, errors) | `TIMESTAMP_SECONDS(start_time) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL ...)` |

---

## 2. Protobuf Default Values vs. NULL (The `NULLIF` Rule)

In Google SecOps, event records are backed by Protocol Buffers (proto3):
* Unset strings default to **`""` (empty string)**, **NOT `NULL`**.
* Unset integers default to `0`, unset booleans default to `false`.

### Required Patterns:
* **String Filtering:** Never write `WHERE field IS NOT NULL` alone if you want to skip blank fields. Write:
  ```sql
  WHERE NULLIF(metadata.log_type, '') IS NOT NULL
  ```
* **Fallback / COALESCE:** `COALESCE(principal.hostname, ip)` will evaluate to `""` if the hostname is unset, skipping the IP fallback! Always wrap:
  ```sql
  COALESCE(NULLIF(principal.hostname, ''), principal.ip[SAFE_OFFSET(0)], 'Unknown Host/IP')
  ```

---

## 3. Ingestion Table Metric Sparsity Trap

In the **`ingestion`** table:
* Volume metrics write to `log_volume` (with `log_count = 0`).
* Count metrics write to `log_count` (with `log_volume = 0`).

**Never** filter `WHERE log_volume > 0` in the main `WHERE` clause if you need `log_count` or `avg_bytes_per_log` (`total_size_bytes / total_logs`), because that drops all count metric records, forcing `SUM(log_count) = 0` and dividing by zero.

### Correct Pattern for Ingestion Queries:
```sql
FROM ingestion
|> WHERE component = 'Ingestion API'
     AND NULLIF(log_type, '') IS NOT NULL
     AND TIMESTAMP_SECONDS(start_time) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
|> AGGREGATE
     SUM(log_volume) AS total_size_bytes,
     SUM(log_count) AS total_logs,
     ROUND(SAFE_DIVIDE(SUM(log_volume), NULLIF(SUM(log_count), 0)), 2) AS avg_bytes_per_log,
     ROUND(AVG(IF(log_volume > 0, log_volume, NULL)), 2) AS avg_batch_bytes
   GROUP BY log_type
```

---

## 4. Native Dashboards Function Compatibility

| Function / Syntax | Supported in BigQuery Data Lake? | Supported in Chronicle Native Dashboards? | Native Dashboards Replacement |
| :--- | :--- | :--- | :--- |
| `SELECT * FROM ingestion` (or `SELECT * FROM <cte>` touching `ingestion`) | Yes | ❌ **Forbidden** (`selecting * from ingestion is not supported` or HTTP 500 `generic::unknown`) | Project explicit named columns in outer `SELECT` |
| `QUALIFY ROW_NUMBER() OVER (...) <= n` (without `WHERE`/`GROUP BY`/`HAVING`) | Yes | ❌ **Syntax error** unless preceded by `WHERE`, `GROUP BY`, or `HAVING` | Use Pipe Syntax `\|> EXTEND ROW_NUMBER() OVER (...) AS rn \|> WHERE rn <= n` |
| `APPROX_QUANTILES(col, n)`| Yes | ❌ **Function not found** | `PERCENT_RANK()` or `NTILE` with `MIN(IF(...))` |
| `PERCENTILE_CONT(col, p)` | Yes | ❌ **Function not found** | `PERCENT_RANK() OVER (...)` |
| `PERCENT_RANK() OVER ()`  | Yes | ✅ **Supported** | Use for exact continuous percentiles |
| `NTILE(n) OVER ()`        | Yes | ✅ **Supported** | Use for discrete bucket quantiles |
| `STDDEV(col)`, `AVG(col)` | Yes | ✅ **Supported** | Directly supported |

---

## 5. Safe Array Access vs. Correlated Subqueries

Avoid running correlated subqueries like `(SELECT ip FROM UNNEST(principal.ip) AS ip LIMIT 1)`:
* It forces the execution engine to evaluate a nested plan per row.
* Instead, use GoogleSQL **`[SAFE_OFFSET(0)]`**:
  ```sql
  principal.ip[SAFE_OFFSET(0)]
  security_result[SAFE_OFFSET(0)].action
  ```
  Returns `NULL` safely if the array is empty without indexing errors.
