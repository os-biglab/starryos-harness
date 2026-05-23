# StarryOS Syscall Implementation Guide

## File layout

```
os/StarryOS/kernel/src/syscall/
├── mod.rs          # Dispatch table + SyscallError type
├── fs.rs           # File system calls (open, read, write, stat, …)
├── mm.rs           # Memory calls (mmap, munmap, brk, mprotect, …)
├── task.rs         # Process/thread (clone, fork, execve, wait4, exit, …)
├── signal.rs       # Signal calls (kill, sigaction, sigprocmask, …)
├── net.rs          # Network calls (socket, bind, connect, send, recv, …)
├── time.rs         # Time calls (clock_gettime, nanosleep, …)
├── misc.rs         # Miscellaneous (uname, getrlimit, prctl, …)
└── io.rs           # I/O multiplexing (epoll, select, poll, …)
```

## SyscallResult type

```rust
pub type SyscallResult = Result<isize, SyscallError>;
// Ok(n)   → returns n to userspace
// Err(e)  → returns -(e as isize) to userspace
```

## User pointer types

| Type | Direction | Use for |
|------|-----------|---------|
| `UserInPtr<T>` | User → Kernel (read) | Reading struct/array from user |
| `UserOutPtr<T>` | Kernel → User (write) | Writing struct/array to user |
| `UserInOutPtr<T>` | Both | `sockaddr` length params, etc. |

### Reading a user struct

```rust
use crate::utils::user_ptr::UserInPtr;

pub fn sys_example(user_ptr: usize, len: usize) -> SyscallResult {
    if len == 0 || len > MAX_LEN { return Err(SyscallError::EINVAL); }
    let ptr = UserInPtr::<u8>::new(user_ptr as *const u8);
    let data: Vec<u8> = ptr.read_array(len)?;  // EFAULT on invalid ptr
    // ... use data
    Ok(0)
}
```

### Reading a single struct

```rust
let ptr = UserInPtr::<SomeStruct>::new(user_ptr as *const SomeStruct);
let s: SomeStruct = ptr.read()?;
```

### Writing to user

```rust
let ptr = UserOutPtr::<u64>::new(user_ptr as *mut u64);
ptr.write(result_value)?;
```

### String from user

```rust
use crate::utils::user_ptr::UserInPtr;
let path_ptr = UserInPtr::<u8>::new(path as *const u8);
let path_str: String = path_ptr.read_cstr()?;  // reads until NUL, returns Err(EFAULT) on bad ptr
```

## Dispatch table pattern

In `mod.rs`, the dispatch looks like:

```rust
pub fn syscall(nr: usize, args: [usize; 6]) -> isize {
    let result: SyscallResult = match nr {
        SYS_READ        => sys_read(args[0] as i32, args[1], args[2]),
        SYS_WRITE       => sys_write(args[0] as i32, args[1], args[2]),
        // ... your new syscall:
        SYS_GETXATTR    => sys_getxattr(args[0], args[1], args[2], args[3]),
        _               => {
            warn!("[syscall] unimplemented syscall: {}", nr);
            Err(SyscallError::ENOSYS)
        }
    };
    syscall_result_to_isize(result)
}
```

## Syscall numbers by architecture

Syscall numbers differ per arch. In StarryOS they are typically defined as constants:
```rust
// riscv64 uses the same table as generic Linux (aarch64 table)
pub const SYS_READ:    usize = 63;
pub const SYS_WRITE:   usize = 64;
pub const SYS_MMAP:    usize = 222;
// ...
```

For x86_64 vs aarch64/riscv64, there may be separate dispatch files or `#[cfg(target_arch)]` guards.

## Common patterns

### Getting a file from fd

```rust
use crate::task::current_process;

let file = current_process()
    .fd_table()
    .get(fd as usize)
    .ok_or(SyscallError::EBADF)?;
```

### Allocating a new fd

```rust
let fd = current_process()
    .fd_table()
    .alloc(file_object)?;
Ok(fd as isize)
```

### Getting current task / process

```rust
let task = current_task();          // current thread
let proc = current_process();       // current process (may differ from task)
```

### Handling optional user pointer (NULL = "not provided")

```rust
pub fn sys_something(ptr: usize, len: usize) -> SyscallResult {
    if ptr == 0 {
        // NULL ptr means "use default" for many syscalls
        return Ok(0);
    }
    let uptr = UserInPtr::<u8>::new(ptr as *const u8);
    let data = uptr.read_array(len)?;
    // ...
}
```

## Testing your new syscall

1. Write a C or Rust test program that calls the syscall
2. Compile for the target arch
3. Put it in `test-suit/starryos/normal/<name>/`
4. Add `qemu-riscv64.toml` with `success_regex` and `fail_regex`
5. Run: `cargo xtask starry test qemu -t riscv64 -c <name>`
