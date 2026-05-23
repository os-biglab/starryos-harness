---
name: os-review
description: Review OS kernel code in TGOSKits for correctness, safety, and performance. Use when auditing unsafe Rust code, checking concurrency correctness, reviewing memory management, validating syscall implementations, checking platform compatibility, or doing PR review. Trigger phrases: review, audit, check safety, is this correct, code review, PR review, unsafe review, concurrency, memory safety, review this.
allowed-tools: "Read Grep Glob Bash LSP"
effort: high
---

# OS Code Review

You are reviewing kernel code for TGOSKits. Apply the full checklist from `references/review-checklist.md`. Work through each dimension systematically.

## Review Process

1. **Understand the change** — read all modified files, understand the intent
2. **Run the checklist** (below) — go dimension by dimension
3. **Check tests** — ensure the change has test coverage
4. **Verify build hygiene** — fmt and clippy clean?
5. **Summarise findings** — group by severity: Critical / Warning / Suggestion

---

## Dimension 1 — Unsafe Code

For every `unsafe { }` block:

- [ ] Is there a comment explaining why this unsafe is unavoidable?
- [ ] All raw pointer derefs: verified non-null, correctly aligned, within bounds?
- [ ] User-space pointers: only accessed via `UserInPtr` / `UserOutPtr`, never raw deref
- [ ] `transmute`: source and destination types have the same size and alignment? (add `static_assert`)
- [ ] Shared mutable state across threads: is `Send` / `Sync` explicitly justified?
- [ ] No `unsafe` silencing a legitimate compiler warning about a bug

```bash
# Find all unsafe in changed files
grep -n "unsafe" <file> 
```

## Dimension 2 — Concurrency & Locking

- [ ] `SpinLock` / `SpinNoIrq`: held for the shortest possible time, no blocking/sleeping inside
- [ ] `Mutex` (sleepable lock): not used in interrupt context
- [ ] Lock ordering: if code acquires L1 then L2, is this order consistent everywhere globally?
  ```bash
  grep -rn "lock()" os/ components/ --include="*.rs" | grep -A2 -B2 "<lock_name>"
  ```
- [ ] No double-lock: same lock acquired twice in the same call chain?
- [ ] percpu data: accessed only in preempt-disabled / irq-disabled critical section?
- [ ] `Arc` cycles? (would cause memory leak — check for reference cycles in task/process objects)
- [ ] `AtomicXxx` operations: correct ordering (`Acquire`/`Release`/`SeqCst`) for the use case?

## Dimension 3 — Memory Management

- [ ] Allocations: OOM path handled? `alloc()` → checked for null / wrapped in `Result`
- [ ] `mmap`/`munmap`: VMA ranges updated correctly, no overlapping VMAs left behind
- [ ] TLB invalidated after page table changes? (`flush_tlb_all()` or per-page flush)
- [ ] Kernel stack overflow risk: large stack arrays / deep recursion?
- [ ] Device memory: mapped as non-cacheable? (`CachePolicy::Uncached` or equivalent)
- [ ] Physical frames released on all error paths (no frame leaks)

## Dimension 4 — Error Handling

- [ ] No `.unwrap()` / `.expect()` on fallible paths (OK only in test code or provably infallible)
- [ ] Syscall return values follow Linux errno convention (negative for error, non-negative for success)
- [ ] All resources (fd, memory, locks) released on every error path — use RAII or explicit cleanup
- [ ] Error variants are specific (`EINVAL` vs `ENOTSUP` vs `ENOSYS`) — no lazy `EINVAL` for everything
- [ ] `?` operator propagation: does unwinding the stack leave no partial state?

## Dimension 5 — Performance (hot paths only)

- [ ] No heap allocation in syscall fast path / interrupt handler
- [ ] Debug logging behind `#[cfg(feature = "debug")]` or `if_log_enabled!`
- [ ] Interrupt handlers: short as possible; expensive work deferred to task context
- [ ] Cache-line alignment: frequently accessed shared data structured to avoid false sharing?
- [ ] `memcpy` / `memset` of large user buffers: done with proper chunking?

## Dimension 6 — Platform Compatibility

- [ ] Arch-specific code in `arch/<arch>/` subdirectory or `#[cfg(target_arch = "...")]` block
- [ ] No hardcoded constants for page size, physical address range, interrupt numbers
  ```bash
  grep -rn "4096\|0x1000\b" <file>   # suspect magic numbers
  ```
- [ ] New syscall registered for all relevant architectures (syscall numbers differ per arch)
- [ ] Tested on at least riscv64; aarch64 and x86_64 if touching shared code

## Dimension 7 — API & Interface Correctness

- [ ] Public `trait` methods: are pre-conditions / post-conditions documented?
- [ ] `crate_interface` `#[def_interface]`: is the default impl (if any) sound?
- [ ] FFI / C ABI functions: correct calling convention, no Rust types that don't cross ABI safely
- [ ] `no_std` compatibility: no std-only types in shared components

## Dimension 8 — Test Coverage

- [ ] Is the changed code path exercised by an existing test?
- [ ] If new syscall: is there a `test-suit/starryos/normal/<name>/` case?
- [ ] If new ArceOS module: does it appear in `scripts/test/clippy_crates.csv`?
- [ ] Edge cases covered: empty input, max-size input, null pointers, invalid fds

---

## Quick commands

```bash
# Check formatting
cargo fmt --check --package <crate>

# Check clippy
cargo xtask clippy --package <crate>

# Run affected tests
cargo xtask starry test qemu -t riscv64 -c <case>
cargo xtask arceos test qemu --target riscv64gc-unknown-none-elf

# Find all TODO / FIXME / HACK / SAFETY comments
grep -rn "TODO\|FIXME\|HACK\|SAFETY\|UNSOUND" <file>
```

---

## Severity guide

| Level | Meaning | Action |
|-------|---------|--------|
| **Critical** | Can cause UB, data corruption, security hole, kernel panic | Must fix before merge |
| **Warning** | Logic error, resource leak, incorrect errno | Should fix before merge |
| **Suggestion** | Style, naming, minor improvement | Optional / NIT |
