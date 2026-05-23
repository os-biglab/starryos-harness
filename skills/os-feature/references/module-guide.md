# ArceOS Module Development Guide

## What is a module?

ArceOS modules live in `os/arceos/modules/`. They are `no_std` Rust crates that provide kernel services. Each module has a clear responsibility:

| Module | Responsibility |
|--------|---------------|
| `axhal` | Hardware abstraction (IRQ, timer, paging, percpu) |
| `axruntime` | Boot and initialization sequencing |
| `axtask` | Task (thread) scheduling and management |
| `axmm` | Memory management (virtual address spaces) |
| `axfs` | File system multiplexer (VFS integration) |
| `axfs-ng` | Next-gen file system layer |
| `axnet` | Network stack |
| `axnet-ng` | Next-gen network stack |
| `axdriver` | Device driver framework |
| `axalloc` | Global allocator (heap) |
| `axsync` | Synchronization primitives |
| `axconfig` | Configuration constants |
| `axlog` | Logging macros |
| `axdisplay` | Display / framebuffer |

## Creating a new module

### Directory structure

```
os/arceos/modules/axfoo/
├── Cargo.toml
└── src/
    └── lib.rs
```

### Cargo.toml template

```toml
[package]
name = "axfoo"
version.workspace = true
edition.workspace = true
authors.workspace = true
license.workspace = true
homepage.workspace = true
repository.workspace = true

[features]
default = []
# Add feature flags here

[dependencies]
# Other workspace crates
axhal = { workspace = true }
# axconfig = { workspace = true }

[dev-dependencies]
```

### Register in workspace

In the root `Cargo.toml`, add to `[workspace.members]`:
```toml
"os/arceos/modules/axfoo",
```

And in `[workspace.dependencies]` if other modules need to depend on it:
```toml
axfoo = { path = "os/arceos/modules/axfoo" }
```

### src/lib.rs template

```rust
#![no_std]
#![doc = include_str!("../README.md")]  // optional

extern crate alloc;

use core::sync::atomic::{AtomicBool, Ordering};

// If you need logging
use axlog::{debug, info, warn, error};

/// Module initialization. Called from axruntime during boot.
pub fn init() {
    info!("axfoo: initializing");
    // ...
}
```

## Exposing interfaces via crate_interface

Use `crate_interface` when other modules need to call your module but you don't want a direct dependency:

```rust
// In axfoo/src/lib.rs — declare the interface
use crate_interface::def_interface;

#[def_interface]
pub trait FooInterface {
    fn do_something(arg: usize) -> usize;
}

// In axfoo — provide a default impl (optional, may panic)
struct DefaultImpl;
#[crate_interface::impl_interface]
impl FooInterface for DefaultImpl {
    fn do_something(_arg: usize) -> usize { 0 }
}
```

```rust
// In axbar/src/lib.rs — call the interface without importing axfoo
use crate_interface::call_interface;
let result = call_interface!(FooInterface::do_something(42));
```

## Integration with axruntime

If your module needs initialization at boot, add a call in:
```
os/arceos/modules/axruntime/src/lib.rs
```
Look for the `fn rust_main()` function and add:
```rust
#[cfg(feature = "axfoo")]
axfoo::init();
```

And add the feature flag to `axruntime/Cargo.toml`:
```toml
[features]
axfoo = ["dep:axfoo"]

[dependencies]
axfoo = { workspace = true, optional = true }
```

## Module design rules

1. **Depend on abstractions, not implementations** — prefer `axhal` traits over arch-specific code
2. **Feature-gated** — use `#[cfg(feature = "X")]` to make functionality optional
3. **no_std by default** — only use `std` in dev-dependencies / tests
4. **No circular dependencies** — check with `cargo tree`
5. **Minimal panic surface** — prefer `Result` return types; only `panic!` on truly unrecoverable states
6. **Logging** — use `axlog` macros, not `println!`
7. **Global init** — expose a single `init()` function; avoid lazy_static where avoidable

## Testing

```bash
cargo fmt --package axfoo
cargo xtask clippy --package axfoo

# If package has std-compatible tests, add to whitelist
# scripts/test/std_crates.csv
# Then: cargo xtask test std

# System test via QEMU
cargo xtask arceos build -t riscv64 -a <example-using-axfoo>
cargo xtask arceos qemu  -t riscv64 -a <example-using-axfoo>
```
