#!/usr/bin/env python3
"""Local validator for OpenTelemetry Transformation Language (OTTL) statements and conditions.

Validates:
1. Quote syntax (double quotes only; rejects single-quoted literals outside double quotes).
2. Balanced parentheses `()`, brackets `[]`, braces `{}`, and double quotes `""`.
3. Logical and comparison operators (`and`, `or`, `not`, `==`, `!=`, `<`, `<=`, `>`, `>=`;
   rejects `&&`, `||`, `!`, single `=`).
4. Null literal syntax (`nil` only; rejects `null`, `NULL`, `None`).
5. Statement vs. Condition mode:
   - `statement`: Must start with a known lowercase Editor (`set`, `replace_pattern`, etc.)
     and optionally have a valid `where <condition>` clause.
   - `condition`: Must be a boolean expression; rejects top-level Editor calls.
6. Function names against official OTTL & Bindplane Editors (lowercase) and Converters (PascalCase).
7. Context path roots (`log`, `resource`, `datapoint`, `metric`, `span`, `spanevent`).
8. Regular expression arguments inside `IsMatch`, `replace_pattern`, `replace_all_patterns`,
   `delete_matching_keys`, `keep_matching_keys`, `ExtractPatterns`, `RegexExtract`.
"""

import argparse
import json
import re
import sys
from typing import Dict, List, Optional, Tuple

KNOWN_EDITORS = {
    "append",
    "convert_gauge_to_sum",
    "convert_sum_to_gauge",
    "convert_summary_count_val_to_sum",
    "convert_summary_quantile_val_to_gauge",
    "convert_summary_sum_val_to_sum",
    "copy_metric",
    "delete_index",
    "delete_key",
    "delete_matching_keys",
    "extract_count_metric",
    "extract_sum_metric",
    "flatten",
    "keep_keys",
    "keep_matching_keys",
    "limit",
    "merge_histogram_buckets",
    "merge_maps",
    "replace_all_matches",
    "replace_all_patterns",
    "replace_match",
    "replace_pattern",
    "scale_metric",
    "set",
    "set_semconv_span_name",
    "truncate_all",
    "truncate_time",
}

KNOWN_CONVERTERS = {
    "Append",
    "Base64Decode",
    "Bool",
    "CommunityID",
    "Concat",
    "ConvertAttributesToElementsXML",
    "ConvertCase",
    "ConvertTextToElementsXML",
    "Day",
    "Decode",
    "DeleteKey",
    "Double",
    "Duration",
    "ExtractGrokPatterns",
    "ExtractPatterns",
    "FNV",
    "Format",
    "GetXML",
    "HasPrefix",
    "HasSuffix",
    "Hex",
    "Hour",
    "Hours",
    "InsertXML",
    "Int",
    "IsBool",
    "IsDouble",
    "IsInt",
    "IsInCIDR",
    "IsList",
    "IsMap",
    "IsMatch",
    "IsString",
    "IsValidLuhn",
    "Len",
    "Log",
    "MD5",
    "Microseconds",
    "Milliseconds",
    "Minute",
    "Minutes",
    "Month",
    "Murmur3Hash",
    "Murmur3Hash128",
    "Nanoseconds",
    "Now",
    "ParseCSV",
    "ParseInt",
    "ParseJSON",
    "ParseKeyValue",
    "ParseSeverity",
    "ParseSimplifiedXML",
    "ParseCEF",
    "ParseLEEF",
    "ParseXML",
    "RegexExtract",
    "RemoveXML",
    "ReplaceMatch",
    "ReplacePattern",
    "SHA1",
    "SHA256",
    "SHA512",
    "Second",
    "Seconds",
    "SliceToMap",
    "Sort",
    "SpanID",
    "Split",
    "String",
    "Substring",
    "Time",
    "ToKeyValueString",
    "TraceID",
    "Trim",
    "TruncateTime",
    "UUID",
    "Unix",
    "UnixMicro",
    "UnixMilli",
    "UnixNano",
    "UnixSeconds",
    "Url",
    "UserAgent",
    "Weekday",
    "Year",
}

