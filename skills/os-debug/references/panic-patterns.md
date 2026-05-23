# Common Kernel Panic Patterns

## Arithmetic panics

| Message | Root cause | Fix pattern |
|---------|-----------|-------------|
| `attempt to subtract with overflow` | Unsigned underflow (e.g. `a - b` when `a < b`) | Guard with `if a >= b { a - b } else { 0 }` or use `saturating_sub` |
| `attempt to add with overflow` | Unsigned overflow | Use `checked_add(b).ok_or(EOVERFLOW)?` |
| `attempt to multiply with overflow` | Multiplication overflow | Use `checked_mul` |
| `attempt to divide by zero` | Divisor is zero | Validate divisor before division |
| `index out of bounds: len is N, index is M` | Slice access past end | Validate index or use `.get(i).ok_or(EINVAL)?` |

## Option / Result panics

| Message | Root cause | Fix pattern |
|---------|-----------|-------------|
| `called unwrap() on a None value` | `.unwrap()` on `None` | Replace with `.ok_or(EINVAL)?` or explicit `match` |
| `called expect() on a None value: <msg>` | `.expect()` on `None` | Same as above; the message tells you what was expected |
| `called unwrap() on an Err value: <e>` | `.unwrap()` on `Err` | Use `?` operator or explicit error handling |

## Explicit panics

| Message | Root cause | Fix pattern |
|---------|-----------|-------------|
| `panicked at 'not yet implemented'` | Hit a `todo!()` or `unimplemented!()` | Implement the missing path |
| `panicked at 'unreachable code'` | `unreachable!()` actually reached | Fix the control-flow assumption |
| `panicked at 'assertion failed: <expr>'` | `assert!` check violated | Fix the invariant that was assumed |
| `panicked at 'assertion failed: left == right'` | `assert_eq!` mismatch | Debug the two values, fix logic |

## Memory / alignment panics

| Message | Root cause | Fix pattern |
|---------|-----------|-------------|
| `misaligned pointer dereference` | Raw pointer not aligned to `align_of::<T>()` | Align pointer with `align_up` or use `read_unaligned` |
| `null pointer dereference` | Deref of null raw pointer | Guard: `if ptr.is_null() { return Err(EFAULT); }` |
| `stack overflow` | Deep recursion or large stack frame | Reduce recursion depth; move large buffers to heap |

## Lock / concurrency panics

| Message | Root cause | Fix pattern |
|---------|-----------|-------------|
| `spinlock deadlock detected` (custom) | Same spinlock acquired twice in call chain | Restructure to avoid re-entry; use re-entrant lock if needed |
| `already borrowed: BorrowMutError` | `RefCell` double-borrow | Use `try_borrow_mut()` or redesign ownership |

## How to find the panic site without a backtrace

1. Note the file and line from the panic message
2. If the path is relative, anchor to repo root: `find /workspace -path "*src/foo.rs"`
3. Open the file at the reported line
4. Walk up the call stack mentally: who calls this function with invalid input?

## Enabling backtraces

Add to boot args or env:
```
RUST_BACKTRACE=1
```
Or add to kernel boot config. In StarryOS, the panic handler in `kernel/src/` may need adjustment to print frames.
