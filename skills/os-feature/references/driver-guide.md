# Device Driver Development Guide

## Driver framework overview

```
components/axdriver_crates/
├── axdriver/           # Driver registry and probing framework
├── axdriver_base/      # Base traits and device types
├── axdriver_block/     # Block device trait (BlockDriverOps)
├── axdriver_net/       # Network device trait (NetDriverOps)
├── axdriver_display/   # Display device trait (DisplayDriverOps)
├── axdriver_input/     # Input device trait (InputEventOps)
└── axdriver_virtio/    # VirtIO driver implementations
```

## Step 1 — Identify the device class

| Device type | Trait to implement | Registry location |
|-------------|-------------------|-------------------|
| Block (disk) | `BlockDriverOps` | `axdriver/src/drivers.rs` |
| Network (NIC) | `NetDriverOps` | `axdriver/src/drivers.rs` |
| Display / GPU | `DisplayDriverOps` | `axdriver/src/drivers.rs` |
| Input (keyboard, mouse) | `InputEventOps` | `axdriver/src/drivers.rs` |
| UART / serial | Custom | Platform-specific in `axhal` |

## Step 2 — Create the driver crate

```
components/axdriver_crates/axdriver_myfoo/
├── Cargo.toml
└── src/
    └── lib.rs
```

### Cargo.toml

```toml
[package]
name = "axdriver_myfoo"
version.workspace = true
edition.workspace = true
license.workspace = true

[dependencies]
axdriver_base = { workspace = true }
axdriver_block = { workspace = true }     # if block driver
# Add platform-specific deps as needed
log = { workspace = true }

[features]
default = []
```

## Step 3 — Implement the trait

### Block driver example

```rust
#![no_std]
extern crate alloc;

use axdriver_base::{BaseDriverOps, DevError, DevResult, DeviceType};
use axdriver_block::BlockDriverOps;

pub struct MyFooDevice {
    // device-specific state
}

impl BaseDriverOps for MyFooDevice {
    fn device_name(&self) -> &str { "myfoo" }
    fn device_type(&self) -> DeviceType { DeviceType::Block }
}

impl BlockDriverOps for MyFooDevice {
    fn num_blocks(&self) -> u64 { /* total blocks */ }
    fn block_size(&self) -> usize { 512 }

    fn read_block(&mut self, block_id: u64, buf: &mut [u8]) -> DevResult {
        // Read block_id into buf
        Ok(())
    }

    fn write_block(&mut self, block_id: u64, buf: &[u8]) -> DevResult {
        // Write buf to block_id
        Ok(())
    }

    fn flush(&mut self) -> DevResult { Ok(()) }
}
```

## Step 4 — Register the driver

In `os/arceos/modules/axdriver/src/` (exact file may be `drivers.rs`, `lib.rs`, or arch-specific):

```rust
#[cfg(feature = "myfoo")]
{
    use axdriver_myfoo::MyFooDevice;
    let dev = MyFooDevice::try_new().expect("failed to init myfoo");
    // Register with the appropriate registry
    axdriver::register_block_driver(dev);
}
```

Add the feature to `axdriver/Cargo.toml`:
```toml
[features]
myfoo = ["dep:axdriver_myfoo"]

[dependencies]
axdriver_myfoo = { workspace = true, optional = true }
```

## Step 5 — Add to workspace

Root `Cargo.toml`:
```toml
[workspace.members]
# ...
"components/axdriver_crates/axdriver_myfoo",

[workspace.dependencies]
axdriver_myfoo = { path = "components/axdriver_crates/axdriver_myfoo" }
```

## Step 6 — MMIO / DMA

For hardware MMIO-mapped devices:

```rust
use core::ptr::{read_volatile, write_volatile};

unsafe {
    let reg = 0x1000_0000 as *mut u32;
    let val = read_volatile(reg);
    write_volatile(reg, val | 0x1);
}
```

- Map MMIO region in `axhal` platform code before the driver uses it
- Use `DeviceMemory` or `PhysAddr` types from `axhal`/`axmm` for safe wrappers

For DMA:
- Allocate coherent DMA memory with `alloc_coherent()` (platform-specific)
- Ensure non-cacheable mapping for DMA buffers
- Memory barriers (`fence`) required before/after DMA operations on riscv

## Step 7 — Platform detection / probing

For QEMU virt platform, devices are detected via device tree (DTB):
```
components/axplat_crates/platforms/qemu-virt-*/
```

Add a probe entry in the platform's device probe code to instantiate your driver when the compatible string matches.

## Testing

```bash
cargo fmt --package axdriver_myfoo
cargo xtask clippy --package axdriver_myfoo
# Build an ArceOS app that uses the driver feature
cargo xtask arceos build -t riscv64 -a <app> --features axdriver/myfoo
```