CONTEXT_PATHS = {
    "log": {
        "body",
        "attributes",
        "resource",
        "instrumentation_scope",
        "time",
        "time_unix_nano",
        "observed_time",
        "observed_time_unix_nano",
        "severity_number",
        "severity_text",
        "flags",
        "trace_id",
        "span_id",
        "dropped_attributes_count",
        "cache",
        "log",
    },
    "resource": {
        "attributes",
        "dropped_attributes_count",
        "cache",
        "resource",
    },
    "datapoint": {
        "attributes",
        "time",
        "time_unix_nano",
        "start_time",
        "start_time_unix_nano",
        "value_int",
        "value_double",
        "count",
        "sum",
        "bucket_counts",
        "explicit_bounds",
        "exemplars",
        "flags",
        "min",
        "max",
        "metric",
        "resource",
        "instrumentation_scope",
        "cache",
        "datapoint",
    },
    "metric": {
        "name",
        "description",
        "unit",
        "type",
        "aggregation_temporality",
        "is_monotonic",
        "datapoints",
        "resource",
        "instrumentation_scope",
        "cache",
        "metric",
    },
    "span": {
        "trace_id",
        "span_id",
        "trace_state",
        "parent_span_id",
        "name",
        "kind",
        "start_time",
        "start_time_unix_nano",
        "end_time",
        "end_time_unix_nano",
        "attributes",
        "dropped_attributes_count",
        "events",
        "dropped_events_count",
        "links",
        "dropped_links_count",
        "status",
        "resource",
        "instrumentation_scope",
        "cache",
        "span",
    },
    "spanevent": {
        "time",
        "time_unix_nano",
        "name",
        "attributes",
        "dropped_attributes_count",
        "span",
        "resource",
        "instrumentation_scope",
        "cache",
        "spanevent",
    },
}

RESERVED_KEYWORDS = {
    "and",
    "or",
    "not",
    "where",
    "true",
    "false",
    "nil",
}

SEVERITY_ENUMS = {
    "SEVERITY_NUMBER_UNSPECIFIED",
    "SEVERITY_NUMBER_TRACE",
    "SEVERITY_NUMBER_TRACE2",
    "SEVERITY_NUMBER_TRACE3",
    "SEVERITY_NUMBER_TRACE4",
    "SEVERITY_NUMBER_DEBUG",
    "SEVERITY_NUMBER_DEBUG2",
    "SEVERITY_NUMBER_DEBUG3",
    "SEVERITY_NUMBER_DEBUG4",
    "SEVERITY_NUMBER_INFO",
    "SEVERITY_NUMBER_INFO2",
    "SEVERITY_NUMBER_INFO3",
    "SEVERITY_NUMBER_INFO4",
    "SEVERITY_NUMBER_WARN",
    "SEVERITY_NUMBER_WARN2",
    "SEVERITY_NUMBER_WARN3",
    "SEVERITY_NUMBER_WARN4",
    "SEVERITY_NUMBER_ERROR",
    "SEVERITY_NUMBER_ERROR2",
    "SEVERITY_NUMBER_ERROR3",
    "SEVERITY_NUMBER_ERROR4",
    "SEVERITY_NUMBER_FATAL",
    "SEVERITY_NUMBER_FATAL2",
    "SEVERITY_NUMBER_FATAL3",
    "SEVERITY_NUMBER_FATAL4",
}

VALID_STRING_ESCAPES = {'"', "\\", "n", "r", "t"}


def strip_strings_and_collect_literals(
    expr: str,
) -> Tuple[str, List[Tuple[int, str]], List[str], List[str]]:
    """Replaces double-quoted literals with placeholders and validates string escapes/quotes."""
    errors: List[str] = []
    warnings: List[str] = []
    literals: List[Tuple[int, str]] = []
    out_chars: List[str] = []

    in_double = False
    i = 0
    n = len(expr)
    current_lit: List[str] = []
    lit_start = 0

    while i < n:
        ch = expr[i]
        if not in_double:
            if ch == '"':
                in_double = True
                lit_start = i
                current_lit = []
                out_chars.append(f"__STR_{len(literals)}__")
            elif ch == "'":
                errors.append(
                    f"Single quote found at position {i}. OTTL requires double quotes (\"...\") for all string literals and map keys."
                )
                out_chars.append(ch)
            else:
                out_chars.append(ch)
            i += 1
        else:
            if ch == "\\":
                if i + 1 >= n:
                    errors.append(
                        f"Trailing backslash at end of string starting at position {lit_start}."
                    )
                    i += 1
                else:
                    next_ch = expr[i + 1]
                    if next_ch not in VALID_STRING_ESCAPES:
                        warnings.append(
                            f"Unescaped backslash sequence '\\{next_ch}' inside string literal at position {i}. "
                            f"In OTTL strings, regex escapes must be double-escaped as '\\\\{next_ch}'."
                        )
                    current_lit.append(ch)
                    current_lit.append(next_ch)
                    i += 2
            elif ch == '"':
                in_double = False
                literals.append((lit_start, "".join(current_lit)))
                i += 1
            else:
                current_lit.append(ch)
                i += 1

    if in_double:
        errors.append(f"Unclosed double quote starting at position {lit_start}.")

    return "".join(out_chars), literals, errors, warnings


