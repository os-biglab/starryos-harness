#!/usr/bin/env python3
"""
Stop hook: generate session summary from activity log.
Reads Stop event JSON from stdin.
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

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir:
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
    activity_file = log_dir / "activity.md"

    if not activity_file.exists():
        return 0

    # Read activity log
    content = activity_file.read_text().strip()
    if not content or content == "# Activity Log":
        return 0

    # Count activities
    lines = [l for l in content.split("\n") if l.startswith("- [")]
    if not lines:
        return 0

    # Generate summary
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Extract unique files
    files = set()
    for line in lines:
        if "`" in line:
            parts = line.split("`")
            if len(parts) >= 2:
                files.add(parts[1])

    # Write summary
    summary_file = log_dir / f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
    summary = f"""# Session Summary

**Ended**: {timestamp}
**Activities**: {len(lines)}
**Files modified**: {len(files)}

## Modified Files
"""
    for f in sorted(files):
        summary += f"- `{f}`\n"

    summary += "\n## Activity Timeline\n"
    summary += content.replace("# Activity Log\n\n", "")

    summary_file.write_text(summary)

    # Clear activity log for next session
    activity_file.write_text("# Activity Log\n\n")

    print(f"[os-biglab] session summary: {summary_file.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
