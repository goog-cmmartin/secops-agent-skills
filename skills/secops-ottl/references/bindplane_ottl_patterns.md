# Bindplane & Google SecOps OTTL Patterns

This reference documents how Bindplane represents OTTL processors via its REST API (`/v1`), how collector pipeline ordering affects OTTL field paths (`body` MAP vs `body` STRING), detection safety rules, and tuple-pinned OTTL recipes for tuning high-volume Google SecOps log sources.

---

## 1. Bindplane REST API & Authentication

- **Base URL**: `https://app.bindplane.com/v1` (or self-hosted Bindplane OP URL)
- **Authentication Headers**:
  ```http
  X-Bindplane-Api-Key: <BINDPLANE_API_KEY>
  X-Bindplane-Account-ID: <BINDPLANE_PROJECT_ID>
  Accept: application/json
  Content-Type: application/json
  ```
- **Core Endpoints**:
  - `GET /v1/configurations` — List all collector configurations (`{"configurations": [...]}`).
  - `GET /v1/configurations/{name}` — Get a specific configuration (`{"configuration": {...}}`).
  - `GET /v1/processors` — List all reusable processors (`{"processors": [...]}`).
  - `GET /v1/processors/{name}` — Get a specific reusable processor definition.
  - `DELETE /v1/processors/{name}` — Delete a reusable processor from the library.
  - `GET /v1/processor-types/{type}` — Inspect parameter schemas for a processor type (`transform:2`, `filter-by-condition:3`, `secops_filter:2`, `processor_bundle:2`, `google_secops_standardization:5`).
  - `POST /v1/apply` — Upsert one or more Bindplane resources (`{"resources": [ ... ]}`).
  - `POST /v1/rollout/{config_name}` — Start a configuration rollout after editing a configuration.

> **Important Note on `/v1/apply`:** Bindplane's `/v1/apply` endpoint validates the JSON structure and parameter names of the processor resource, **not** the internal OTTL syntax string. Always run `validate_ottl.py` and `bindplane_cli.py audit-config <NAME>` before calling `/v1/apply`.

---

## 2. Pipeline Ordering, `body` State Machine & Fail-Open Behavior

In Bindplane configurations that export to Google SecOps (`google_secops_standardization:5`), `body` changes type as it moves through the pipeline:

1. **Before `parse_json:3` (`body` is `STRING`)**:
   - Raw log line is in `body` / `body.string`.
2. **After `parse_json:3` (`body` is `MAP`)**:
   - `parse_json:3` parses the JSON string into a structured map in `body`.
   - **Recommended Filter Position:** Place all `filter-by-condition:3` processors **immediately after `parse_json:3`** (even before `copy_field_v2:3` and `google_secops_standardization:5`) so later processors process fewer records.
   - Because `body` is a `MAP` here:
     - **DO:** Access parsed fields (`body["id.orig_h"]`, `body["id.resp_h"]`, `body["id.resp_p"]`, `body["query"]`).
     - **DO NOT:** Pass `body` directly to `IsMatch(body, "...")`. Passing a `MAP` to `IsMatch` fails at runtime!
3. **After `google_secops_standardization:5` or `marshal:5` (`body` is `STRING` again)**:
   - `google_secops_standardization:5` (`BRO_JSON`, `NIX_SYSTEM`, `WINEVTLOG`) serializes `body` back into a raw JSON string and sets `attributes["chronicle_log_type"]`.
   - Any `filter-by-condition:3` placed *after* `google_secops_standardization:5` that indexes `body["id.resp_p"]` will evaluate to `nil`.
4. **How Type Mismatches Fail (`error_mode: ignore`)**:
   - With `error_mode: ignore`, a filter condition that errors (such as `IsMatch(body, ...)` when `body` is a `MAP`, or `body["id.resp_p"] == 1900` when `body` is a `STRING`) evaluates to `false` and **keeps the log**.
   - **Reorder Hazard:** If an existing pipeline has two filters after `google_secops_standardization:5`—one using `IsMatch(body, ...)` and one using `body["id.resp_p"]`—simply dragging both filters before `google_secops_standardization:5` fixes the second filter but **breaks the first filter** (`IsMatch(body, ...)` now receives a `MAP` and stops dropping anything). Rewrite the first filter to match on parsed fields (`body["id.resp_h"]`, `body["id.orig_h"]`) before moving it!

---

## 3. Detection Safety & High-Confidence Filtering Rules

1. **Never Drop Lateral Movement or Name-Resolution Poisoning Ports:**
   - **KEEP:** `UDP/5355` (**LLMNR**) and `UDP/137` (**NBT-NS**) — required to detect Responder / Inveigh poisoning. Also watch for typos like `131` (often meant to be `137`).
   - **KEEP:** `445` (SMB), `135` (MS-RPC), `88` (Kerberos), `389`/`636` (LDAP/LDAPS).
   - **SAFE TO DROP (Multicast Discovery Chaff):** `1900` (SSDP) and `5353` (mDNS).
