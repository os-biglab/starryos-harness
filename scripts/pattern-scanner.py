#!/usr/bin/env python3
"""
Pattern scanner: scans kernel source against evolving regex rules from patterns.json.
Reports findings with severity levels.

Usage:
    python3 pattern-scanner.py <directory>
    python3 pattern-scanner.py os/StarryOS/kernel/src/
    python3 pattern-scanner.py --patterns /path/to/patterns.json <directory>
"""

import sys
import os
import re
import json
from pathlib import Path


DEFAULT_PATTERNS_FILE = None


def find_patterns_file():
    """Find patterns.json relative to this script."""
    script_dir = Path(__file__).parent
    candidates = [
        script_dir.parent / "docs" / "os-biglab-patterns" / "patterns.json",
        script_dir / "patterns.json",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def load_patterns(path):
    """Load pattern rules from JSON file."""
    if not path or not path.exists():
        # Use built-in defaults
        return get_default_patterns()
    try:
        return json.loads(path.read_text())
    except Exception as e:
        print(f"Warning: failed to load {path}: {e}")
        return get_default_patterns()


def get_default_patterns():
    """Built-in default patterns."""
    return [
        {
            "id": "todo-fixme",
            "description": "TODO/FIXME/HACK marker",
            "grep_pattern": r"(TODO|FIXME|HACK|XXX)\b",
            "file_glob": "*.rs",
            "severity": "P3",
            "category": "Semantic",
        },
        {
            "id": "unwrap-in-kernel",
            "description": "unwrap() in kernel code (may panic)",
            "grep_pattern": r"\.unwrap\(\)",
            "file_glob": "*.rs",
            "severity": "P2",
            "category": "Safety",
        },
        {
            "id": "unsafe-no-comment",
            "description": "unsafe block without SAFETY comment nearby",
            "grep_pattern": r"unsafe\s*\{",
            "file_glob": "*.rs",
            "severity": "P2",
            "category": "Safety",
        },
        {
            "id": "catch-all-match",
            "description": "Wildcard match arm that may hide errors",
            "grep_pattern": r"_\s*=>\s*(Ok|return|continue|break)",
            "file_glob": "*.rs",
            "severity": "P2",
            "category": "Semantic",
        },
    ]


def should_exclude(line, exclude_pattern):
    """Check if line matches exclude pattern."""
    if not exclude_pattern:
        return False
    return bool(re.search(exclude_pattern, line, re.IGNORECASE))


def scan_file(filepath, patterns):
    """Scan a single file against all patterns."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    lines = content.split("\n")
    findings = []

    for pattern in patterns:
        pattern_id = pattern["id"]
        grep_pattern = pattern["grep_pattern"]
        severity = pattern.get("severity", "P3")
        category = pattern.get("category", "General")
        exclude = pattern.get("exclude_pattern", "")
        context_lines = pattern.get("context_lines", 1)
        file_glob = pattern.get("file_glob", "*.rs")

        # Check file glob
        if file_glob and not filepath.match(file_glob):
            continue

        try:
            regex = re.compile(grep_pattern)
        except re.error:
            continue

        for i, line in enumerate(lines, 1):
            if regex.search(line):
                if should_exclude(line, exclude):
                    continue

                # Get context
                start = max(0, i - 1 - context_lines)
                end = min(len(lines), i + context_lines)
                context = lines[start:end]

                findings.append({
                    "file": str(filepath),
                    "line": i,
                    "pattern_id": pattern_id,
                    "severity": severity,
                    "category": category,
                    "description": pattern.get("description", ""),
                    "matched": line.strip(),
                    "context": context,
                })

    return findings


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Pattern scanner for Rust kernel code")
    parser.add_argument("directory", help="Directory to scan")
    parser.add_argument("--patterns", help="Path to patterns.json")
    parser.add_argument("--severity", default="P0,P1,P2,P3",
                        help="Filter by severity (default: P0,P1,P2,P3)")
    args = parser.parse_args()

    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"Error: {directory} is not a directory")
        sys.exit(1)

    # Load patterns
    if args.patterns:
        patterns_path = Path(args.patterns)
    else:
        patterns_path = find_patterns_file()

    patterns = load_patterns(patterns_path)
    allowed_severities = set(args.severity.split(","))

    # Scan
    all_findings = []
    for rs_file in directory.rglob("*.rs"):
        # Skip test files
        if "/test" in str(rs_file).lower():
            continue
        findings = scan_file(rs_file, patterns)
        all_findings.extend(findings)

    # Filter by severity
    all_findings = [f for f in all_findings if f["severity"] in allowed_severities]

    # Report
    if not all_findings:
        print("No findings.")
        sys.exit(0)

    # Group by severity
    by_severity = {}
    for f in all_findings:
        by_severity.setdefault(f["severity"], []).append(f)

    total = len(all_findings)
    p0_count = len(by_severity.get("P0", []))
    p1_count = len(by_severity.get("P1", []))

    print(f"## Pattern Scan Results\n")
    print(f"Total findings: {total}")
    print(f"  P0: {p0_count}, P1: {p1_count}, P2: {len(by_severity.get('P2', []))}, P3: {len(by_severity.get('P3', []))}")
    print()

    for severity in ["P0", "P1", "P2", "P3"]:
        findings = by_severity.get(severity, [])
        if not findings:
            continue

        print(f"### {severity} ({len(findings)} findings)\n")
        for f in findings[:20]:  # Limit output
            print(f"  {f['file']}:{f['line']} [{f['pattern_id']}] {f['description']}")
            print(f"    {f['matched']}")
            print()

        if len(findings) > 20:
            print(f"  ... and {len(findings) - 20} more\n")

    # Exit code: 1 if P0 findings
    if p0_count > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
