# OpenTelemetry Transformation Language (OTTL) Reference

This reference documents the grammar, context paths, operators, Editors, and Converters of the OpenTelemetry Transformation Language (OTTL) as used in OpenTelemetry Collector `transform` and `filter` processors and Bindplane (`transform:2`, `filter-by-condition:3`, `secops_filter:2`).

Sources:
- [OpenTelemetry Collector Contrib `pkg/ottl/README.md`](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/pkg/ottl/README.md)
- [OpenTelemetry Collector Contrib `pkg/ottl/LANGUAGE.md`](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/pkg/ottl/LANGUAGE.md)
- [OpenTelemetry Collector Contrib `pkg/ottl/ottlfuncs/README.md`](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/pkg/ottl/ottlfuncs/README.md)
- [OpenTelemetry Collector Contrib `pkg/ottl/contexts/ottllog/README.md`](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/pkg/ottl/contexts/ottllog/README.md)
- [Bindplane OTTL Guide](https://bindplane.com/blog/what-is-the-opentelemetry-transform-language-ottl)

---

## 1. OTTL Grammar & Syntax Rules

### Statements vs. Conditions
OTTL is used in two distinct forms depending on the processor:
1. **Transform Statement (`transform:2`)**:
   - Invokes an **Editor** function (always lowercase) that mutates the telemetry item, optionally guarded by a `where` boolean clause:
     ```text
     <editor_function>(<arg1>, <arg2>, ...)
     <editor_function>(<arg1>, <arg2>, ...) where <boolean_condition>
     ```
   - Example:
     ```text
     set(attributes["environment"], "prod") where resource.attributes["deployment.environment"] == nil
     ```
2. **Filter Condition (`filter-by-condition:3`, `secops_filter:2`, or `transform:2` `conditions` list)**:
   - A pure **boolean expression** (using comparison operators, `and`/`or`/`not`, and **Converter** functions returning `bool` such as `IsMatch`):
     ```text
     <boolean_condition>
     ```
   - Example:
     ```text
     body["id.resp_p"] == 53 and (body["id.orig_h"] == "10.128.0.2" or IsMatch(body["query"], "\\.internal$"))
     ```

### Literals & Types
- **Strings**: Must be enclosed in **double quotes** (`"..."`). Single quotes (`'...'`) are **syntax errors**. Escape inner double quotes as `\"` and literal backslashes as `\\`.
- **Integers & Floats**: Signed or unsigned base-10 numbers (`42`, `-1`, `3.14159`).
- **Booleans**: `true` or `false` (lowercase).
- **Nil**: `nil` (lowercase). Never use `null`, `NULL`, or `None`.
- **Byte Slices**: Hex literal `0x...` (for example, `0x000102ff`).
- **Lists / Slices**: `[ "a", "b", "c" ]` or `[ 80, 443 ]`.
- **Maps**: `{"key": "value", "count": 1}`.

### Operators
- **Comparison Operators**:
  - `==` (equal)
  - `!=` (not equal)
  - `<` (less than)
  - `<=` (less than or equal)
  - `>` (greater than)
  - `>=` (greater than or equal)
- **Logical (Boolean) Operators**:
  - `and` (conjunction; **never** `&&`)
  - `or` (disjunction; **never** `||`)
  - `not` (negation; **never** `!`)
- **Arithmetic Operators**:
  - `+`, `-`, `*`, `/` (supported on numeric values; `+` also concatenates strings in modern OTTL, or use `Concat([...], "")`).
- **Grouping & Precedence**:
  - Parentheses `(` and `)` control evaluation precedence (`not` binds tightest, then `and`, then `or`). Always wrap `or` clauses in parentheses when combining with `and`.

---

## 2. OTTL Context Paths

Every OTTL expression is evaluated against a **Context**.

### Log Context (`ottllog` — Bindplane `logs_context: "log"`)
| Path | Type | Description |
| :--- | :--- | :--- |
| `body` | `any` (`map`, `slice`, `string`, `int`, `bool`, `bytes`) | The log record body. Can be indexed directly if `body` is a map (`body["field"]`). |
| `body.string` | `string` | String representation of the log body. Safe for string matching when `body` is a raw string. |
| `attributes` | `pcommon.Map` | Log record attributes map. Access keys with `attributes["key"]` or nested `attributes["a"]["b"]`. |
| `resource.attributes` | `pcommon.Map` | Resource-level attributes (e.g., `resource.attributes["host.name"]`, `resource.attributes["service.name"]`). |
| `resource.dropped_attributes_count` | `int` | Count of dropped resource attributes. |
| `instrumentation_scope.name` | `string` | Name of the instrumentation scope. |
| `instrumentation_scope.version` | `string` | Version of the instrumentation scope. |
| `instrumentation_scope.attributes` | `pcommon.Map` | Instrumentation scope attributes. |
| `time` | `time.Time` | Timestamp when the event occurred. |
| `time_unix_nano` | `int` | Event timestamp in nanoseconds since Unix epoch. |
| `observed_time` | `time.Time` | Timestamp when the event was observed by the collector. |
| `observed_time_unix_nano` | `int` | Observed timestamp in nanoseconds since Unix epoch. |
| `severity_number` | `int` (Enum) | Numerical severity (`SEVERITY_NUMBER_TRACE`=1, `SEVERITY_NUMBER_DEBUG`=5, `SEVERITY_NUMBER_INFO`=9, `SEVERITY_NUMBER_WARN`=13, `SEVERITY_NUMBER_ERROR`=17, `SEVERITY_NUMBER_FATAL`=21). |
| `severity_text` | `string` | Text severity level (e.g., `"INFO"`, `"ERROR"`, `"ERR"`). |
| `flags` | `int` | Log trace flags. |
| `trace_id` | `pcommon.TraceID` | Trace ID bytes (`trace_id.string` for hex string). |
| `span_id` | `pcommon.SpanID` | Span ID bytes (`span_id.string` for hex string). |
| `dropped_attributes_count` | `int` | Count of dropped log attributes. |
| `cache` | `pcommon.Map` | Per-item scratchpad map for storing temporary values during statement execution (`cache["temp"]`). Never exported. |

### Resource Context (`ottlresource` — Bindplane `logs_context: "resource"`)
- `attributes` (`pcommon.Map`)
- `dropped_attributes_count` (`int`)
- `cache` (`pcommon.Map`)
*(Note: When `logs_context` is `"log"`, you can still read and mutate `resource.attributes["..."]` directly without switching contexts.)*

### Metric / DataPoint Contexts (`ottlmetric` / `ottldatapoint`)
- **Metric (`metric`)**: `name`, `description`, `unit`, `type`, `aggregation_temporality`, `is_monotonic`, `datapoints`, `resource.attributes`, `instrumentation_scope.attributes`.
- **DataPoint (`datapoint`)**: `attributes`, `time_unix_nano`, `start_time_unix_nano`, `value_int`, `value_double`, `count`, `sum`, ` flags`, `metric.name`, `metric.type`, `resource.attributes`.

### Trace / Span Contexts (`ottlspan` / `ottlspanevent`)
- **Span (`span`)**: `trace_id`, `span_id`, `parent_span_id`, `name`, `kind`, `start_time_unix_nano`, `end_time_unix_nano`, `attributes`, `status.code`, `status.message`, `events`, `links`, `resource.attributes`.
- **SpanEvent (`spanevent`)**: `time_unix_nano`, `name`, `attributes`, `dropped_attributes_count`, `span.name`, `resource.attributes`.

---

## 3. Official OTTL Editors (Lowercase — Transform Statements Only)

Editors modify the telemetry item in-place. They can **only** be called as the top-level function of a transform statement.

| Editor Signature | Description & Example |
| :--- | :--- |
| `set(target, value)` | Sets `target` path to `value`. If `value` is `nil`, does nothing.Creates the key if it does not exist.<br>`set(attributes["env"], "prod") where body["env"] == "production"` |
| `delete_key(targetMap, key)` | Removes `key` (string) from `targetMap`.<br>`delete_key(attributes, "raw_credit_card")` |
| `delete_matching_keys(targetMap, regexPattern)` | Deletes all keys from `targetMap` matching `regexPattern`.<br>`delete_matching_keys(attributes, "^debug_.*")` |
| `keep_keys(targetMap, [keys...])` | Deletes all keys from `targetMap` **except** those listed in the string slice.<br>`keep_keys(attributes, ["host.name", "service.name", "log.file.path"])` |
| `keep_matching_keys(targetMap, regexPattern)` | Keeps only keys in `targetMap` that match `regexPattern`.<br>`keep_matching_keys(attributes, "^(host|service)\\.")` |
| `replace_pattern(target, regexPattern, replacement, [function], [regexPatternArg])` | Replaces all substrings matching `regexPattern` in `target` with `replacement`. Supports `$1` capture groups.<br>`replace_pattern(body.string, "ssn=\\d{3}-\\d{2}-\\d{4}", "ssn=REDACTED")` |
| `replace_match(target, globPattern, replacement)` | If the entire `target` string matches `globPattern` (`*` wildcard), replaces it with `replacement`.<br>`replace_match(attributes["http.target"], "/api/v1/users/*", "/api/v1/users/{id}")` |
| `replace_all_matches(targetMap, globPattern, replacement)` | Replaces any string value in `targetMap` matching `globPattern` with `replacement`.<br>`replace_all_matches(attributes, "*secret*", "REDACTED")` |
| `replace_all_patterns(targetMap, mode, regexPattern, replacement)` | Applies regex replacement across all `"key"` or `"value"` strings in `targetMap`.<br>`replace_all_patterns(attributes, "value", "\\b\\d{16}\\b", "REDACTED_CC")` |
| `merge_maps(targetMap, sourceMap, strategy)` | Merges `sourceMap` into `targetMap`. `strategy` is `"insert"` (do not overwrite existing), `"update"` (only update existing), or `"upsert"` (overwrite and insert).<br>`merge_maps(body, ParseJSON(body.string), "upsert") where IsMatch(body.string, "^\\{")` |
| `flatten(targetMap, [prefix], [resolveConflicts], [depth])` | Flattens nested maps in `targetMap` into dot-separated keys.<br>`flatten(body)` |
| `truncate_all(targetMap, limit)` | Truncates all string values in `targetMap` so none exceed `limit` characters.<br>`truncate_all(attributes, 1024)` |
| `limit(targetMap, limit, [priorityKeys])` | Limits `targetMap` to at most `limit` keys, always preserving `priorityKeys`.<br>`limit(attributes, 50, ["host.name", "service.name"])` |
| `append(targetSlice, [value])` | Appends `value` to an existing slice or creates a single-element slice. |

---

## 4. Official OTTL Converters (PascalCase — Expressions & Filter Conditions)

Converters compute and return a value without directly mutating the target path (unless passed as the second argument of `set(target, Converter(...))`). Boolean Converters (`IsMatch`, `IsMap`, `IsString`, `IsBool`, `IsInt`, `IsDouble`, `IsList`, `HasPrefix`, `HasSuffix`) can be used directly in `where` clauses and filter conditions.

### Boolean & Matching Converters
| Converter Signature | Return Type | Description & Example |
| :--- | :--- | :--- |
| `IsMatch(target, regexPattern)` | `bool` | Returns `true` if `target` matches Go RE2 `regexPattern`. Safely returns `false` if `target` is `nil`.<br>`IsMatch(body.string, "(?i)failed password")` |
| `HasPrefix(target, prefix)` | `bool` | Returns `true` if string `target` starts with `prefix`.<br>`HasPrefix(attributes["log.file.path"], "/var/log/nginx/")` |
| `HasSuffix(target, suffix)` | `bool` | Returns `true` if string `target` ends with `suffix`.<br>`HasSuffix(body["query"], ".local")` |
| `IsMap(target)` / `IsString(target)` / `IsInt(target)` / `IsDouble(target)` / `IsBool(target)` / `IsList(target)` | `bool` | Type-check predicates.<br>`IsMap(body) and body["event_type"] == "dns"` |
| `IsValidLuhn(target)` | `bool` | Returns `true` if `target` string/int passes the Luhn checksum (useful for credit card detection). |
| `IsInCIDR(ipStr, [cidrStrings...])` | `bool` | *(Bindplane/OTTL extension)* Checks if IP belongs to CIDR blocks. When unavailable, use `IsMatch(body["id.orig_h"], "^10\\.")`. |

### String & Regex Extraction Converters
| Converter Signature | Return Type | Description & Example |
| :--- | :--- | :--- |
| `Concat([strings...], delimiter)` | `string` | Joins a slice of strings/values using `delimiter`.<br>`set(attributes["full_addr"], Concat([body["id.orig_h"], body["id.orig_p"]], ":"))` |
| `Split(target, delimiter)` | `[]string` | Splits `target` string by `delimiter`.<br>`set(attributes["path_parts"], Split(attributes["url.path"], "/"))` |
| `Substring(target, start, length)` | `string` | Extracts a substring starting at `start` of `length` characters.<br>`set(body.string, Substring(body.string, 0, 4096)) where Len(body.string) > 4096` |
| `ConvertCase(target, toCase)` | `string` | Converts string case. `toCase` is `"lower"`, `"upper"`, `"snake"`, or `"camel"`.<br>`set(attributes["action"], ConvertCase(body["action"], "lower"))` |
| `Trim(target, [trimSet])` | `string` | Trims leading and trailing whitespace (or characters in `trimSet`). |
| `ExtractPatterns(target, regexPattern)` | `pcommon.Map` | Extracts named capture groups `(?P<name>...)` into a map.<br>`merge_maps(attributes, ExtractPatterns(body.string, "user=(?P<user>\\S+)\\s+src=(?P<src_ip>\\S+)"), "upsert")` |
| `ExtractGrokPatterns(target, grokPattern, [namedOnly])` | `pcommon.Map` | Extracts fields using Grok patterns.<br>`merge_maps(attributes, ExtractGrokPatterns(body.string, "%{COMMONAPACHELOG}", true), "upsert")` |
| `RegexExtract(target, regexPattern, [submatchIdx])` | `string` | *(Bindplane/SecOps helper where supported; in standard OTTL prefer `ExtractPatterns`)* |
| `Len(target)` | `int` | Returns the length of a string, slice, or map.<br>`Len(body.string) > 10000` |

### Parsing & Serialization Converters
| Converter Signature | Return Type | Description & Example |
| :--- | :--- | :--- |
| `ParseJSON(target)` | `pcommon.Map` | Parses a JSON string into a map.<br>`set(body, ParseJSON(body.string)) where IsString(body) and HasPrefix(body.string, "{")` |
| `ParseKeyValue(target, [delimiter], [pairDelimiter])` | `pcommon.Map` | Parses `k1=v1 k2=v2` strings into a map.<br>`merge_maps(attributes, ParseKeyValue(body.string, "=", " "), "upsert")` |
| `ParseXML(target)` / `ParseSimplifiedXML(target)` | `pcommon.Map` | Parses XML strings (such as Windows Event Log XML) into a map. |
| `ParseCSV(target, header, [delimiter], ...)` | `pcommon.Map` | Parses a CSV row into a map keyed by `header`. |
| `Format(formatStr, [args...])` | `string` | Formats values using Go `fmt.Sprintf` verbs (`"%s:%d"`). |

### Type Conversion & Hashing Converters
| Converter Signature | Return Type | Description & Example |
| :--- | :--- | :--- |
| `Int(target)` / `Double(target)` / `String(target)` / `Bool(target)` | `int` / `float` / `string` / `bool` | Converts scalar values between types.<br>`Int(body["status_code"]) >= 500` |
| `SHA256(target)` / `SHA1(target)` / `MD5(target)` / `FNV(target)` | `string` | Computes cryptographic or non-cryptographic hex digest of `target` string/bytes.<br>`set(attributes["user.hash"], SHA256(body["username"]))` |
| `Base64Decode(target)` | `string` | Decodes a Base64-encoded string. |
| `UUID()` | `string` | Generates a random v4 UUID string. |

### Time Converters
| Converter Signature | Return Type | Description & Example |
| :--- | :--- | :--- |
| `Now()` | `time.Time` | Returns the current UTC timestamp. |
| `Time(timestampStr, formatStr, [location])` | `time.Time` | Parses a timestamp string using strptime-style layout tokens (`"%Y-%m-%dT%H:%M:%S.%fZ"`).<br>`set(time, Time(body["timestamp"], "%Y-%m-%dT%H:%M:%SZ"))` |
| `UnixSeconds(timeVal)` / `UnixMilli(timeVal)` / `UnixMicro(timeVal)` / `UnixNano(timeVal)` | `int` | Converts a `time.Time` or duration to integer epoch units. |
| `Duration(durationStr)` | `time.Duration` | Parses a Go duration string (`"5m"`, `"24h"`, `"500ms"`). |