def check_balanced_delimiters(stripped: str) -> List[str]:
    """Checks balanced (), [], and {} outside string literals."""
    errors: List[str] = []
    stack: List[Tuple[str, int]] = []
    pairs = {")": "(", "]": "[", "}": "{"}
    for idx, ch in enumerate(stripped):
        if ch in "([{":
            stack.append((ch, idx))
        elif ch in ")]}":
            if not stack:
                errors.append(f"Unmatched closing '{ch}' at position {idx}.")
            else:
                top_ch, top_idx = stack.pop()
                if pairs[ch] != top_ch:
                    errors.append(
                        f"Mismatched delimiter '{top_ch}' (at {top_idx}) closed by '{ch}' (at {idx})."
                    )
    for top_ch, top_idx in stack:
        errors.append(f"Unclosed delimiter '{top_ch}' opened at position {top_idx}.")
    return errors


def check_forbidden_operators_and_tokens(stripped: str) -> List[str]:
    """Checks for C-style operators (&&, ||, !), single '=', and null/None."""
    errors: List[str] = []
    if "&&" in stripped:
        errors.append("Invalid operator '&&'. Use lowercase 'and' in OTTL.")
    if "||" in stripped:
        errors.append("Invalid operator '||'. Use lowercase 'or' in OTTL.")
    if re.search(r"!(?!=)", stripped):
        errors.append("Invalid operator '!'. Use lowercase 'not' or '!=' in OTTL.")
    if re.search(r"(?<![=!<>])=(?!=)", stripped):
        errors.append(
            "Invalid single '=' operator. Use '==' for equality comparisons or 'set(target, value)' for assignment."
        )
    for bad_null in ("null", "NULL", "None", "NIL"):
        if re.search(rf"\b{bad_null}\b", stripped):
            errors.append(f"Invalid null literal '{bad_null}'. Use lowercase 'nil' in OTTL.")
    for bad_bool in ("True", "TRUE", "False", "FALSE", "AND", "OR", "NOT", "WHERE"):
        if re.search(rf"\b{bad_bool}\b", stripped):
            errors.append(
                f"Invalid uppercase keyword '{bad_bool}'. OTTL keywords ('and', 'or', 'not', 'where', 'true', 'false', 'nil') must be lowercase."
            )
    return errors


def validate_regex_literals(
    stripped: str, literals: List[Tuple[int, str]]
) -> List[str]:
    """Compiles regex patterns passed to OTTL regex functions."""
    errors: List[str] = []
    # Match function calls where the 2nd argument is a regex literal:
    # IsMatch(target, __STR_N__), replace_pattern(target, __STR_N__, ...),
    # delete_matching_keys(target, __STR_N__), keep_matching_keys(target, __STR_N__),
    # ExtractPatterns(target, __STR_N__), RegexExtract(target, __STR_N__)
    regex_fn_2nd_arg = re.finditer(
        r"\b(IsMatch|replace_pattern|delete_matching_keys|keep_matching_keys|ExtractPatterns|RegexExtract)\s*\([^,]+,\s*__STR_(\d+)__",
        stripped,
    )
    for match in regex_fn_2nd_arg:
        fn_name = match.group(1)
        lit_idx = int(match.group(2))
        if 0 <= lit_idx < len(literals):
            raw_lit = literals[lit_idx][1]
            # Unescape OTTL string layer (\\ -> \, \" -> ")
            unescaped = (
                raw_lit.replace("\\\\", "\\")
                .replace('\\"', '"')
                .replace("\\n", "\n")
                .replace("\\r", "\r")
                .replace("\\t", "\t")
            )
            try:
                re.compile(unescaped)
            except re.error as exc:
                errors.append(
                    f"Invalid regular expression in {fn_name}(..., \"{raw_lit}\"): {exc}"
                )
    return errors