2. **Pin the Tuple (Source IP / Host + Query / Process):**
   - When a small set of hosts generates millions of repetitive queries (for example, broken NTP sync or `msftconnecttest.com` probes), **remediate the underlying host misconfiguration first** (fix `timesyncd`/`chrony`, local NTP server, or `ndots`/search domain).
   - When adding a collector filter as a stopgap, **always pin `body["id.orig_h"]`** (or `resource.attributes["host.name"]`) to the exact noisy hosts. Dropping a domain across all hosts creates a fleet-wide blind spot.
   - Note if a noisy source IP is an internal DNS server/DC (for example, `SITE-DC$`) forwarding queries on behalf of downstream clients.
3. **Handle DNS 0x20 Case Randomization & Prefer Exact Comparisons:**
   - Resolvers using 0x20 encoding randomize query letter casing (`NtP.UbUnTu.CoM`). Always normalize with `ConvertCase(body["query"], "lower")`.
   - Use exact equality (`ConvertCase(body["query"], "lower") == "www.msftconnecttest.com"`) rather than regex whenever matching static FQDNs.
4. **Account for Correlated Zeek Logs (`dns.log` + `conn.log`):**
   - Every Zeek `dns` flow also writes a `conn` log on `id.resp_p == 53`. Filtering only `body["query"]` leaves the matching `conn` records unless you also filter or account for the pinned `conn` tuple.
5. **Never Blindly Drop Shared Cloud/CDN IPs (`443`):**
   - High-frequency HTTPS polling to Microsoft/Azure/AWS/CDN IPs (e.g., `20.112.250.133:443`) looks identical to C2 beaconing at the IP layer. Always inspect `ssl.server_name` (TLS SNI) first and never drop a shared cloud IP by destination address alone.

---

## 4. Corrected Bindplane OTTL Processor Recipes

### Recipe 1: Corrected Zeek (`BRO_JSON`) Pipeline Order & Filters (Placed Immediately After `parse_json:3`)

**Processor 2 — Broadcast / Multicast Filter (Rewritten for Parsed `MAP` Fields):**
```text
body["id.resp_h"] == "255.255.255.255" or IsMatch(body["id.resp_h"], "^(224|239)\\.\\d+\\.\\d+\\.\\d+$") or IsMatch(ConvertCase(body["id.resp_h"], "lower"), "^ff0[0-9a-f]:")
```

**Processor 3 — Multicast Discovery Port Filter (SSDP `1900` & mDNS `5353` ONLY — Preserves LLMNR `5355` and NBT-NS `137`):**
```text
body["id.resp_p"] == 1900 or body["id.resp_p"] == 5353
```

**Processor 4 — Tuple-Pinned, Case-Normalized DNS Stopgap Filter:**
```text
body["id.resp_p"] == 53 and ((IsMatch(ConvertCase(body["query"], "lower"), "^ntp\\.ubuntu\\.com(\\.site\\.lan)?$") and (body["id.orig_h"] == "172.16.2.7" or body["id.orig_h"] == "172.16.5.110" or body["id.orig_h"] == "172.16.5.111" or body["id.orig_h"] == "172.16.1.12")) or ((ConvertCase(body["query"], "lower") == "www.msftconnecttest.com" or ConvertCase(body["query"], "lower") == "ipv6.msftconnecttest.com") and (body["id.orig_h"] == "172.16.1.12" or body["id.orig_h"] == "172.16.2.7")))
```

### Recipe 2: Windows Event Logs (`WINEVTLOG`) — Host-Pinned Token Right Adjustments (`4703`)
When `WINEVTLOG` uses `raw: true` (XML string in `body.string`), drop Event ID `4703` only for the specific noisy service binaries and hosts:
```text
IsMatch(body.string, "<EventID>4703</EventID>") and IsMatch(body.string, "(?i)(C:\\\\Windows\\\\System32\\\\svchost\\.exe|C:\\\\Program Files\\\\Puppet Labs\\\\Puppet\\\\puppet\\\\bin\\\\ruby\\.exe)")
```

### Recipe 3: Linux Syslog (`NIX_SYSTEM`) — Host-Pinned `multipathd` & `CRON` Chaff
```text
IsMatch(body.string, "multipathd\\[\\d+\\]:\\s+sda:\\s+(failed to get (sgio|sysfs|udev) uid|add missing path)") or IsMatch(body.string, "CRON\\[\\d+\\]:\\s+pam_unix\\(cron:session\\):\\s+session\\s+(opened|closed)\\s+for\\s+user\\s+root")
```

### Recipe 4: Redacting Credentials & Sensitive Tokens Before SecOps Ingestion (`transform:2`)
```text
replace_pattern(body.string, "(?i)(authorization:\\s*bearer\\s+|password=|apikey=|api_key=|secret=)[^&\"'\\s]+", "$1REDACTED") where body.string != nil
```
