#!/usr/bin/env python3
"""
PostToolUse hook: log Edit/Write activity to docs/os-biglab-logs/activity.md.
Reads PostToolUse event JSON from stdin.
"""

import sys
import json
import os
from datetime import datetime
from pathlib import Path


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    tool_name = data.get("tool_name", "")
    if tool_name not in ("Edit", "Write"):
        return 0

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path:
        return 0

    # Determine log directory
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir:
        # Try to find git root
        try:
            import subprocess
            project_dir = subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
        except Exception:
            return 0

    log_dir = Path(project_dir) / "docs" / "os-biglab-logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "activity.md"

    # Create header if file doesn't exist
    if not log_file.exists():
        log_file.write_text("# Activity Log\n\n")

    # Format entry
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    action = "edited" if tool_name == "Edit" else "wrote"

    # Get relative path if possible
    try:
        rel_path = os.path.relpath(file_path, project_dir)
    except ValueError:
        rel_path = file_path

    entry = f"- [{timestamp}] {action} `{rel_path}`\n"

    # Append to log (deduplicate if same file as last entry)
    content = log_file.read_text()
    lines = content.strip().split("\n")
    if lines and rel_path in lines[-1]:
        return 0  # Skip duplicate

    with open(log_file, "a") as f:
        f.write(entry)

    return 0


if __name__ == "__main__":
    sys.exit(main())
