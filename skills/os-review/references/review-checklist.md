# OS Code Review Checklist

Use this checklist for every kernel code review. Mark each item ✓ (pass), ✗ (fail — note the issue), or N/A.

---

## Pre-review: understand the change

- [ ] Read the PR description / commit message — does the stated goal match the code?
- [ ] Identify all modified files and their purpose
- [ ] Understand the expected before/after behaviour
- [ ] Check if this touches a hot path (syscall fast path, interrupt handler, scheduler)

---

## 1. Unsafe code

For each `unsafe { }` block:

- [ ] Is there a comment explaining why unsafe is unavoidable? (one line max)
- [ ] Raw pointer: verified non-null before deref?
- [ ] Raw pointer: correctly aligned for type `T` (`ptr as usize % align_of::<T>() == 0`)?
- [ ] Raw pointer: points within a valid allocation (not dangling)?
- [ ] User-space pointer: goes through `UserInPtr`/`UserOutPtr`, not direct deref?
- [ ] `transmute`: source and destination have same size and alignment? `static_assert` present?
- [ ] Cross-thread raw pointer sharing: `Send`/`Sync` justification present?
- [ ] No `unsafe` block added just to silence a compiler error about a real bug?

---

## 2. Concurrency and locking

- [ ] `SpinLock` held for shortest possible critical section (no I/O, no sleeping)?
- [ ] `SpinNoIrq` (or `IrqSave`) used when the same lock is acquired in interrupt context?
- [ ] `Mutex` (sleepable) NOT used in interrupt or NMI context?
- [ ] Lock acquisition order: if A→B exists elsewhere, no new B→A path introduced?
- [ ] Double-lock: same lock never acquired twice in the same call chain?
- [ ] percpu data: accessed only with preemption/interrupts disabled?
- [ ] `Arc` cycles: no new reference cycles in process / task / file objects?
- [ ] Atomic operations: ordering (`Acquire`/`Release`/`SeqCst`) appropriate for use case?
- [ ] All shared state modifications visible to other cores (fence/barrier present if needed)?

---

## 3. Memory management

- [ ] Allocation failure: every `alloc()` / `Box::new()` / `Vec::new()` path handles OOM?
- [ ] mmap/munmap: VMA ranges correctly updated, no overlapping VMAs?
- [ ] After page table change: TLB flushed (`flush_tlb_all()` or per-page)?
- [ ] Kernel stack: no large (>4KB) stack-allocated arrays or deep recursion?
- [ ] Device / DMA memory: mapped as non-cacheable?
- [ ] Physical frame leak: all allocated frames freed on every error path?
- [ ] After `munmap` or process exit: all PTEs cleared and physical frames returned?

---

## 4. Error handling

- [ ] No `.unwrap()` on fallible operations outside of test code or provably infallible calls?
- [ ] No `.expect()` in production paths (kernel will panic on unexpected input)?
- [ ] Syscall return values follow Linux errno convention (negative = error)?
- [ ] Specific errno chosen (not lazy `EINVAL` for everything)?
- [ ] All resources (fd, memory, lock) released on every error path?
- [ ] Error propagation with `?` does not skip cleanup (RAII used or explicit drop)?
- [ ] Partial state not left behind when an error occurs mid-operation?

---

## 5. Performance (hot paths only — skip for init code)

- [ ] No heap allocation in syscall fast path or interrupt handler?
- [ ] Debug / trace logging gated behind `#[cfg(feature = "debug")]` or `if_log_enabled!`?
- [ ] Interrupt handler: exits as quickly as possible, defers work to task?
- [ ] No unnecessary `memcpy` of large kernel buffers in hot path?
- [ ] Cache-line alignment: frequently accessed shared data avoids false sharing?
- [ ] Sleeping lock not used where a spinlock (or lock-free) would suffice?

---

## 6. Platform compatibility

- [ ] Arch-specific code in `arch/<arch>/` subdirectory or `#[cfg(target_arch = "...")]` block?
- [ ] No hardcoded constants for page size, physical address range, interrupt numbers?
  - Page size: use `PAGE_SIZE` from `axconfig` or `axhal`
  - Address ranges: use platform config, not `0x8000_0000` literals
- [ ] New syscall: number registered correctly for all supported architectures?
  - riscv64 and aarch64 share the generic Linux table; x86_64 is different
- [ ] Build tested on at least riscv64; multi-arch if touching shared code?

---

## 7. API and interface correctness

- [ ] Public trait methods: invariants and pre/post-conditions documented?
- [ ] `crate_interface` `#[def_interface]`: default impl (if any) is sound and not a silent no-op?
- [ ] FFI / `extern "C"` functions: correct calling convention, no non-ABI-safe Rust types?
- [ ] `no_std` compatibility: no `std`-only types in shared components?
- [ ] Deprecated or removed APIs not introduced?

---

## 8. Test coverage

- [ ] Changed code path exercised by an existing test?
- [ ] New syscall: test case in `test-suit/starryos/normal/<name>/`?
- [ ] New ArceOS module/crate: added to `scripts/test/clippy_crates.csv`?
- [ ] Edge cases tested: empty input, max-size input, null pointer, invalid fd?
- [ ] Existing tests still pass: `cargo xtask starry test qemu -t riscv64`?

---

## 9. Code quality

- [ ] `cargo fmt` applied (no formatting diff)?
- [ ] `cargo xtask clippy --package <crate>` passes with zero warnings?
- [ ] No `#[allow(...)]` added to suppress a real warning (fix the root cause)?
- [ ] Comments explain WHY, not WHAT (identifiers already explain what)?
- [ ] No dead code, commented-out code, or debug `println!` left in?
- [ ] PR title follows `type(scope): description` Conventional Commits format?

---

## Severity guide for findings

| Label | When to use | Merge impact |
|-------|------------|--------------|
| **Critical** | UB, memory corruption, security hole, kernel panic trigger | Block merge |
| **Warning** | Logic error, resource leak, wrong errno, test missing | Should fix |
| **NIT** | Style, naming, minor improvement | Optional |
