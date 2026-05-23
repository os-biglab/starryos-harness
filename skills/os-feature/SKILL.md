---
name: os-feature
description: Implement new features in TGOSKits OS (ArceOS / StarryOS / Axvisor). Use when adding a new Linux syscall to StarryOS, implementing a new ArceOS module, writing a new device driver, extending the VFS layer, or modifying memory management. Trigger phrases: add syscall, implement syscall, new module, new driver, add feature, implement, port, missing syscall, extend, support.
allowed-tools: "Read Grep Glob Write Edit Bash LSP"
effort: high
---

# OS Feature Implementation

You are adding a new feature to TGOSKits. Follow the correct workflow for the type of feature.

## Quick: Which subsystem?

| Feature type | Guide section |
|-------------|---------------|
| New Linux syscall (StarryOS) | §A |
| New ArceOS kernel module | §B |
| New device driver | §C |
| File system extension | §D |
| Memory management change | §E |

---

## §A — Adding a New StarryOS Syscall

### A1. Locate the syscall number

Linux syscall tables by arch:
- riscv64: `os/StarryOS/kernel/src/syscall/mod.rs` (look for existing `SYS_*` constants)
- Or grep: `grep -rn "SYS_<name>" components/ os/ --include="*.rs"`

Generate boilerplate with:
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/gen-syscall.py \
  --name <syscall_name> \
  --nr <syscall_number> \
  --args "<arg0_name>:<arg0_type>,<arg1_name>:<arg1_type>"
```

Example:
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/gen-syscall.py \
  --name getxattr \
  --nr 8 \
  --args "path:*const u8,name:*const u8,value:*mut u8,size:usize"
```

### A2. Register in dispatch table

File: `os/StarryOS/kernel/src/syscall/mod.rs`

Find the `match nr` block (or `syscall_dispatch!` macro) and add:
```rust
SYS_<NAME> => sys_<name>(args[0], args[1], ...),
```

### A3. Implement the function

Choose the correct file based on category:

| Category | File |
|----------|------|
| File I/O | `os/StarryOS/kernel/src/syscall/fs.rs` |
| Memory | `os/StarryOS/kernel/src/syscall/mm.rs` |
| Process/Thread | `os/StarryOS/kernel/src/syscall/task.rs` |
| Signals | `os/StarryOS/kernel/src/syscall/signal.rs` |
| Network | `os/StarryOS/kernel/src/syscall/net.rs` |
| Time | `os/StarryOS/kernel/src/syscall/time.rs` |
| Other | Create new file, re-export from `mod.rs` |

**Implementation template:**
```rust
/// sys_<name>: brief description of what this syscall does.
/// See: https://man7.org/linux/man-pages/man2/<name>.2.html
pub fn sys_<name>(arg0: usize, arg1: usize, arg2: usize) -> SyscallResult {
    // 1. Parse and validate arguments
    let ptr = arg0 as *const u8;
    let ptr = UserInPtr::<u8>::new(ptr);          // wraps user pointer safely
    let len = arg1;
    if len > MAX_SAFE_LEN { return Err(SyscallError::EINVAL); }

    // 2. Perform operation (use '?' to propagate errors)
    let data = ptr.read_array(len)?;

    // 3. Return result (0 on success, or positive value like fd/count)
    Ok(0)
}
```

**User pointer safety rules:**
- NEVER dereference raw `*const T` / `*mut T` from userspace
- Use `UserInPtr<T>` for reading from user, `UserOutPtr<T>` for writing to user
- Validate length before `read_array` / `write_array`
- Return `Err(SyscallError::EFAULT)` if pointer is invalid

See `references/syscall-guide.md` for complete patterns.

### A4. Test

```bash
cargo fmt --package starry-kernel    # (or actual crate name)
cargo xtask clippy --package starry-kernel
cargo xtask starry test qemu -t riscv64
```

Add a test case in `test-suit/starryos/normal/<syscall-name>/` (use `starry-test-suit` skill).

---

## §B — New ArceOS Module

See `references/module-guide.md` for full details.

1. Create `os/arceos/modules/ax<name>/`:
   - `Cargo.toml` (use `edition.workspace = true`, `version.workspace = true`)
   - `src/lib.rs`

2. Add to workspace `Cargo.toml` under `[workspace.members]`

3. Expose interfaces via `crate_interface` if other modules need to call in:
   ```rust
   // In your module
   #[def_interface]
   pub trait MyInterface { fn method(&self) -> RetType; }
   ```

4. Add feature flag in dependent modules if optional

5. Verify:
   ```bash
   cargo fmt --package ax<name>
   cargo xtask clippy --package ax<name>
   cargo xtask arceos build -t riscv64 -a <example>
   ```

---

## §C — New Device Driver

See `references/driver-guide.md` for full details.

1. Create crate under `components/axdriver_crates/` or `drivers/`
2. Implement the relevant trait from `axdriver_crates`:
   - Block device: `BlockDriverOps`
   - Network device: `NetDriverOps`
   - Display: `DisplayDriverOps`
3. Register in `os/arceos/modules/axdriver/src/`:
   - Add `#[cfg(feature = "<driver>")]` block
   - Register via the driver registry
4. Expose via feature flag in `axdriver/Cargo.toml`

---

## §D — VFS / File System Extension

Key files:
- VFS interface: `components/axfs_crates/axfs_vfs/src/`
- ramfs: `components/axfs_crates/axfs_ramfs/src/`
- devfs: `components/axfs_crates/axfs_devfs/src/`
- StarryOS FS glue: `os/StarryOS/kernel/src/file/`

Pattern for new file type or operation:
1. Add method to `VfsNodeOps` or `VfsOps` trait in `axfs_vfs`
2. Implement in the relevant fs crate (ramfs / devfs / your new fs)
3. Wire up in StarryOS `kernel/src/file/` if it needs OS-level handling

---

## §E — Memory Management Change

Key paths:
- Address space: `components/axmm_crates/axmm/src/`
- Page table: `os/arceos/modules/axhal/src/arch/<arch>/paging.rs`
- StarryOS MM: `os/StarryOS/kernel/src/mm/`
- Starry VM: `components/starry-vm/src/`

Rules:
- Any change to page table code must be tested on all target archs (riscv64, aarch64, x86_64)
- After mapping changes, flush TLB: `flush_tlb_all()` or `flush_tlb_page(va)`
- Mark device/DMA memory `NON_CACHEABLE` in page table flags
- Never hardcode page size — use `PAGE_SIZE` from `axconfig` or `axhal`

---

## Completion checklist

- [ ] `cargo fmt` run on all modified crates
- [ ] `cargo xtask clippy --package <crate>` passes with no warnings
- [ ] Tested on at least riscv64; ideally also aarch64
- [ ] Test case added or existing test verified
- [ ] `cargo xtask starry test qemu -t riscv64` passes
- [ ] PR title follows `feat(scope): description` convention
