---
name: os-debug
description: Debug kernel issues in TGOSKits (ArceOS / StarryOS / Axvisor). Use when investigating kernel panics, page faults, instruction faults, syscall errors, QEMU crashes, memory corruption, deadlocks, or any unexpected OS behaviour. Trigger phrases: debug, panic, crash, page fault, kernel fault, fault, hang, deadlock, segfault, QEMU not responding, kernel log, backtrace, exception, trap, oops.
allowed-tools: "Read Grep Glob Bash LSP"
effort: high
---

# OS Debug

You are debugging a TGOSKits kernel issue. Follow this structured workflow.

## Step 0 — Collect raw evidence first

```bash
# Show current branch and last 10 commits
git log --oneline -10

# Run the target OS and capture all output
cargo xtask starry qemu -t riscv64 2>&1 | tee /tmp/os_run.log
# or for ArceOS:
cargo xtask arceos qemu -t riscv64 -a <app> 2>&1 | tee /tmp/os_run.log
```

Then analyse the log with:
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/parse-qemu-log.py /tmp/os_run.log
```

## Step 1 — Classify the problem

| Output signature | Likely cause | Go to |
|-----------------|-------------|-------|
| `panicked at '...' file:line` | Rust panic (assert, unwrap, overflow) | §A |
| `InstructionPageFault` / `LoadPageFault` / `StorePageFault` | Wrong address dereference | §B |
| `IllegalInstruction` | Alignment, ISA mismatch, bad function ptr | §C |
| Syscall returns `-EFAULT`/`-EINVAL` | Bad user ptr or invalid arg | §D |
| System hangs, no output | Deadlock or infinite loop | §E |
| Build fails `undefined symbol` | Missing feature flag or crate_interface impl | §F |

---

## §A — Rust Panic Analysis

1. Extract the panic message: `grep -n 'panicked at' /tmp/os_run.log`
2. Open the file at the reported line
3. Check: unwrap on None? arithmetic overflow? failed assert?
4. If there is a backtrace, work top-down from frame 0
5. Pay attention to `rust_begin_unwind` → that's the final panic handler

Common patterns (see `references/panic-patterns.md` for full list):
- `attempt to subtract with overflow` — unsigned underflow, check `a >= b` before `a - b`
- `called unwrap() on a None value` — fix with `ok_or(EINVAL)?` instead

---

## §B — Page Fault Analysis

Architecture-specific fault handler locations:

| Arch | Handler |
|------|---------|
| riscv64 | `os/arceos/modules/axhal/src/arch/riscv/trap.rs` |
| aarch64 | `os/arceos/modules/axhal/src/arch/aarch64/trap.rs` |
| x86_64  | `os/arceos/modules/axhal/src/arch/x86_linux/trap.rs` |

StarryOS page-fault path: `kernel/src/mm/` → `components/starry-vm/` → `components/axmm_crates/`

Checklist:
- [ ] Is the faulting address a valid user VA or kernel VA?
- [ ] Was the VMA mapped for the access type (read/write/exec)?
- [ ] Is stack growth needed? Check `SIGSEGV` vs stack VMA limit
- [ ] Are page table TLBs flushed after mapping changes?
- [ ] Is the pointer a raw user ptr that bypassed `UserPtr` validation?

---

## §C — Illegal Instruction

1. Get faulting PC from exception message
2. Disassemble: in GDB `x/10i $pc` or `riscv64-unknown-elf-objdump -d <elf> | grep -A5 <addr>`
3. Check: misaligned access, wrong ISA extension (e.g., `F`/`D` extension not enabled), corrupted function pointer / vtable

---

## §D — Syscall Error Debugging

```bash
# Temporary tracing — add to syscall dispatch, remove before commit
# os/StarryOS/kernel/src/syscall/mod.rs
ax_println!("[TRACE] syscall nr={} args={:?}", nr, args);
```

1. Find the syscall file: `ls os/StarryOS/kernel/src/syscall/`
2. Check arg parsing: length, pointer validity, fd range
3. Check return value encoding (negative errno vs positive result)
4. Common errors — see `references/errno-table.md`

---

## §E — Deadlock / Hang

```bash
# Launch QEMU with monitor console
cargo xtask starry qemu -t riscv64 -- -monitor stdio
# Then in monitor: info registers, info cpus
```

QEMU + GDB workflow (see `references/gdb-workflow.md`):
```bash
# Terminal 1 — start QEMU, wait for GDB
cargo xtask starry qemu -t riscv64 -- -s -S

# Terminal 2 — connect GDB
riscv64-unknown-elf-gdb \
  target/riscv64gc-unknown-none-elf/release/starry \
  -ex "target remote :1234" \
  -ex "set scheduler-locking off" \
  -ex "thread apply all bt"
```

Deadlock indicators:
- Multiple harts all stuck in `spin_lock` / `lock()` with same spinlock address
- Spinlock acquired but `unlock()` never called (check control flow in holding path)

---

## §F — Undefined Symbol / Missing Implementation

```bash
# Find who declares the interface
grep -rn "def_interface\|#\[def_interface\]" os/ components/ --include="*.rs"

# Find who implements it
grep -rn "impl_interface\|#\[impl_interface\]" os/ components/ --include="*.rs"

# Check feature flags
cargo tree -p <crate> --workspace --features <feat>
```

---

## Final checklist before reporting fixed

- [ ] Reproduces the original failure without the fix
- [ ] Fix applied and re-run confirms resolution
- [ ] `cargo fmt --package <crate>` run
- [ ] `cargo xtask clippy --package <crate>` passes
- [ ] No new warnings introduced
