#!/usr/bin/env bash
# Run cargo clippy on a specific crate.
# Usage: auto-clippy.sh <crate-name>
# Or pipe a PostToolUse event JSON on stdin to auto-detect the crate.

set -euo pipefail

CRATE=""

if [[ $# -ge 1 ]]; then
    CRATE="$1"
else
    # Auto-detect from PostToolUse event JSON on stdin
    INPUT=$(cat)
    FILE=$(python3 - <<'EOF'
import sys, json
try:
    d = json.load(sys.stdin)
    ti = d.get("tool_input", {})
    print(ti.get("file_path", ""))
except Exception:
    print("")
EOF
<<< "$INPUT")

    [[ "$FILE" == *.rs ]] || exit 0

    DIR=$(dirname "$FILE")
    MANIFEST=""
    while [[ "$DIR" != "/" ]]; do
        if [[ -f "$DIR/Cargo.toml" ]]; then
            MANIFEST="$DIR/Cargo.toml"
            break
        fi
        DIR=$(dirname "$DIR")
    done

    [[ -n "$MANIFEST" ]] || exit 0

    CRATE=$(python3 - <<'EOF'
import sys, pathlib
manifest = pathlib.Path(sys.argv[1])
for line in manifest.read_text().splitlines():
    line = line.strip()
    if line.startswith("name") and "=" in line:
        val = line.split("=", 1)[1].strip().strip('"').strip("'")
        if val:
            print(val)
            break
EOF
"$MANIFEST")
fi

[[ -n "$CRATE" ]] || exit 0

cd /workspace
echo "[os-biglab] clippy: $CRATE"
cargo xtask clippy --package "$CRATE"