def validate_functions_and_paths(
    stripped: str, mode: str, context: str
) -> Tuple[List[str], List[str]]:
    """Validates function names (Editors vs Converters) and context paths."""
    errors: List[str] = []
    warnings: List[str] = []

    # Find all function calls: identifier followed by '('
    fn_matches = list(re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", stripped))
    for idx, match in enumerate(fn_matches):
        fn_name = match.group(1)
        if fn_name in RESERVED_KEYWORDS:
            continue
        if fn_name in KNOWN_EDITORS:
            if mode == "condition":
                errors.append(
                    f"Editor '{fn_name}()' cannot be used inside a filter condition. "
                    f"Filter conditions must be pure boolean expressions (use Converters like IsMatch instead)."
                )
            elif idx > 0 and match.start() > 0:
                errors.append(
                    f"Editor '{fn_name}()' can only be called as the top-level statement, not nested inside another expression."
                )
        elif fn_name in KNOWN_CONVERTERS:
            if mode == "statement" and idx == 0 and match.start() == len(stripped) - len(stripped.lstrip()):
                errors.append(
                    f"Converter '{fn_name}()' cannot be used as a standalone transform statement. "
                    f"Wrap it in an Editor such as 'set(target, {fn_name}(...))' or use '--mode condition' for filters."
                )
        else:
            # Check case-insensitive match to give a helpful suggestion
            lower_map = {k.lower(): k for k in KNOWN_EDITORS | KNOWN_CONVERTERS}
            suggestion = lower_map.get(fn_name.lower())
            if suggestion:
                errors.append(
                    f"Unknown function '{fn_name}()'. Did you mean '{suggestion}()'? "
                    f"(Remember: Editors are lowercase, Converters are PascalCase)."
                )
            else:
                errors.append(
                    f"Unknown OTTL function '{fn_name}()'. Check references/ottl_language_reference.md for supported Editors and Converters."
                )

    # Mode-specific top-level checks
    clean_stripped = stripped.strip()
    if mode == "statement":
        top_fn_match = re.match(r"^([a-z_][a-z0-9_]*)\s*\(", clean_stripped)
        if not top_fn_match:
            errors.append(
                "Transform statement must begin with a lowercase Editor function call (e.g., 'set(...)', 'replace_pattern(...)', 'delete_key(...)')."
            )
    elif mode == "condition":
        if re.search(r"\bwhere\b", clean_stripped):
            errors.append(
                "Filter conditions cannot contain a 'where' clause. Write the boolean condition directly."
            )

    # Validate path roots
    valid_roots = CONTEXT_PATHS.get(context, CONTEXT_PATHS["log"])
    # Remove function names and __STR_N__ placeholders before checking identifiers
    no_Strings = re.sub(r"__STR_\d+__", '""', clean_stripped)
    for token_match in re.finditer(
        r"(?<![.\w])([A-Za-z_][A-Za-z0-9_]*)(?:\s*(\(|\.|\[))?", no_Strings
    ):
        ident = token_match.group(1)
        next_sym = token_match.group(2)
        if (
            ident in RESERVED_KEYWORDS
            or ident in SEVERITY_ENUMS
            or ident.startswith("0x")
        ):
            continue
        if next_sym == "(":
            continue
        if ident not in valid_roots:
            errors.append(
                f"Unknown context path root '{ident}' for context '{context}'. "
                f"Valid roots for '{context}' are: {', '.join(sorted(valid_roots))}."
            )

    return errors, warnings


NEVER_DROP_PORTS = {
    135: "MS-RPC (lateral movement / DCOM / WMI)",
    137: "NBT-NS (NetBIOS Name Service — critical for Responder/Inveigh poisoning detection)",
    138: "NetBIOS Datagram Service",
    139: "NetBIOS Session Service (SMB over NetBIOS)",
    389: "LDAP (Active Directory reconnaissance / BloodHound)",
    445: "SMB (lateral movement / PsExec / file shares)",
    636: "LDAPS (Active Directory reconnaissance)",
    5355: "LLMNR (Link-Local Multicast Name Resolution — critical for Responder/Inveigh poisoning detection; keep only 1900 SSDP and 5353 mDNS in multicast drop lists)",
}

TYPO_PORT_WARNINGS = {
    131: "Port 131 is unassigned/obscure and is frequently a typo for 137 (NBT-NS). Neither 131 nor 137 should be dropped.",
}


def check_detection_and_pipeline_safety(
    expr: str,
    stripped: str,
    literals: List[Tuple[int, str]],
    mode: str,
    body_state: str = "any",
) -> Tuple[List[str], List[str]]:
    """Checks for detection blind spots, body STRING vs MAP mismatches, DNS 0x20 casing, and unpinned filters."""
    errors: List[str] = []
    warnings: List[str] = []

    # 1. Body state checks (MAP vs STRING)
    uses_body_map = bool(re.search(r'\bbody\s*\[', stripped))
    uses_body_as_raw_scalar = bool(
        re.search(r'\b(IsMatch|replace_pattern|HasPrefix|HasSuffix|Concat|Split)\s*\(\s*body\s*,', stripped)
    )
    if body_state == "string" and uses_body_map:
        errors.append(
            "Pipeline type mismatch: expression indexes 'body[...]' as a MAP, but 'body' is currently a STRING at this point in the pipeline "
            "(e.g., after 'google_secops_standardization' or before 'parse_json'). With 'error_mode: ignore', this fails open and drops nothing."
        )
    if body_state == "map" and uses_body_as_raw_scalar:
        errors.append(
            "Pipeline type mismatch: expression passes 'body' directly to a string function (e.g., 'IsMatch(body, ...)'), "
            "but 'body' is a parsed MAP at this point in the pipeline (after 'parse_json' and before 'google_secops_standardization'). "
            "With 'error_mode: ignore', this fails open and drops nothing. Match on specific parsed fields such as 'body[\"id.resp_h\"]' instead."
        )

    if mode != "condition":
        return errors, warnings

    # 2. Check for never-drop ports (LLMNR 5355, NBT-NS 137, SMB 445, etc.)
    for port_match in re.finditer(
        r'\b(?:id\.resp_p|id\.orig_p|port|dst_port|target\.port|__STR_\d+__)\b[^\n;]*?==\s*(\d+)',
        stripped,
    ):
        port_num = int(port_match.group(1))
        if port_num in NEVER_DROP_PORTS:
            warnings.append(
                f"DETECTION BLIND SPOT: Condition matches port {port_num} ({NEVER_DROP_PORTS[port_num]}). "
                f"Never drop port {port_num} in SecOps collector filters."
            )
        elif port_num in TYPO_PORT_WARNINGS:
            warnings.append(
                f"SUSPICIOUS PORT {port_num}: {TYPO_PORT_WARNINGS[port_num]}"
            )

    # Also check raw expr for body["id.resp_p"] == <port>
    for port_match in re.finditer(
        r'body\[\s*"(?:id\.resp_p|id\.orig_p|dst_port|src_port|port)"\s*\]\s*==\s*(\d+)',
        expr,
    ):
        port_num = int(port_match.group(1))
        msg_never = (
            f"DETECTION BLIND SPOT: Condition matches port {port_num} ({NEVER_DROP_PORTS.get(port_num, '')}). "
            f"Never drop port {port_num} in SecOps collector filters."
        )
        msg_typo = f"SUSPICIOUS PORT {port_num}: {TYPO_PORT_WARNINGS.get(port_num, '')}"
        if port_num in NEVER_DROP_PORTS and msg_never not in warnings:
            warnings.append(msg_never)
        elif port_num in TYPO_PORT_WARNINGS and msg_typo not in warnings:
            warnings.append(msg_typo)

    # 3. Check DNS query case-sensitivity (0x20 bit randomization)
    if re.search(r'body\[\s*"query"\s*\]', expr) and not re.search(
        r'ConvertCase\s*\(\s*body\[\s*"query"\s*\]\s*,\s*"lower"\s*\)', expr
    ):
        warnings.append(
            "DNS 0x20 CASE SENSITIVITY: 'body[\"query\"]' is compared without 'ConvertCase(body[\"query\"], \"lower\")'. "
            "Resolvers using DNS 0x20 bit-randomization send mixed-case queries (e.g., 'NtP.UbUnTu.CoM') that bypass case-sensitive filters."
        )

    # 4. Check tuple pinning when filtering DNS queries or specific ports
    if re.search(r'body\[\s*"query"\s*\]', expr) and not re.search(
        r'body\[\s*"id\.orig_h"\s*\]|attributes\[\s*"host\.name"\s*\]|resource\.attributes\[\s*"host\.name"\s*\]',
        expr,
    ):
        warnings.append(
            "UNPINNED FILTER: DNS query filter does not pin source host/IP ('body[\"id.orig_h\"]' or 'resource.attributes[\"host.name\"]'). "
            "Dropping domain names across all hosts creates a fleet-wide C2/tunneling blind spot; pin the filter to the specific noisy source IPs/hosts."
        )

    return errors, warnings


def validate_ottl_expression(
    expr: str,
    mode: str = "condition",
    context: str = "log",
    body_state: str = "any",
) -> Dict[str, object]:
    """Validates a single OTTL expression and returns a structured result dict."""
    expr_trimmed = expr.strip()
    if not expr_trimmed:
        return {
            "expression": expr,
            "mode": mode,
            "context": context,
            "body_state": body_state,
            "valid": False,
            "errors": ["Empty OTTL expression."],
            "warnings": [],
        }

    stripped, literals, str_errors, str_warnings = strip_strings_and_collect_literals(
        expr_trimmed
    )
    delim_errors = check_balanced_delimiters(stripped)
    op_errors = check_forbidden_operators_and_tokens(stripped)
    fn_errors, fn_warnings = validate_functions_and_paths(stripped, mode, context)
    regex_errors = validate_regex_literals(stripped, literals)
    safety_errors, safety_warnings = check_detection_and_pipeline_safety(
        expr_trimmed, stripped, literals, mode, body_state=body_state
    )

    all_errors = (
        str_errors + delim_errors + op_errors + fn_errors + regex_errors + safety_errors
    )
    all_warnings = str_warnings + fn_warnings + safety_warnings

    return {
        "expression": expr_trimmed,
        "mode": mode,
        "context": context,
        "body_state": body_state,
        "valid": len(all_errors) == 0,
        "errors": all_errors,
        "warnings": all_warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate OTTL filter conditions and transform statements."
    )
    parser.add_argument(
        "expressions",
        nargs="*",
        help="One or more OTTL expressions to validate.",
    )
    parser.add_argument(
        "--mode",
        choices=["condition", "statement"],
        default="condition",
        help="'condition' for filter boolean expressions (filter-by-condition:3 / secops_filter:2) or 'statement' for transform Editor statements (transform:2).",
    )
    parser.add_argument(
        "--context",
        choices=sorted(CONTEXT_PATHS.keys()),
        default="log",
        help="OTTL context ('log', 'resource', 'datapoint', 'metric', 'span', 'spanevent'). Default: log.",
    )
    parser.add_argument(
        "--body-state",
        choices=["any", "map", "string"],
        default="any",
        help="Expected type of 'body' at this point in the Bindplane pipeline ('map' after parse_json:3, 'string' before parse_json:3 or after google_secops_standardization:5).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output validation results as JSON.",
    )
    args = parser.parse_args()

    if not args.expressions:
        parser.error("Provide at least one OTTL expression to validate.")

    results = [
        validate_ottl_expression(
            expr, mode=args.mode, context=args.context, body_state=args.body_state
        )
        for expr in args.expressions
    ]
    all_valid = all(r["valid"] for r in results)

    if args.json:
        print(json.dumps({"valid": all_valid, "results": results}, indent=2))
    else:
        for res in results:
            status = "VALID" if res["valid"] else "INVALID"
            print(
                f"[{status}] ({res['mode']}, context={res['context']}, body_state={res['body_state']}): {res['expression']}"
            )
            for err in res["errors"]:
                print(f"  ERROR: {err}")
            for warn in res["warnings"]:
                print(f"  WARNING: {warn}")

    return 0 if all_valid else 1


if __name__ == "__main__":
    sys.exit(main())
