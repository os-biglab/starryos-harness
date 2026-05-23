#!/usr/bin/env python3
"""
Lock order graph builder and deadlock detector.
Scans Rust source files for lock acquisition patterns and builds a directed graph.
Detects cycles (potential deadlocks).

Usage:
    python3 lock-order-graph.py <directory>
    python3 lock-order-graph.py os/StarryOS/kernel/src/
"""

import sys
import os
import re
from collections import defaultdict
from pathlib import Path


# Pattern: let guard = something.lock()
LOCK_ACQUIRE = re.compile(
    r'let\s+(?:mut\s+)?(\w+)\s*=\s*(\w+(?:\.\w+)*)\.lock\(\)'
)

# Pattern: something.lock().method() (temporary lock)
LOCK_TEMP = re.compile(
    r'(\w+(?:\.\w+)*)\.lock\(\)\.(\w+)\('
)

# Pattern: drop(guard)
DROP_GUARD = re.compile(r'drop\((\w+)\)')


def scan_file(filepath):
    """Scan a single file for lock acquisition patterns."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    lines = content.split("\n")
    acquisitions = []
    held_locks = []  # stack of (lock_name, var_name)

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Skip comments
        if stripped.startswith("//") or stripped.startswith("/*"):
            continue

        # Check for held lock acquisition
        m = LOCK_ACQUIRE.search(stripped)
        if m:
            var_name = m.group(1)
            lock_name = m.group(2)
            acquisitions.append({
                "file": str(filepath),
                "line": i,
                "lock": lock_name,
                "var": var_name,
                "type": "held",
                "held": [l[0] for l in held_locks],
            })
            held_locks.append((lock_name, var_name))
            continue

        # Check for drop
        m = DROP_GUARD.search(stripped)
        if m:
            dropped = m.group(1)
            held_locks = [(l, v) for l, v in held_locks if v != dropped]
            continue

        # Check for temporary lock (not held)
        m = LOCK_TEMP.search(stripped)
        if m:
            lock_name = m.group(1)
            acquisitions.append({
                "file": str(filepath),
                "line": i,
                "lock": lock_name,
                "var": None,
                "type": "temporary",
                "held": [l[0] for l in held_locks],
            })

    return acquisitions


def build_graph(acquisitions):
    """Build lock order directed graph."""
    edges = defaultdict(set)  # from_lock -> set of to_locks
    details = defaultdict(list)  # (from, to) -> list of locations

    for acq in acquisitions:
        for held in acq["held"]:
            if held != acq["lock"]:
                edges[held].add(acq["lock"])
                details[(held, acq["lock"])].append(
                    f"{acq['file']}:{acq['line']}"
                )

    return edges, details


def find_cycles(edges):
    """Find cycles in the lock order graph using DFS."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = defaultdict(int)
    parent = {}
    cycles = []

    def dfs(u, path):
        color[u] = GRAY
        for v in edges.get(u, []):
            if color[v] == GRAY:
                # Found cycle
                cycle = []
                idx = path.index(v)
                cycle = path[idx:] + [v]
                cycles.append(cycle)
            elif color[v] == WHITE:
                parent[v] = u
                dfs(v, path + [v])
        color[u] = BLACK

    all_nodes = set(edges.keys())
    for targets in edges.values():
        all_nodes.update(targets)

    for node in sorted(all_nodes):
        if color[node] == WHITE:
            dfs(node, [node])

    return cycles


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 lock-order-graph.py <directory>")
        sys.exit(1)

    directory = Path(sys.argv[1])
    if not directory.is_dir():
        print(f"Error: {directory} is not a directory")
        sys.exit(1)

    # Scan all .rs files
    all_acquisitions = []
    for rs_file in directory.rglob("*.rs"):
        # Skip test files
        if "/test" in str(rs_file).lower() or "mock" in str(rs_file).lower():
            continue
        acqs = scan_file(rs_file)
        all_acquisitions.extend(acqs)

    if not all_acquisitions:
        print("No lock acquisitions found.")
        sys.exit(0)

    # Build graph
    edges, details = build_graph(all_acquisitions)

    # Print graph
    print("## Lock Order Graph\n")
    for from_lock in sorted(edges.keys()):
        for to_lock in sorted(edges[from_lock]):
            locs = details.get((from_lock, to_lock), [])
            print(f"  {from_lock} → {to_lock}")
            for loc in locs[:3]:  # Show first 3 locations
                print(f"    at {loc}")

    # Find cycles
    cycles = find_cycles(edges)
    if cycles:
        print(f"\n## DEADLOCK CYCLES DETECTED: {len(cycles)}\n")
        for i, cycle in enumerate(cycles, 1):
            print(f"  Cycle {i}: {' → '.join(cycle)}")
        sys.exit(1)
    else:
        print("\n## No deadlock cycles detected.")
        sys.exit(0)


if __name__ == "__main__":
    main()
