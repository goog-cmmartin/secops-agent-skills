# GoogleSQL Pipe Syntax (`|>`) Templates for SecOps Log Tuning

All queries below are validated for the Google SecOps Chronicle Dashboard Engine (`dashboardQueries:execute`).

---

## Stage 1: Macro Volume & `event_type` Discovery (`events` $\bowtie$ `ingestion`)

Ranks the top `log_type` sources by byte volume from `ingestion`, joins against `events` grouped by `(metadata.log_type, metadata.event_type, metadata.product_event_type)`, and returns the top event categories along with `avg_bytes_per_log` and estimated MB:

```sql
FROM events
|> WHERE TIMESTAMP_SECONDS(metadata.event_timestamp.seconds) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
     AND NULLIF(metadata.log_type, '') IS NOT NULL
|> AGGREGATE COUNT(1) AS event_count
   GROUP BY
     metadata.log_type AS log_type,
     metadata.event_type AS event_type,
     COALESCE(NULLIF(metadata.product_event_type, ''), 'UNSET') AS product_event_type
|> JOIN (
     FROM ingestion
     |> WHERE component = 'Ingestion API'
          AND NULLIF(log_type, '') IS NOT NULL
          AND TIMESTAMP_SECONDS(start_time) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
     |> AGGREGATE
          SUM(log_volume) AS total_volume_bytes,
          SUM(log_count) AS total_ingested_logs,
          ROUND(SAFE_DIVIDE(SUM(log_volume), NULLIF(SUM(log_count), 0)), 2) AS avg_bytes_per_log
        GROUP BY log_type
     |> ORDER BY total_volume_bytes DESC
     |> LIMIT 10
   ) USING (log_type)
|> EXTEND
     SUM(event_count) OVER (PARTITION BY log_type) AS total_udm_events_for_log_type,
     ROUND(event_count * 100.0 / SUM(event_count) OVER (PARTITION BY log_type), 2) AS pct_of_log_type,
     ROUND(total_volume_bytes / 1073741824.0, 2) AS log_type_ingested_gb,
     ROUND(event_count * avg_bytes_per_log / 1048576.0, 2) AS est_product_event_mb,
     ROW_NUMBER() OVER (PARTITION BY log_type ORDER BY event_count DESC) AS rank_in_log_type
|> WHERE rank_in_log_type <= 5
|> ORDER BY total_volume_bytes DESC, pct_of_log_type DESC
|> LIMIT 50;
```

---

## Stage 2 Templates by `metadata.event_type` Family

### 1. File Activity (`FILE_CREATION`, `FILE_DELETION`, `FILE_MODIFICATION`, `FILE_*`)

Groups by the acting binary (`principal.process.file.full_path`) and aggregates `COUNT(DISTINCT target.file.full_path)` + `ANY_VALUE(target.file.full_path)` so ephemeral temp/lock filenames do not shatter the aggregation:

```sql
FROM events
|> WHERE TIMESTAMP_SECONDS(metadata.event_timestamp.seconds) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
     AND metadata.log_type = '<LOG_TYPE>'
     AND metadata.event_type = '<EVENT_TYPE>'
     AND COALESCE(NULLIF(metadata.product_event_type, ''), 'UNSET') = '<PRODUCT_EVENT_TYPE>'
|> AGGREGATE
     COUNT(1) AS event_count,
     COUNT(DISTINCT principal.hostname) AS distinct_hosts,
     ANY_VALUE(principal.hostname) AS sample_host,
     COUNT(DISTINCT target.file.full_path) AS distinct_targets,
     ANY_VALUE(target.file.full_path) AS sample_target
   GROUP BY
     COALESCE(NULLIF(principal.process.file.full_path, ''), NULLIF(target.process.file.full_path, ''), 'UNSET') AS actor_dimension
|> EXTEND
     ROUND(event_count * 100.0 / SUM(event_count) OVER (), 2) AS pct_of_category,
     ROUND(event_count * <AVG_BYTES_PER_LOG> / 1048576.0, 2) AS est_mb
|> ORDER BY event_count DESC
|> LIMIT 10;
```

---

### 2. Process & Script Activity (`PROCESS_LAUNCH`, `PROCESS_UNCATEGORIZED`, `PROCESS_*`)

Groups by parent and target process paths, aggregating distinct command lines and supplying a sample command line / script block:

