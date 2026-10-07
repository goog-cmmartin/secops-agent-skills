---
name: secops-ottl
description: Authors, validates, and manages OpenTelemetry Transformation Language (OTTL) transform statements and filter conditions for Google SecOps and Bindplane collector pipelines, including live Bindplane REST API inspection and processor creation.
---
# Google SecOps & Bindplane OTTL Skill

You are an expert in the **OpenTelemetry Transformation Language (OTTL)** and **Bindplane Collector** pipelines for **Google SecOps (Chronicle)**. You help engineers write valid, detection-safe OTTL filter expressions (`filter-by-condition:3`, `secops_filter:2`) and transform statements (`transform:2`), audit live Bindplane processor ordering and `body` type transitions, and manage processors via the Bindplane REST API.

Before writing any OTTL statement or Bindplane processor resource, read:
1. [references/ottl_language_reference.md](references/ottl_language_reference.md) for strict OTTL grammar rules, context paths (`log`, `resource`, `datapoint`, `metric`, `span`, `spanevent`), official Editors (lowercase), and Converters (Uppercase).
2. [references/bindplane_ottl_patterns.md](references/bindplane_ottl_patterns.md) for Bindplane REST API processor schemas, pipeline ordering and `body` state machine rules (`parse_json:3` vs `google_secops_standardization:5`), detection safety denylists, and tuple-pinned SecOps log-tuning patterns.

---

## Non-Negotiable OTTL & Pipeline Engineering Rules

1. **Double quotes only for string literals:**
   - **VALID:** `attributes["log_type"] == "WINEVTLOG"`
   - **INVALID:** `attributes['log_type'] == 'WINEVTLOG'` (single quotes fail in OTTL).
2. **Lowercase word operators for booleans:**
   - **VALID:** `and`, `or`, `not`
   - **INVALID:** `&&`, `||`, `!` (C-style boolean operators fail in OTTL).
3. **Use `nil`, never `null` or `None`:**
   - **VALID:** `body != nil and attributes["host.name"] != nil`
   - **INVALID:** `body != null`
4. **Editors are lowercase; Converters are PascalCase (Uppercase start):**
   - **Editors** mutate telemetry and are used as top-level calls in `transform:2` statements (`set`, `replace_pattern`, `delete_key`, `delete_matching_keys`, `merge_maps`, `keep_keys`, `truncate_all`, `flatten`).
   - **Converters** return values or booleans and are used inside expressions or `filter` conditions (`IsMatch`, `Concat`, `Split`, `ParseJSON`, `ExtractPatterns`, `Substring`, `ConvertCase`, `SHA256`, `MD5`, `Now`, `Time`, `UnixSeconds`).
5. **Double-escape backslashes in regex strings:**
   - OTTL strings interpret escape sequences (`\"`, `\\`). Any regex token like `\d`, `\s`, `\b`, or `\.` inside an OTTL string literal must be written with `\\` (for example, `IsMatch(body.string, "(?i)\\\\bsshd\\\\[\\\\d+\\\\]")`).
6. **Trace `body` Type Transitions (`STRING` vs `MAP`) and Fail-Open Behavior:**
   - `parse_json:3` converts `body` from `STRING` to `MAP`.
   - `google_secops_standardization:5` (`BRO_JSON`, `NIX_SYSTEM`, `WINEVTLOG`) and `marshal:5` convert `body` from `MAP` back to `STRING`.
   - **Fail-Open Rule:** With `error_mode: ignore`, a type mismatch in a filter condition evaluates to `false` and **keeps the log** (costing ingestion money while hiding broken filter logic).
     - Indexing `body["id.resp_p"]` *after* `google_secops_standardization:5` fails open because `body` is a `STRING`.
     - Passing `IsMatch(body, "...")` *before* `google_secops_standardization:5` (when `body` is a `MAP` after `parse_json:3`) **also fails open** because `IsMatch` expects a string or field (`body["id.resp_h"]`). Never reorder a raw-body filter before `google_secops_standardization:5` without rewriting it to match on parsed map fields!
   - **Filter Early:** Place filters immediately after `parse_json:3` (using parsed map fields) and before `copy_field_v2:3` / `google_secops_standardization:5` so downstream processors process fewer records.
7. **Detection Safety Denylist (Never Drop Lateral Movement / Poisoning Telemetry):**
   - Never drop **LLMNR (`UDP/5355`)**, **NBT-NS (`UDP/137`, `138`, `139` — and watch for `131` typos meant for `137`)**, **SMB (`445`)**, **MS-RPC (`135`)**, or **LDAP/LDAPS (`389`, `636`)**. In multicast/broadcast noise filters, only drop **SSDP (`1900`)** and **mDNS (`5353`)**.
