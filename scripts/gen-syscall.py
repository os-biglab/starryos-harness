#!/usr/bin/env python3
"""
gen-syscall.py — Generate StarryOS syscall boilerplate.

Usage:
    python3 gen-syscall.py --name <syscall_name> --nr <syscall_number> \
                           [--args "name:type,name:type,..."] \
                           [--category fs|mm|task|signal|net|time|misc]

Examples:
    python3 gen-syscall.py --name getxattr --nr 8 \
        --args "path:usize,name:usize,value:usize,size:usize" \
        --category fs

    python3 gen-syscall.py --name membarrier --nr 283 --args "cmd:i32,flags:u32,cpu_id:i32"

Output: ready-to-paste Rust code for:
  1. The syscall dispatch entry (for mod.rs)
  2. The implementation function (for <category>.rs)
"""

import sys
import argparse
import textwrap
from typing import List, Tuple

# ── Argument type helpers ─────────────────────────────────────────────────────

def arg_to_cast(name: str, idx: int, raw_type: str) -> str:
    """Generate: let <name> = args[<idx>] as <type>;"""
    raw = raw_type.strip()

    # Pointer types — wrap in UserInPtr / UserOutPtr
    if raw.startswith("*const"):
        inner = raw[len("*const"):].strip()
        return f"    let {name} = UserInPtr::<{inner}>::new(args[{idx}] as *const {inner});"
    if raw.startswith("*mut"):
        inner = raw[len("*mut"):].strip()
        return f"    let {name} = UserOutPtr::<{inner}>::new(args[{idx}] as *mut {inner});"

    # Integral types
    type_map = {
        "usize": "usize", "isize": "isize",
        "i32": "i32", "u32": "u32",
        "i64": "i64", "u64": "u64",
        "i16": "i16", "u16": "u16",
        "i8": "i8",   "u8":  "u8",
        "bool": "bool",
    }
    cast_type = type_map.get(raw, raw)
    return f"    let {name} = args[{idx}] as {cast_type};"

def parse_args(args_str: str) -> List[Tuple[str, str]]:
    """Parse 'name:type,name:type' into list of (name, type) tuples."""
    if not args_str:
        return []
    result = []
    for part in args_str.split(","):
        part = part.strip()
        if ":" in part:
            n, t = part.split(":", 1)
            result.append((n.strip(), t.strip()))
        else:
            result.append((part, "usize"))
    return result

def has_user_ptr(args: List[Tuple[str, str]]) -> bool:
    return any(t.startswith("*const") or t.startswith("*mut") for _, t in args)

# ── Code generation ───────────────────────────────────────────────────────────

def gen_dispatch_entry(name: str, nr: int, args: List[Tuple[str, str]]) -> str:
    argc = len(args)
    arg_refs = ", ".join(f"args[{i}]" for i in range(argc))
    if arg_refs:
        call = f"sys_{name}({arg_refs})"
    else:
        call = f"sys_{name}()"
    return f"        {nr} /* SYS_{name.upper()} */ => {call},"

def gen_impl(name: str, args: List[Tuple[str, str]], category: str, nr: int) -> str:
    lines = []

    # Imports
    imports = [
        "use crate::syscall::SyscallResult;",
        "use crate::syscall::SyscallError;",
    ]
    if has_user_ptr(args):
        imports.append("use crate::utils::user_ptr::{UserInPtr, UserOutPtr};")
    lines.append("\n".join(imports))
    lines.append("")

    # Doc comment
    lines.append(f"/// sys_{name} (nr={nr}): TODO: brief description.")
    lines.append(f"/// Linux man: https://man7.org/linux/man-pages/man2/{name}.2.html")

    # Function signature
    if args:
        raw_params = ", ".join(f"args_raw_{i}: usize" for i in range(len(args)))
        sig = f"pub fn sys_{name}({raw_params}) -> SyscallResult {{"
        lines.append(sig)
        lines.append(f"    // Re-name raw args to semantically meaningful names")
        for i, (n, _) in enumerate(args):
            lines.append(f"    let args = [args_raw_0{', 0'.join('' for _ in range(5))}];  // placeholder — use actual arg array")
            break
        lines.append(f"    let args: [usize; 6] = [" +
                     ", ".join(f"args_raw_{i}" for i in range(len(args))) +
                     ", 0" * (6 - len(args)) + "];")
        lines.append("")
        for i, (n, t) in enumerate(args):
            lines.append(arg_to_cast(n, i, t))
    else:
        lines.append(f"pub fn sys_{name}() -> SyscallResult {{")

    lines.append("")
    lines.append("    // TODO: implement sys_" + name)

    if has_user_ptr(args):
        for n, t in args:
            if t.startswith("*const"):
                inner = t[len("*const"):].strip()
                lines.append(f"    // Example read: let val = {n}.read()?;")
            elif t.startswith("*mut"):
                inner = t[len("*mut"):].strip()
                lines.append(f"    // Example write: {n}.write(result_value)?;")

    lines.append("")
    lines.append("    Err(SyscallError::ENOSYS)  // replace with actual implementation")
    lines.append("}")

    return "\n".join(lines)

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate StarryOS syscall boilerplate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(__doc__),
    )
    parser.add_argument("--name", required=True, help="syscall name without sys_ prefix (e.g. getxattr)")
    parser.add_argument("--nr", required=True, type=int, help="Linux syscall number")
    parser.add_argument("--args", default="", help="Comma-separated name:type pairs")
    parser.add_argument("--category", default="misc",
                        choices=["fs", "mm", "task", "signal", "net", "time", "misc", "io"],
                        help="Which category file to put the impl in")
    args = parser.parse_args()

    parsed_args = parse_args(args.args)

    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  os-biglab: syscall boilerplate for sys_{args.name} (nr={args.nr})")
    print(f"{sep}\n")

    print("── 1. Dispatch entry (add to os/StarryOS/kernel/src/syscall/mod.rs) ──\n")
    print(gen_dispatch_entry(args.name, args.nr, parsed_args))

    print(f"\n── 2. Implementation (add to os/StarryOS/kernel/src/syscall/{args.category}.rs) ──\n")
    print(gen_impl(args.name, parsed_args, args.category, args.nr))

    print(f"\n── 3. Next steps ──")
    print(f"  a. Add the dispatch entry to mod.rs")
    print(f"  b. Add the impl function to {args.category}.rs")
    print(f"  c. Remove placeholder args[] line and use actual arg parameter names")
    print(f"  d. Replace ENOSYS return with real implementation")
    print(f"  e. Run: cargo fmt && cargo xtask clippy --package starry-kernel")
    print(f"  f. Add test: test-suit/starryos/normal/{args.name}/")
    print()

if __name__ == "__main__":
    main()
