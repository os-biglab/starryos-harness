#!/usr/bin/env bash
# Hook: run cargo fmt on the crate containing the file just written/edited.
# Input: PostToolUse event JSON on stdin.
# Only acts on .rs files; silently exits for everything else.

set -euo pipefail

INPUT=$(cat)

# Extract file_path from tool_input (handles both Write and Edit tool events)
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

# Only act on Rust source files
[[ "$FILE" == *.rs ]] || exit 0

# Find the nearest Cargo.toml walking up from the file's directory
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

# Extract the package name from the Cargo.toml
CRATE=$(python3 - <<'EOF'
import sys, pathlib
manifest = pathlib.Path(sys.argv[1])
for line in manifest.read_text().splitlines():
    line = line.strip()
    if line.startswith("name") and "=" in line:
        val = line.split("=", 1)[1].strip().strip('"').strip("'")
        # Skip workspace-level Cargo.toml (has [workspace] but name could be the project)
        if val:
            print(val)
            break
EOF
"$MANIFEST")

[[ -n "$CRATE" ]] || exit 0

# Run cargo fmt — change to repo root first
cd /workspace
cargo fmt --package "$CRATE" 2>/dev/null && echo "[os-biglab] fmt: $CRATE" || true
