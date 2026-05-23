---
name: os-nav
description: Navigate and understand TGOSKits OS codebase (ArceOS / StarryOS / Axvisor). Use when exploring unfamiliar modules, finding where a feature is implemented, understanding component relationships, tracing execution flow from entry point to implementation, or learning how a subsystem works. Trigger phrases: where is, find, how does, understand, explain, show me, which crate, which module, navigate, trace, what handles, where is X implemented, how is Y called.
allowed-tools: "Read Grep Glob Bash LSP"
effort: medium
---

# OS Codebase Navigation

You are helping navigate the TGOSKits repository. Use the maps below to quickly orient, then drill into specifics with Read/Grep/LSP.

## Repository Overview

```
/workspace/
├── os/arceos/           ArceOS — modular OS framework
│   ├── modules/         Kernel modules (axhal, axtask, axmm, axfs, axnet, axdriver…)
│   ├── api/             C + POSIX API layers
│   └── ulib/axstd/      Rust std implementation
├── os/StarryOS/         StarryOS — POSIX-compatible kernel
│   └── kernel/src/
│       ├── syscall/     All syscall implementations
│       ├── task/        Process and thread management
│       ├── file/        File descriptor table, VFS glue
│       ├── mm/          Memory management (mmap, brk, …)
│       └── pseudofs/    procfs, sysfs entries
├── os/axvisor/          Axvisor — type-1 hypervisor
├── components/          60+ shared components (subtree-managed)
│   ├── axplat_crates/   Multi-arch platform support
│   ├── axmm_crates/     Address space, page tables
│   ├── axdriver_crates/ Driver framework (block/net/display/virtio)
│   ├── axfs_crates/     VFS, ramfs, devfs
│   ├── axsched/         Task scheduler
│   ├── starry-process/  Process data structures
│   ├── starry-signal/   Signal subsystem
│   └── starry-vm/       Virtual memory (mmap implementation)
├── test-suit/           System test cases
│   ├── arceos/          ArceOS QEMU tests
│   └── starryos/        StarryOS QEMU tests (normal/ stress/)
└── scripts/axbuild/     xtask implementation (Rust)
```

See `references/module-map.md` for the full module dependency graph.

---

## Find-by-Feature Quick Reference

| I want to understand… | Start here |
|-----------------------|-----------|
| How a syscall is dispatched | `os/StarryOS/kernel/src/syscall/mod.rs` |
| Specific syscall (e.g. mmap) | `grep -rn "fn sys_mmap" os/ --include="*.rs"` |
| Process creation (fork/clone) | `os/StarryOS/kernel/src/syscall/task.rs` + `components/starry-process/` |
| Signal delivery | `components/starry-signal/src/` |
| Memory mapping internals | `components/starry-vm/src/` → `components/axmm_crates/` |
| Page table / TLB | `os/arceos/modules/axhal/src/arch/<arch>/paging.rs` |
| Hardware interrupts | `os/arceos/modules/axhal/src/arch/<arch>/trap.rs` |
| Context switch | `os/arceos/modules/axtask/src/` → `components/axsched/` |
| VFS / file ops | `components/axfs_crates/axfs_vfs/src/` |
| Device driver framework | `components/axdriver_crates/axdriver/src/` |
| Timer / clock | `os/arceos/modules/axhal/src/time.rs` |
| Boot / init sequence | `os/arceos/modules/axruntime/src/lib.rs` |
| Platform config | `components/axplat_crates/platforms/` |

---

## Navigation Commands

```bash
# Find a function definition
grep -rn "fn <name>" os/ components/ --include="*.rs"

# Find a trait definition
grep -rn "trait <Name>" os/ components/ --include="*.rs"

# Find all implementations of a trait
grep -rn "impl <Name>" os/ components/ --include="*.rs"

# Find where a crate is used
grep -rn "<crate-name>" Cargo.toml os/ components/ --include="*.toml"

# List all syscall functions in StarryOS
grep -rn "pub fn sys_" os/StarryOS/kernel/src/syscall/ --include="*.rs"

# Show dependency tree for a crate
cargo tree -p <crate> --workspace

# Find crate_interface declarations
grep -rn "def_interface\|impl_interface" os/ components/ --include="*.rs"

# Find feature flags for a crate
grep -rn "feature = \"" os/arceos/modules/<module>/Cargo.toml
```

---

## Understanding `crate_interface`

TGOSKits uses the `crate_interface` crate for cross-crate weak-link calls (similar to C weak symbols):

```rust
// Declaring an interface (e.g., in axhal)
#[def_interface]
pub trait MyTrait {
    fn some_method() -> RetType;
}

// Calling the interface (from anywhere)
call_interface!(MyTrait::some_method())

// Implementing in another crate
#[impl_interface]
impl MyTrait for () {
    fn some_method() -> RetType { ... }
}
```

When you see `call_interface!(Foo::bar())`:
1. `grep -rn "def_interface" os/ components/ --include="*.rs"` to find the trait
2. `grep -rn "impl_interface" os/ components/ --include="*.rs"` to find all implementations
3. The implementation that gets linked is determined by the dependency graph

---

## Tracing Execution Flow

### Entry point → syscall

1. User program triggers `ecall` (riscv) / `svc` (aarch64) / `syscall` (x86)
2. Trap handler: `os/arceos/modules/axhal/src/arch/<arch>/trap.rs`
3. StarryOS exception entry: `os/StarryOS/kernel/src/` (look for `handle_syscall`)
4. Dispatch: `os/StarryOS/kernel/src/syscall/mod.rs`
5. Implementation: `os/StarryOS/kernel/src/syscall/<category>.rs`

### Boot sequence

1. Platform reset vector → `os/arceos/modules/axhal/src/arch/<arch>/boot.rs`
2. `axruntime`: `os/arceos/modules/axruntime/src/lib.rs` → `rust_main()`
3. Memory init → Driver init → FS init → Network init → User app

---

## LSP-assisted navigation

For precise Go-to-definition and find-references, use the LSP tool:
- **goToDefinition** at a symbol to jump to its definition
- **findReferences** to see everywhere a function/type is used
- **hover** for type info and documentation
- **incomingCalls** / **outgoingCalls** for call hierarchy

Example: to understand all callers of `sys_mmap`:
1. Read `os/StarryOS/kernel/src/syscall/mm.rs` to find the line of `fn sys_mmap`
2. Use `LSP findReferences` at that line/column
