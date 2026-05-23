#!/usr/bin/env python3
"""
parse-qemu-log.py — Extract and summarise kernel errors from QEMU/OS output.

Usage:
    python3 parse-qemu-log.py [logfile]     # read from file
    cargo xtask starry qemu ... 2>&1 | python3 parse-qemu-log.py  # pipe

Output: structured summary of panics, faults, syscall errors, and warnings.
"""

import sys
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional

# ── Pattern definitions ───────────────────────────────────────────────────────

PATTERNS = {
    "panic": re.compile(
        r"panicked at '?([^'\"]+)'?,?\s*([\w/.\-]+\.rs:\d+)",
        re.IGNORECASE
    ),
    "panic_msg": re.compile(r"panicked at (.*)", re.IGNORECASE),
    "page_fault": re.compile(
        r"(InstructionPageFault|LoadPageFault|StorePageFault|PageFault)"
        r".*?(?:addr|vaddr|badaddr)[=: ]+(?:0x)?([0-9a-fA-F]+)",
        re.IGNORECASE
    ),
    "fault_generic": re.compile(
        r"(InstructionFault|LoadFault|StoreFault|IllegalInstruction"
        r"|InstructionMisaligned|LoadMisaligned|StoreMisaligned"
        r"|InstructionAccessFault|LoadAccessFault|StoreAccessFault)",
        re.IGNORECASE
    ),
    "exception": re.compile(
        r"Unhandled\s+(?:exception|trap)[:\s]+(\w+)",
        re.IGNORECASE
    ),
    "sepc": re.compile(r"sepc\s*[=:]\s*(?:0x)?([0-9a-fA-F]+)", re.IGNORECASE),
    "pc":   re.compile(r"\b(?:pc|epc|elr|rip)\s*[=:]\s*(?:0x)?([0-9a-fA-F]+)", re.IGNORECASE),
    "syscall_err": re.compile(
        r"\[syscall\].*?(?:nr|syscall)[\s=]+(\d+).*?(?:err|error|errno)[=: ]+(-?\d+)",
        re.IGNORECASE
    ),
    "warn": re.compile(r"\b(WARN|WARNING)\b[:\s]+(.*)", re.IGNORECASE),
    "oom": re.compile(r"(out of memory|OOM|alloc.*failed|ENOMEM)", re.IGNORECASE),
    "deadlock": re.compile(r"(deadlock|spinlock.*timeout|lock.*stuck)", re.IGNORECASE),
    "kernel_bug": re.compile(r"(kernel BUG|BUG:|Oops:)", re.IGNORECASE),
    "test_result": re.compile(r"(test result|PASSED|FAILED|ok \d+|FAILED \d+)", re.IGNORECASE),
    "backtrace_frame": re.compile(r"^\s*#\d+\s+0x[0-9a-fA-F]+", re.MULTILINE),
}

LINUX_ERRNO = {
    1: "EPERM", 2: "ENOENT", 9: "EBADF", 11: "EAGAIN",
    12: "ENOMEM", 13: "EACCES", 14: "EFAULT", 22: "EINVAL",
    38: "ENOSYS", 95: "EOPNOTSUPP",
}

@dataclass
class Finding:
    category: str
    message: str
    line_no: int
    context: List[str] = field(default_factory=list)

def classify_line(line: str, line_no: int, prev_lines: List[str]) -> Optional[Finding]:
    """Return a Finding if the line matches a known error pattern."""

    m = PATTERNS["panic"].search(line) or PATTERNS["panic_msg"].search(line)
    if m:
        return Finding("PANIC", line.strip(), line_no, prev_lines[-3:])

    m = PATTERNS["page_fault"].search(line)
    if m:
        fault_type, addr = m.group(1), m.group(2)
        return Finding("PAGE_FAULT", f"{fault_type} at 0x{addr}", line_no, prev_lines[-3:])

    m = PATTERNS["fault_generic"].search(line)
    if m and "handled" not in line.lower():
        return Finding("FAULT", m.group(1), line_no, prev_lines[-3:])

    m = PATTERNS["exception"].search(line)
    if m:
        return Finding("EXCEPTION", m.group(1), line_no, prev_lines[-3:])

    m = PATTERNS["oom"].search(line)
    if m:
        return Finding("OOM", line.strip(), line_no, prev_lines[-3:])

    m = PATTERNS["deadlock"].search(line)
    if m:
        return Finding("DEADLOCK", line.strip(), line_no, prev_lines[-3:])

    m = PATTERNS["kernel_bug"].search(line)
    if m:
        return Finding("KERNEL_BUG", line.strip(), line_no, prev_lines[-3:])

    return None

