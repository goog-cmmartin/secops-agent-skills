# GoogleSQL Pipe Syntax (`|>`) Patterns for Google SecOps

This reference contains standard, battle-tested Piped SQL patterns for Chronicle Native Dashboards and UDM Search.

---

## Pattern 1: Aggregate and Window Percentage

Compute total counts and percent share without repeating `COUNT(1)` inside the window function:

```sql
FROM events
|> WHERE (TIMESTAMP_SECONDS(metadata.event_timestamp.seconds) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY))
     AND NULLIF(metadata.log_type, '') IS NOT NULL
|> AGGREGATE COUNT(1) AS event_count
   GROUP BY metadata.log_type
|> EXTEND
     ROUND(event_count * 100.0 / SUM(event_count) OVER (), 2) AS percent_of_total
|> ORDER BY event_count DESC
|> LIMIT 20;
```

---

## Pattern 2: Continuous Percentiles & Median (P50, P90, P95)

Calculate batch size distributions when `APPROX_QUANTILES` is unavailable:

```sql
FROM ingestion
|> WHERE component = 'Ingestion API'
     AND NULLIF(log_type, '') IS NOT NULL
     AND TIMESTAMP_SECONDS(start_time) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
|> SELECT log_type, log_volume, log_count
|> EXTEND PERCENT_RANK() OVER (
     PARTITION BY log_type, (log_volume > 0)
     ORDER BY log_volume
   ) AS vol_pct_rank
|> AGGREGATE
     ROUND(SAFE_DIVIDE(SUM(log_volume), NULLIF(SUM(log_count), 0)), 2) AS avg_bytes_per_log,
     ROUND(AVG(IF(log_volume > 0, log_volume, NULL)), 2) AS avg_batch_bytes,
     COALESCE(MIN(IF(log_volume > 0 AND vol_pct_rank >= 0.50, log_volume, NULL)), MAX(log_volume)) AS median_batch_bytes,
     COALESCE(MIN(IF(log_volume > 0 AND vol_pct_rank >= 0.90, log_volume, NULL)), MAX(log_volume)) AS p90_batch_bytes,
     COALESCE(MIN(IF(log_volume > 0 AND vol_pct_rank >= 0.95, log_volume, NULL)), MAX(log_volume)) AS p95_batch_bytes
   GROUP BY log_type
|> ORDER BY avg_batch_bytes DESC
|> LIMIT 20;
```

---

## Pattern 3: Subquery JOINs (`events` $\bowtie$ `ingestion`)

Correlate granular UDM event types with ingestion pipeline telemetry using `|> JOIN (...) USING (key)`:

```sql
FROM events
|> WHERE (TIMESTAMP_SECONDS(metadata.event_timestamp.seconds) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY))
     AND NULLIF(metadata.log_type, '') IS NOT NULL
|> AGGREGATE COUNT(1) AS event_count
   GROUP BY metadata.log_type, metadata.product_event_type
|> JOIN (
     FROM ingestion
     |> WHERE component = 'Ingestion API'
          AND NULLIF(log_type, '') IS NOT NULL
          AND TIMESTAMP_SECONDS(start_time) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
     |> AGGREGATE ROUND(SAFE_DIVIDE(SUM(log_volume), NULLIF(SUM(log_count), 0)), 2) AS avg_bytes_per_log
        GROUP BY log_type
   ) USING (log_type)
|> EXTEND
     ROUND(event_count * avg_bytes_per_log / 1048576.0, 2) AS est_total_mb,
     ROUND(event_count * 100.0 / SUM(event_count) OVER (PARTITION BY log_type), 2) AS pct_of_log_type
|> ORDER BY est_total_mb DESC
|> LIMIT 50;
```

---

## Pattern 4: Windows Path & Sysmon Filter Matching

Handling Windows case-insensitivity and backslashes using `LOWER()` and raw string literals `r'...'`:

```sql
FROM events
|> WHERE (TIMESTAMP_SECONDS(metadata.event_timestamp.seconds) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY))
     AND metadata.event_type = 'PROCESS_LAUNCH'
     AND (
       LOWER(principal.process.file.full_path) IN (
         r'c:\windows\system32\conhost.exe',
         r'c:\windows\microsoft.net\framework64\v4.0.30319\mscorsvw.exe'
       )
       OR STARTS_WITH(LOWER(target.process.command_line), r'c:\windows\system32\svchost.exe -k')
     )
|> AGGREGATE COUNT(1) AS event_count
   GROUP BY
     principal.process.file.full_path,
     target.process.file.full_path
|> ORDER BY event_count DESC
|> LIMIT 50;
```
