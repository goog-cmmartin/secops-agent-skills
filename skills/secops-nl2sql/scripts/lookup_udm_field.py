#!/usr/bin/env python3
"""UDM & SecOps Proto Field Inspector.

Searches local Protocol Buffer definitions (udm.proto, ingestion.proto)
to find exact field names, nested types, arrays, and documentation comments.

Usage:
    python scripts/lookup_udm_field.py <field_or_message_name>
    python scripts/lookup_udm_field.py process
    python scripts/lookup_udm_field.py security_result
"""

import sys
import os
import re

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROTOS_DIR = os.path.join(CURRENT_DIR, "../resources/protos")


def search_protos(keyword: str):
    proto_files = ["udm.proto", "ingestion.proto"]
    keyword_re = re.compile(re.escape(keyword), re.IGNORECASE)

    matches = []

    for fname in proto_files:
        fpath = os.path.join(PROTOS_DIR, fname)
        if not os.path.exists(fpath):
            continue

        with open(fpath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        current_message = None
        message_stack = []

        for idx, line in enumerate(lines):
            stripped = line.strip()

            # Track message / enum blocks
            msg_match = re.match(r"^(message|enum)\s+([A-Za-z0-9_]+)", stripped)
            if msg_match:
                message_stack.append(msg_match.group(2))
                current_message = ".".join(message_stack)

            if "}" in stripped and message_stack:
                message_stack.pop()
                current_message = ".".join(message_stack) if message_stack else None

            # Check if line matches search keyword
            if keyword_re.search(line):
                # Grab surrounding comments if present
                comment_lines = []
                c_idx = idx - 1
                while c_idx >= 0 and lines[c_idx].strip().startswith("//"):
                    comment_lines.insert(0, lines[c_idx].strip())
                    c_idx -= 1

                matches.append({
                    "file": fname,
                    "line_num": idx + 1,
                    "message": current_message or "Top-level",
                    "text": line.rstrip(),
                    "comments": comment_lines[-3:]  # up to 3 comment lines
                })

    return matches


def main():
    if len(sys.argv) < 2:
        print("Usage: python lookup_udm_field.py <field_or_message_name>")
        sys.exit(1)

    term = sys.argv[1]
    results = search_protos(term)

    if not results:
        print(f"No matching fields or definitions found for '{term}' in local protos.")
        sys.exit(0)

    print(f"--- Found {len(results)} matches for '{term}' in SecOps Protos ---")
    for r in results[:20]:
        print(f"\n[{r['file']}:{r['line_num']}] in Message: {r['message']}")
        for c in r["comments"]:
            print(f"  {c}")
        print(f"  > {r['text'].strip()}")

    if len(results) > 20:
        print(f"\n... and {len(results) - 20} more matches.")


if __name__ == "__main__":
    main()