def extract_pc(lines: List[str]) -> Optional[str]:
    for line in lines:
        m = PATTERNS["sepc"].search(line) or PATTERNS["pc"].search(line)
        if m:
            return "0x" + m.group(1)
    return None

def parse(text: str) -> List[Finding]:
    lines = text.splitlines()
    findings: List[Finding] = []
    seen: set = set()
    prev: List[str] = []

    for i, line in enumerate(lines):
        f = classify_line(line, i + 1, prev)
        if f:
            key = (f.category, f.message[:60])
            if key not in seen:
                seen.add(key)
                findings.append(f)
        prev.append(line)
        if len(prev) > 10:
            prev.pop(0)

    return findings

def render(findings: List[Finding], raw_lines: List[str]) -> str:
    if not findings:
        return "✓  No kernel errors detected in the log.\n"

    out = []
    out.append(f"{'='*60}")
    out.append(f"  os-biglab: QEMU Log Analysis — {len(findings)} issue(s) found")
    out.append(f"{'='*60}")

    # Group by severity
    criticals = [f for f in findings if f.category in ("PANIC", "PAGE_FAULT", "KERNEL_BUG", "FAULT", "EXCEPTION")]
    warnings   = [f for f in findings if f.category in ("OOM", "DEADLOCK")]
    infos      = [f for f in findings if f.category not in ("PANIC", "PAGE_FAULT", "KERNEL_BUG", "FAULT", "EXCEPTION", "OOM", "DEADLOCK")]

    if criticals:
        out.append("\n## CRITICAL\n")
        for f in criticals:
            out.append(f"  [{f.category}] line {f.line_no}: {f.message}")
            # Try to find PC near this finding
            context_text = "\n".join(raw_lines[max(0, f.line_no-5):f.line_no+10])
            pc = extract_pc(context_text.splitlines())
            if pc:
                out.append(f"    → PC/sepc: {pc}")
                out.append(f"    → Run: addr2line -e target/<arch>/release/starry -f {pc}")
            if f.context:
                out.append("    Context:")
                for c in f.context:
                    out.append(f"      {c}")

    if warnings:
        out.append("\n## WARNINGS\n")
        for f in warnings:
            out.append(f"  [{f.category}] line {f.line_no}: {f.message}")

    if infos:
        out.append("\n## INFO\n")
        for f in infos:
            out.append(f"  [{f.category}] line {f.line_no}: {f.message}")

    out.append(f"\n{'='*60}")
    out.append("Next steps:")
    if any(f.category == "PANIC" for f in findings):
        out.append("  1. Open the file:line from the panic message")
        out.append("  2. Check for unwrap/overflow/assert at that site")
        out.append("  3. See: skills/os-debug/references/panic-patterns.md")
    if any(f.category in ("PAGE_FAULT", "FAULT") for f in findings):
        out.append("  1. Run with GDB: cargo xtask starry qemu -t riscv64 -- -s -S")
        out.append("  2. See: skills/os-debug/references/gdb-workflow.md")
    if any(f.category == "DEADLOCK" for f in findings):
        out.append("  1. Connect GDB: thread apply all bt")
        out.append("  2. Check lock acquisition order")
    out.append(f"{'='*60}\n")

    return "\n".join(out)

def main():
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        if not path.exists():
            print(f"Error: file not found: {path}", file=sys.stderr)
            sys.exit(1)
        text = path.read_text(errors="replace")
    else:
        text = sys.stdin.read()

    raw_lines = text.splitlines()
    findings = parse(text)
    print(render(findings, raw_lines))
    sys.exit(1 if findings else 0)

if __name__ == "__main__":
    main()
