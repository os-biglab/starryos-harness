#!/usr/bin/env bash
# PreToolUse hook: gate PR creation and git push behind clippy + fmt checks.
# Reads Bash tool input from stdin (JSON), checks if the command is gh pr create
# or git push, then enforces:
#   1. cargo fmt --all -- --check passes
#   2. cargo xtask clippy passes with ZERO warnings
#   3. No direct push to main/master/dev

set -euo pipefail

INPUT=$(cat)

# Extract the bash command from tool input
CMD=$(python3 - <<'EOF'
import sys, json
try:
    d = json.load(sys.stdin)
    ti = d.get("tool_input", {})
    print(ti.get("command", ""))
except Exception:
    print("")
EOF
<<< "$INPUT")

# Only gate gh pr create and git push
if ! echo "$CMD" | grep -qE '(gh\s+pr\s+create|git\s+push)'; then
    exit 0
fi

REPO_ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || echo /workspace)}"
cd "$REPO_ROOT"

# --- Gate 1: Block direct push to protected branches ---
if echo "$CMD" | grep -qE 'git\s+push'; then
    BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
    if echo "$BRANCH" | grep -qE '^(main|master|dev)$'; then
        echo "[os-biglab] BLOCKED: direct push to protected branch '$BRANCH' is not allowed." >&2
        echo "[os-biglab] Create a feature branch and open a PR instead." >&2
        exit 1
    fi
fi

# --- Gate 2: cargo fmt check ---
echo "[os-biglab] pre-push gate: checking cargo fmt..." >&2
if ! cargo fmt --all -- --check >/dev/null 2>&1; then
    echo "[os-biglab] BLOCKED: cargo fmt check failed." >&2
    echo "[os-biglab] Run 'cargo fmt --all' to fix formatting before pushing." >&2
    exit 1
fi
echo "[os-biglab] pre-push gate: fmt OK" >&2

# --- Gate 3: clippy with zero warnings ---
echo "[os-biglab] pre-push gate: running clippy (zero warnings required)..." >&2
CLIPPY_OUTPUT=$(cargo xtask clippy --since HEAD~1 2>&1) || true

# Check for any warning-level diagnostics (compiler warning, clippy warning)
if echo "$CLIPPY_OUTPUT" | grep -qE '^warning(\[|$)'; then
    echo "[os-biglab] BLOCKED: clippy produced warnings. tgoskits requires zero warnings." >&2
    echo "" >&2
    echo "$CLIPPY_OUTPUT" | grep -E '^warning' | head -20 >&2
    echo "" >&2
    echo "[os-biglab] Fix all clippy warnings before pushing." >&2
    exit 1
fi

# Also check for error-level diagnostics
if echo "$CLIPPY_OUTPUT" | grep -qE '^error'; then
    echo "[os-biglab] BLOCKED: clippy produced errors." >&2
    echo "" >&2
    echo "$CLIPPY_OUTPUT" | grep -E '^error' | head -10 >&2
    exit 1
fi

echo "[os-biglab] pre-push gate: clippy OK (zero warnings)" >&2
echo "[os-biglab] pre-push gate: ALL CHECKS PASSED" >&2
exit 0