```sql
FROM events
|> WHERE TIMESTAMP_SECONDS(metadata.event_timestamp.seconds) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
     AND metadata.log_type = '<LOG_TYPE>'
     AND metadata.event_type = '<EVENT_TYPE>'
     AND COALESCE(NULLIF(metadata.product_event_type, ''), 'UNSET') = '<PRODUCT_EVENT_TYPE>'
|> AGGREGATE
     COUNT(1) AS event_count,
     COUNT(DISTINCT principal.hostname) AS distinct_hosts,
     ANY_VALUE(principal.hostname) AS sample_host,
     COUNT(DISTINCT target.process.command_line) AS distinct_targets,
     ANY_VALUE(SUBSTR(target.process.command_line, 1, 200)) AS sample_target
   GROUP BY
     COALESCE(NULLIF(principal.process.file.full_path, ''), 'UNSET') AS parent_process,
     COALESCE(NULLIF(target.process.file.full_path, ''), SUBSTR( NULLIF(target.process.command_line, ''), 1, 120), 'UNSET') AS actor_dimension
|> EXTEND
     ROUND(event_count * 100.0 / SUM(event_count) OVER (), 2) AS pct_of_category,
     ROUND(event_count * <AVG_BYTES_PER_LOG> / 1048576.0, 2) AS est_mb
|> ORDER BY event_count DESC
|> LIMIT 10;
```

---

### 3. DNS Telemetry (`NETWORK_DNS`)

Groups by queried domain (`network.dns.questions[SAFE_OFFSET(0)].name`) and resolver hop (`principal.ip` $\rightarrow$ `target.ip`):

```sql
FROM events
|> WHERE TIMESTAMP_SECONDS(metadata.event_timestamp.seconds) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
     AND metadata.log_type = '<LOG_TYPE>'
     AND metadata.event_type = 'NETWORK_DNS'
     AND COALESCE(NULLIF(metadata.product_event_type, ''), 'UNSET') = '<PRODUCT_EVENT_TYPE>'
|> AGGREGATE
     COUNT(1) AS event_count,
     COUNT(DISTINCT principal.ip[SAFE_OFFSET(0)]) AS distinct_hosts,
     ANY_VALUE(principal.ip[SAFE_OFFSET(0)]) AS sample_host,
     COUNT(DISTINCT target.ip[SAFE_OFFSET(0)]) AS distinct_targets,
     ANY_VALUE(target.ip[SAFE_OFFSET(0)]) AS sample_target
   GROUP BY
     COALESCE(NULLIF(network.dns.questions[SAFE_OFFSET(0)].name, ''), 'UNSET') AS actor_dimension,
     COALESCE(NULLIF(principal.ip[SAFE_OFFSET(0)], ''), 'UNSET') AS src_ip,
     COALESCE(NULLIF(target.ip[SAFE_OFFSET(0)], ''), 'UNSET') AS dst_ip
|> EXTEND
     ROUND(event_count * 100.0 / SUM(event_count) OVER (), 2) AS pct_of_category,
     ROUND(event_count * <AVG_BYTES_PER_LOG> / 1048576.0, 2) AS est_mb
|> ORDER BY event_count DESC
|> LIMIT 10;
```

---

### 4. Network Connections & Flows (`NETWORK_CONNECTION`, `NETWORK_FLOW`, `NETWORK_*`)

Groups by source IP, destination IP, destination port, and protocol to expose noisy internal polling, resolver loops, or duplicate firewall/IDS rules:

```sql
FROM events
|> WHERE TIMESTAMP_SECONDS(metadata.event_timestamp.seconds) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
     AND metadata.log_type = '<LOG_TYPE>'
     AND metadata.event_type = '<EVENT_TYPE>'
     AND COALESCE(NULLIF(metadata.product_event_type, ''), 'UNSET') = '<PRODUCT_EVENT_TYPE>'
|> AGGREGATE
     COUNT(1) AS event_count,
     COUNT(DISTINCT principal.ip[SAFE_OFFSET(0)]) AS distinct_hosts,
     ANY_VALUE(principal.ip[SAFE_OFFSET(0)]) AS sample_host,
     COUNT(DISTINCT target.ip[SAFE_OFFSET(0)]) AS distinct_targets,
     ANY_VALUE(security_result[SAFE_OFFSET(0)].summary) AS sample_target
   GROUP BY
     COALESCE(NULLIF(principal.ip[SAFE_OFFSET(0)], ''), 'UNSET') AS src_ip,
     COALESCE(NULLIF(target.ip[SAFE_OFFSET(0)], ''), 'UNSET') AS dst_ip,
     target.port AS dst_port,
     network.ip_protocol AS ip_protocol
|> EXTEND
     ROUND(event_count * 100.0 / SUM(event_count) OVER (), 2) AS pct_of_category,
     ROUND(event_count * <AVG_BYTES_PER_LOG> / 1048576.0, 2) AS est_mb
|> ORDER BY event_count DESC
|> LIMIT 10;
```

---

### 5. Web / Proxy HTTP Activity (`NETWORK_HTTP`)

Groups by destination hostname and user agent:

```sql
FROM events
|> WHERE TIMESTAMP_SECONDS(metadata.event_timestamp.seconds) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
     AND metadata.log_type = '<LOG_TYPE>'
     AND metadata.event_type = 'NETWORK_HTTP'
     AND COALESCE(NULLIF(metadata.product_event_type, ''), 'UNSET') = '<PRODUCT_EVENT_TYPE>'
|> AGGREGATE
     COUNT(1) AS event_count,
     COUNT(DISTINCT principal.ip[SAFE_OFFSET(0)]) AS distinct_hosts,
     ANY_VALUE(principal.ip[SAFE_OFFSET(0)]) AS sample_host,
     COUNT(DISTINCT target.url) AS distinct_targets,
     ANY_VALUE(SUBSTR(target.url, 1, 150)) AS sample_target
   GROUP BY
     COALESCE(NULLIF(target.hostname, ''), NULLIF(target.ip[SAFE_OFFSET(0)], ''), 'UNSET') AS actor_dimension,
     COALESCE(NULLIF(network.http.parsed_user_agent, ''), NULLIF(network.http.user_agent, ''), 'UNSET') AS user_agent
|> EXTEND
     ROUND(event_count * 100.0 / SUM(event_count) OVER (), 2) AS pct_of_category,
     ROUND(event_count * <AVG_BYTES_PER_LOG> / 1048576.0, 2) AS est_mb
|> ORDER BY event_count DESC
|> LIMIT 10;
```

---

### 6. Registry Activity (`REGISTRY_MODIFICATION`, `REGISTRY_*`)

Groups by acting process path and registry key:

```sql
FROM events
|> WHERE TIMESTAMP_SECONDS(metadata.event_timestamp.seconds) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
     AND metadata.log_type = '<LOG_TYPE>'
     AND metadata.event_type = '<EVENT_TYPE>'
     AND COALESCE(NULLIF(metadata.product_event_type, ''), 'UNSET') = '<PRODUCT_EVENT_TYPE>'
|> AGGREGATE
     COUNT(1) AS event_count,
     COUNT(DISTINCT principal.hostname) AS distinct_hosts,
     ANY_VALUE(principal.hostname) AS sample_host,
     COUNT(DISTINCT target.registry.registry_value_name) AS distinct_targets,
     ANY_VALUE(target.registry.registry_value_name) AS sample_target
   GROUP BY
     COALESCE(NULLIF(principal.process.file.full_path, ''), 'UNSET') AS actor_dimension,
     COALESCE(NULLIF(target.registry.registry_key, ''), 'UNSET') AS registry_key
|> EXTEND
     ROUND(event_count * 100.0 / SUM(event_count) OVER (), 2) AS pct_of_category,
     ROUND(event_count * <AVG_BYTES_PER_LOG> / 1048576.0, 2) AS est_mb
|> ORDER BY event_count DESC
|> LIMIT 10;
```

---

### 7. User, Resource, Permission & System Events (`USER_*`, `RESOURCE_*`, `STATUS_UPDATE`, `GENERIC_EVENT`)

Groups by acting process or target resource/namespace (`principal.process.file.full_path`, `target.resource.name`, `principal.application`) and reports `distinct_hosts` + `sample_host` to separate fleet-wide WMI/daemon polling from single-host audit outliers:

```sql
FROM events
|> WHERE TIMESTAMP_SECONDS(metadata.event_timestamp.seconds) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
     AND metadata.log_type = '<LOG_TYPE>'
     AND metadata.event_type = '<EVENT_TYPE>'
     AND COALESCE(NULLIF(metadata.product_event_type, ''), 'UNSET') = '<PRODUCT_EVENT_TYPE>'
|> AGGREGATE
     COUNT(1) AS event_count,
     COUNT(DISTINCT COALESCE(NULLIF(principal.hostname, ''), NULLIF(target.hostname, ''))) AS distinct_hosts,
     ANY_VALUE(COALESCE(NULLIF(principal.hostname, ''), NULLIF(target.hostname, ''))) AS sample_host,
     COUNT(DISTINCT COALESCE(NULLIF(principal.user.userid, ''), NULLIF(target.user.userid, ''))) AS distinct_targets,
     ANY_VALUE(COALESCE(NULLIF(principal.user.userid, ''), NULLIF(target.user.userid, ''))) AS sample_target
   GROUP BY
     COALESCE(
       NULLIF(principal.process.file.full_path, ''),
       NULLIF(target.process.file.full_path, ''),
       NULLIF(target.resource.name, ''),
       NULLIF(principal.application, ''),
       NULLIF(security_result[SAFE_OFFSET(0)].summary, ''),
       'UNSET'
     ) AS actor_dimension
|> EXTEND
     ROUND(event_count * 100.0 / SUM(event_count) OVER (), 2) AS pct_of_category,
     ROUND(event_count * <AVG_BYTES_PER_LOG> / 1048576.0, 2) AS est_mb
|> ORDER BY event_count DESC
|> LIMIT 10;
```