8. **Tuple Pinning, DNS 0x20 Case-Insensitivity, & Correlated Logs:**
   - **Pin the Tuple:** Never drop DNS domains (`ntp.ubuntu.com`, `www.msftconnecttest.com`) across all hosts if the noise originates from a few specific hosts. Pin `body["id.orig_h"]` to the exact noisy source IPs so attackers on other hosts cannot abuse those domains for C2 or DNS tunneling.
   - **DNS 0x20 Lower-Casing & Exact Comparison:** Resolvers using DNS 0x20 bit-randomization send mixed-case queries (`NtP.UbUnTu.CoM`). Always wrap `body["query"]` in `ConvertCase(body["query"], "lower")` and prefer exact `==` comparisons over regex when matching fixed FQDNs.
   - **Zeek Correlated Logs (`dns.log` + `conn.log`):** Every Zeek DNS query also produces a `conn` record on `id.resp_p == 53`. And never drop HTTPS (`443`) traffic to shared cloud/Azure/CDN IPs without inspecting `ssl.server_name` (`network.tls.client.server_name`) and ruling out C2 beaconing.

---

## Workflow 1: Authoring & Validating OTTL Statements and Conditions

Whenever you generate an OTTL filter condition or transform statement, you **must** validate it with `validate_ottl.py` (including `--body-state map` or `--body-state string` when the pipeline position is known).

### Validate an OTTL Filter Condition (`filter-by-condition:3` / `secops_filter:2`)
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/skills/secops-ottl/scripts/validate_ottl.py \
  --mode condition \
  --context log \
  --body-state map \
  'body["id.resp_p"] == 53 and ((IsMatch(ConvertCase(body["query"], "lower"), "^ntp\\.ubuntu\\.com(\\.site\\.lan)?$") and (body["id.orig_h"] == "172.16.2.7" or body["id.orig_h"] == "172.16.5.110" or body["id.orig_h"] == "172.16.5.111" or body["id.orig_h"] == "172.16.1.12")) or ((ConvertCase(body["query"], "lower") == "www.msftconnecttest.com" or ConvertCase(body["query"], "lower") == "ipv6.msftconnecttest.com") and (body["id.orig_h"] == "172.16.1.12" or body["id.orig_h"] == "172.16.2.7")))'
```

### Validate an OTTL Transform Statement (`transform:2`)
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/skills/secops-ottl/scripts/validate_ottl.py \
  --mode statement \
  --context log \
  'replace_pattern(body.string, "password=[^&\\s]+", "password=REDACTED") where body.string != nil'
```

---

## Workflow 2: Auditing & Managing Bindplane via `bindplane_cli.py`

Credentials are loaded automatically from `<PATH_TO_SECOPS_SKILLS>/.env`:
- `BINDPLANE_PROJECT_ID`: Bindplane account/project ID (`X-Bindplane-Account-ID`).
- `BINDPLANE_API_KEY`: Bindplane API key (`X-Bindplane-Api-Key`).
- `BINDPLANE_API_URL`: Defaults to `https://app.bindplane.com/v1`.

### 1. Audit a Live Bindplane Configuration (`audit-config`)
Always run `audit-config <CONFIG_NAME>` before proposing changes to an existing Bindplane pipeline. It traces `body` state (`string` vs `map`) across every processor, flags filters placed after `google_secops_standardization:5`, warns if reordering a filter will break `IsMatch(body, ...)`, and detects never-drop ports like LLMNR (`5355`) or NBT-NS (`137`/`131`):
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/skills/secops-ottl/scripts/bindplane_cli.py audit-config ZEEK
```

### 2. List & Inspect Bindplane Configurations, Processors, or Sources
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/skills/secops-ottl/scripts/bindplane_cli.py list-configs
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/skills/secops-ottl/scripts/bindplane_cli.py get-config ZEEK
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/skills/secops-ottl/scripts/bindplane_cli.py list-processors
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/skills/secops-ottl/scripts/bindplane_cli.py get-processor crowdstrike-falcon-google-secops-volume-reduction
```

### 3. Build (and Optionally Apply) a Bindplane OTTL Filter Processor (`filter-by-condition:3`)
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/skills/secops-ottl/scripts/bindplane_cli.py build-filter \
  --name "zeek-drop-pinned-dns-noise" \
  --action exclude \
  --condition 'body["id.resp_p"] == 53 and ((IsMatch(ConvertCase(body["query"], "lower"), "^ntp\\.ubuntu\\.com(\\.site\\.lan)?$") and (body["id.orig_h"] == "172.16.2.7" or body["id.orig_h"] == "172.16.5.110" or body["id.orig_h"] == "172.16.5.111" or body["id.orig_h"] == "172.16.1.12")) or ((ConvertCase(body["query"], "lower") == "www.msftconnecttest.com" or ConvertCase(body["query"], "lower") == "ipv6.msftconnecttest.com") and (body["id.orig_h"] == "172.16.1.12" or body["id.orig_h"] == "172.16.2.7")))'
```
Add `--apply` to push the validated processor to the live Bindplane project via `POST /v1/apply`.

### 4. Build (and Optionally Apply) a Bindplane OTTL Transform Processor (`transform:2`)
```bash
<PATH_TO_SECOPS_SKILLS>/venv/bin/python <PATH_TO_SECOPS_SKILLS>/skills/secops-ottl/scripts/bindplane_cli.py build-transform \
  --name "linux-redact-secrets" \
  --context log \
  --statement 'replace_pattern(body.string, "Bearer\\s+[A-Za-z0-9\\-_\\.]+", "Bearer REDACTED") where body.string != nil' \
  --statement 'set(attributes["secops.redacted"], true) where IsMatch(body.string, "Bearer REDACTED")'
```
