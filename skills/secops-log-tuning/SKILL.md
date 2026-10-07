---
name: secops-log-tuning
description: >-
  Identifies high-volume log sources and noisy event patterns in Google SecOps (Chronicle)
  by joining ingestion telemetry with UDM events, routing by metadata.event_type to
  actor-grouped Stage 2 dimensional drill-downs, and quantifying byte/GB savings for
  fleet-wide policy exclusions vs. single-host outliers.
---

# SecOps Log Volume & Ingestion Tuning Skill

This skill guides the agent through a two-stage data-driven log tuning workflow in Google SecOps (Chronicle):
1. **Stage 1 (Macro Volume & `event_type` Discovery):** Join the `ingestion` metrics table with `events` to find the highest-volume `log_type` sources and their top `(metadata.event_type, metadata.product_event_type)` combinations.
2. **Stage 2 (Actor-Grouped Dimensional Drill-Down):** Route each noisy category by its canonical `metadata.event_type` to a targeted Piped SQL query that isolates the exact binaries, file paths, DNS queries, network flows, or hosts responsible for the volume.

---

## Core Design Rules

### 1. Route Drill-Downs by `metadata.event_type`, Not `metadata.product_event_type`
`metadata.product_event_type` is vendor-specific (`"File Creation"`, `"4662"`, `"dns"`, `"7"`). Always include `metadata.event_type` (`FILE_CREATION`, `PROCESS_LAUNCH`, `NETWORK_DNS`, `NETWORK_CONNECTION`, `USER_RESOURCE_ACCESS`, etc.) in Stage 1 so Stage 2 knows which UDM noun fields (`principal.process`, `target.file`, `network.dns`, `target.resource`) are populated.

### 2. The High-Cardinality Shattering Rule
Never place ephemeral or randomized target fields (`target.file.full_path` containing random `.tmp`/`.lock` filenames, dynamic command lines with PIDs/GUIDs, or ephemeral source ports) directly into `GROUP BY` during initial drill-down. Doing so shatters millions of identical events into hundreds of thousands of 1-event buckets, hiding the #1 offender.

Instead:
* **Group by stable policy/actor dimensions:** `principal.process.file.full_path`, `principal.ip[SAFE_OFFSET(0)]`, `target.ip[SAFE_OFFSET(0)]`, `target.port`, `network.dns.questions[SAFE_OFFSET(0)].name`, `target.resource.name`.
* **Aggregate high-cardinality target dimensions:**
  ```sql
  COUNT(DISTINCT target.file.full_path) AS distinct_targets,
  ANY_VALUE(target.file.full_path) AS sample_target,
  COUNT(DISTINCT principal.hostname) AS distinct_hosts
  ```
* If `distinct_targets` is small (e.g., `< 10`), the noise targets a fixed file or command. If `distinct_targets` is huge (e.g., `500,000` lock files created by `ruby.exe`), `sample_target` reveals the naming pattern (`C:\Windows\Temp\puppet*.lock`) without shattering the count.

### 3. Fleet-Wide Policy vs. Single-Host Outlier & Source Misconfiguration Diagnosis
Always compute `COUNT(DISTINCT principal.hostname) AS distinct_hosts` (or `distinct_src_ips` for network logs) and the per-host event rate (`events_per_sec_per_host = event_count / (days * 86400 * distinct_hosts)`):
* **`distinct_hosts <= 3` (Single-Host / Collector Outlier):** Volume is concentrated on 1–3 machines or a single forwarding resolver (e.g., a domain controller `SITE-DC$` forwarding DNS queries on behalf of clients, which masks the true client IPs).
* **`events_per_sec_per_host >= 1.0` (Likely Source Misconfiguration — Fix at Source First):** When a single host emits multiple identical queries or status events per second (e.g., 12 NTP lookups/sec with `.site.lan` search-domain suffixing or 5+ `msftconnecttest.com` probes/sec), diagnose it as a **broken host/service configuration** (broken `timesyncd`/`chrony`, missing local NTP server, bad `ndots`/search domain, or broken disk multipath daemon). Recommend fixing the underlying service first and deploying a **tuple-pinned collector filter** only as a stopgap.
* **`distinct_hosts > 3` (Fleet-Wide Policy Exclusion):** Volume is systemic across the fleet. Remediate via EDR/collector path or process exclusions, or Chronicle ingestion filters.

