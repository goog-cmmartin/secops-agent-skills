#!/bin/bash
set -e

echo "Note: 'Jetski' was Google's internal development harness. Forwarding to 'install_antigravity.sh'..."
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
exec "$SCRIPT_DIR/install_antigravity.sh" "$@"
