# TGOSKits Module Dependency Map

## StarryOS dependency layers (top = higher-level)

```
┌─────────────────────────────────────────────────────┐
│              StarryOS kernel (os/StarryOS/)          │
│  syscall/ → task/ → file/ → mm/ → pseudofs/         │
└──────────────────────────────┬──────────────────────┘
                               │ depends on
         ┌─────────────────────▼──────────────────────┐
         │           Starry components                 │
         │  starry-process  starry-signal  starry-vm   │
         └──────────────────┬──────────────────────────┘
                            │
         ┌──────────────────▼──────────────────────────┐
         │              ArceOS modules                  │
         │  axhal  axtask  axmm  axfs  axnet  axdriver  │
         └──────────────────┬──────────────────────────┘
                            │
         ┌──────────────────▼──────────────────────────┐
         │           Shared components                  │
         │  axmm_crates  axfs_crates  axdriver_crates  │
         │  axplat_crates  axsched  crate_interface    │
         └─────────────────────────────────────────────┘
```

## Key crate relationships

### Process & thread management

```
starry-process ──depends──► axtask (scheduling)
    └── holds FD table, cred, signal mask
starry-signal  ──depends──► starry-process
    └── signal delivery, sigaction, sigprocmask
axtask         ──depends──► axsched (scheduler algorithm)
               ──depends──► axhal   (context switch, percpu)
```

### Memory management

```
starry-vm      ──depends──► axmm        (address space API)
               ──depends──► axhal       (page table impl)
axmm           ──depends──► axmm_crates (MemorySet, VmAreaStruct)
               ──depends──► axhal       (paging, flush_tlb)
axhal          ──implements──► axplat   (platform-specific HAL)
```

### File system

```
StarryOS file/ ──depends──► axfs        (VFS mount, open, read)
axfs           ──depends──► axfs_crates (VfsNode, VfsOps traits)
               ──depends──► axfs_ramfs  (in-memory fs)
               ──depends──► axfs_devfs  (device pseudo fs)
```

### Network

```
StarryOS net/  ──depends──► axnet       (socket API)
axnet          ──depends──► starry-smoltcp (TCP/IP stack)
               ──depends──► axdriver    (NIC driver)
```

### Driver stack

```
axdriver       ──manages──► axdriver_virtio  (VirtIO block, net)
               ──manages──► axdriver_block   (block devices)
               ──manages──► axdriver_net     (network devices)
axdriver_virtio ──depends──► axhal          (MMIO, DMA)
```

## crate_interface call chains

The `crate_interface` crate provides cross-crate weak linking. Key interfaces:

| `def_interface` (declared in) | `impl_interface` (implemented in) | Used by |
|-------------------------------|-----------------------------------|---------|
| `AxHalInterface` (axhal) | platform crates | axruntime boot |
| `AxTaskInterface` (axtask) | starry-process | scheduler callbacks |
| `PageFaultHandler` (axmm) | StarryOS kernel/mm | page fault resolution |
| Allocator interface (axalloc) | axhal / platform | global heap |

## Feature flag dependency chains

ArceOS features control which modules are compiled in:

```
axruntime features:
  multitask   → enables axtask
  fs          → enables axfs
  net         → enables axnet
  display     → enables axdisplay
  driver-…    → enables specific axdriver sub-features
```

## Folder quick-reference

| Path | Purpose |
|------|---------|
| `os/arceos/modules/axhal/src/arch/riscv/` | riscv64 traps, context switch, paging |
| `os/arceos/modules/axhal/src/arch/aarch64/` | aarch64 traps, context switch, paging |
| `os/arceos/modules/axhal/src/arch/x86_linux/` | x86_64 traps, context switch, paging |
| `os/arceos/modules/axtask/src/` | Task struct, scheduler interface |
| `os/arceos/modules/axruntime/src/` | `rust_main`, init sequence |
| `os/StarryOS/kernel/src/syscall/` | All Linux syscall implementations |
| `os/StarryOS/kernel/src/task/` | Starry task/process management |
| `components/axmm_crates/axmm/src/` | `MemorySet` — one per address space |
| `components/starry-vm/src/` | `VmArea`, mmap/munmap logic |
| `components/starry-process/src/` | `Process`, `Thread`, fd table, creds |
| `components/starry-signal/src/` | Signal queue, delivery, `sigaction` |
| `components/axsched/src/` | Scheduler algorithms (CFS-like, round-robin) |
| `components/axfs_crates/axfs_vfs/src/` | VFS trait definitions |
| `components/axdriver_crates/axdriver/src/` | Driver registry |
| `scripts/axbuild/src/` | xtask build tool implementation |
| `test-suit/starryos/normal/` | Normal QEMU test cases |
| `test-suit/starryos/stress/` | Stress QEMU test cases |
