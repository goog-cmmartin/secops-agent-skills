# UDM & Log Ingestion Field Mapping Reference

This document maps common security telemetry concepts (Windows Sysmon, Network, Identity, Entity Graph) to canonical Google SecOps UDM fields.

---

## 1. Process Execution & Windows Sysmon Mappings

In Google SecOps, Sysmon Event ID 1 (`ProcessCreate`) maps to `metadata.event_type = 'PROCESS_LAUNCH'`:

| Telemetry Concept | Sysmon XML Tag | Canonical UDM Field | Notes |
| :--- | :--- | :--- | :--- |
| **Parent Binary** | `<ParentImage>` | `principal.process.file.full_path` | Initiator / parent executable path |
| **Parent CmdLine** | `<ParentCommandLine>` | `principal.process.command_line` | Command line that launched parent |
| **Child Binary** | `<Image>` | `target.process.file.full_path` | The spawned process |
| **Child CmdLine** | `<CommandLine>` | `target.process.command_line` | Arguments of the spawned process |
| **User/Actor** | `<User>` | `principal.user.userid` | Domain\Username or SID |
| **Parent PID** | `<ParentProcessId>` | `principal.process.pid` | Process ID of parent |
| **Child PID** | `<ProcessId>` | `target.process.pid` | Process ID of spawned process |
| **Process Hash** | `<Hashes>` | `target.process.file.sha256` / `md5` | Cryptographic hashes |

---

## 2. Network Telemetry & CIDR Inspection

* **Event Types:** `NETWORK_FLOW`, `NETWORK_CONNECTION`, `NETWORK_DNS`, `NETWORK_HTTP`
* **Source Asset:** `principal.ip` (array of strings), `principal.port`, `principal.hostname`
* **Destination Asset:** `target.ip` (array of strings), `target.port`, `target.hostname`
* **Protocol:** `network.ip_protocol` (e.g. `'TCP'`, `'UDP'`)

### Loopback Noise Filtering Example:
```sql
AND (
  NET.IP_TRUNC(NET.SAFE_IP_FROM_STRING(principal.ip[SAFE_OFFSET(0)]), 8) = NET.IP_FROM_STRING('127.0.0.0')
  OR principal.ip[SAFE_OFFSET(0)] = '::1'
)
```

---

## 3. Metadata & Labels

| Concept | UDM Field | Ingestion Format | Query Example |
| :--- | :--- | :--- | :--- |
| **Log Type** | `metadata.log_type` | String | `NULLIF(metadata.log_type, '') IS NOT NULL` |
| **Product Event Type**| `metadata.product_event_type` | String | `metadata.product_event_type = 'io.k8s...'` |
| **Ingestion Labels** | `metadata.ingestion_labels` | Repeated `{key, value}` | `UNNEST(metadata.ingestion_labels) AS label` |
| **Data RBAC Namespaces**| `metadata.base_labels.namespaces`| Repeated `string` | `UNNEST(metadata.base_labels.namespaces) AS ns` |

---

## 4. Entity Graph (`graph` table)

* **Table:** `graph`
* **Entity Identifier:** `graph.metadata.product_entity_id`
* **Entity Source:** `graph.metadata.source_type` (e.g., `'DERIVED_CONTEXT'`, `'GCP_THREATINTEL'`)
* **Associated Log Types:** `metadata.event_metadata.base_labels.log_types`
* **Collected Timestamp:** `TIMESTAMP_SECONDS(metadata.collected_timestamp.seconds)`