### 4. Detection Safety, Tuple Pinning, Correlated Zeek Logs, & Shared Cloud IP / TLS SNI Rules
* **Never Recommend Dropping Poisoning / Lateral Movement Ports:** Never drop **LLMNR (`5355`)**, **NBT-NS (`137`, `138`, `139`)**, **SMB (`445`)**, **MS-RPC (`135`)**, or **LDAP (`389`, `636`)**. Only **SSDP (`1900`)** and **mDNS (`5353`)** belong in multicast discovery drop lists.
* **Always Pin the Tuple on Low-Host-Count Noise:** Never recommend dropping a DNS domain (`ntp.ubuntu.com`, `msftconnecttest.com`) across all hosts when only a few hosts are noisy. Pin the filter to the exact `(src_ip, dst_port, lower(query))` tuple and use case-insensitive matching (`ConvertCase(body["query"], "lower")`) to handle DNS 0x20 capitalization.
* **Account for Correlated Zeek Logs (`dns` + `conn`):** In `BRO_JSON` (Zeek), every `dns` event also writes a `conn` event on port 53 (`id.resp_p == 53`). Note that filtering only `dns` leaves the matching `conn` volume unless a matching pinned `conn` filter is also applied.
* **Never Recommend Dropping Shared Cloud/CDN IPs (`443`) Without TLS SNI (`network.tls.client.server_name`):** Steady HTTPS polling to Microsoft/Azure/AWS/CDN IPs (e.g., `20.112.250.133:443` at ~5/sec) resembles C2 beaconing. Always inspect `network.tls.client.server_name` (Zeek `ssl.server_name`) and the originating host/process before considering aggregation or filtering.

---

## Workflow Steps

### Step 1: Run Automated 2-Stage Tuning Analysis (Recommended)

Run the built-in two-stage tuning analyzer, which executes Stage 1 (`events` $\bowtie$ `ingestion`) and parallel Stage 2 dimensional drill-downs via the Chronicle Dashboard Engine:

```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/skills/secops-log-tuning/scripts/run_log_tuning.py --days 7 --top-log-types 5 --top-categories 3
```

**Options:**
* `--days <N>`: Lookback window in days (default: `7`).
* `--top-log-types <N>`: Number of top `log_type` sources by byte volume to analyze (default: `5`).
* `--top-categories <K>`: Number of top `(event_type, product_event_type)` categories per `log_type` to drill into (default: `3`).
* `--log-type <LOG_TYPE>`: Optional filter to analyze a single specific `log_type` (e.g., `--log-type SENTINELONE_CF`).
* `--min-mb <FLOAT>`: Minimum estimated volume in MB to trigger a Stage 2 drill-down (default: `50.0`).

---

### Step 2: Run Custom Stage 2 Drill-Downs (When Investigating Specific Patterns)

Consult [tuning_query_templates.md](./references/tuning_query_templates.md) for the canonical GoogleSQL Pipe Syntax (`|>`) templates for each `metadata.event_type` family (`FILE_*`, `PROCESS_*`, `NETWORK_DNS`, `NETWORK_CONNECTION`, `NETWORK_HTTP`, `REGISTRY_*`, `USER_*` / `RESOURCE_*`), and execute them via `validate_sql.py --execute`:

```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/skills/secops-nl2sql/scripts/validate_sql.py --execute --days 7 "<STAGE_2_PIPED_SQL>"
```

---

### Step 3: Deliver the Tuning Report

Structure your findings for the user with:
1. **Macro Volume Summary Table:** Top `log_type`s, 7-day ingested GB, `avg_bytes_per_log`, and top `(event_type, product_event_type)` shares.
2. **Stage 2 Dimensional Breakdowns:** For each major volume driver, show:
   * Top actor/process/flow dimensions
   * Event count, `% of category`, and **estimated MB/GB savings** (`event_count * avg_bytes_per_log`)
   * `distinct_hosts` / `distinct_src_ips` and `distinct_targets` + `sample_target`
3. **Prioritized Tuning Recommendations:** Explicitly label each recommendation as **Fleet-Wide Exclusion** or **Single-Host / Sensor Fix**, state the exact filter criteria (process path, temp file pattern, DNS domain, resolver hop, or Windows Event ID + host), and include the validated Piped SQL queries so the user can save them to a Chronicle Native Dashboard.
