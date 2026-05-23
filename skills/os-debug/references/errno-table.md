# Linux errno Quick Reference

Values as returned by StarryOS syscalls (negative of the constant, e.g. `-EINVAL` = `-22`).

## Most common in kernel development

| errno | Value | Name | Meaning | When to use |
|-------|-------|------|---------|-------------|
| 1 | EPERM | Operation not permitted | Capability / privilege check failed | setuid, raw socket, device access |
| 2 | ENOENT | No such file or directory | Path does not exist | open, stat, unlink on missing path |
| 9 | EBADF | Bad file descriptor | fd not open or wrong type | Invalid fd passed to read/write/ioctl |
| 11 | EAGAIN / EWOULDBLOCK | Resource temporarily unavailable | Non-blocking op would block | O_NONBLOCK socket/pipe read |
| 12 | ENOMEM | Out of memory | Kernel allocation failed | mmap, brk, kmalloc |
| 13 | EACCES | Permission denied | File mode check failed | open with wrong mode |
| 14 | EFAULT | Bad address | User pointer unmapped or invalid | Any syscall with user pointer arg |
| 16 | EBUSY | Device or resource busy | Resource locked | mount, close on busy device |
| 17 | EEXIST | File exists | O_CREAT|O_EXCL on existing file | create-only open |
| 19 | ENODEV | No such device | Device not registered | open on missing /dev node |
| 20 | ENOTDIR | Not a directory | Path component is a file | openat with file as dir |
| 21 | EISDIR | Is a directory | Operation not valid on dir | read/write on directory fd |
| 22 | EINVAL | Invalid argument | Bad argument value or combination | Most validation failures |
| 24 | EMFILE | Too many open files | Per-process fd limit reached | open when fd table full |
| 25 | ENOTTY | Inappropriate ioctl | ioctl on non-terminal | ioctl on wrong fd type |
| 28 | ENOSPC | No space left on device | FS full | write when disk full |
| 32 | EPIPE | Broken pipe | Write to pipe/socket with no reader | SIGPIPE or write to closed pipe |
| 35 | EDEADLK | Resource deadlock avoided | Detected lock cycle | fcntl record locks |
| 36 | ENAMETOOLONG | Filename too long | Path exceeds PATH_MAX | Long path passed to open/stat |
| 38 | ENOSYS | Function not implemented | Syscall not supported | Unimplemented syscall |
| 40 | ELOOP | Too many symbolic links | symlink loop | Path resolution with circular symlinks |
| 95 | EOPNOTSUPP | Operation not supported | Valid op, not supported for this fd type | e.g. sendfile on non-regular file |
| 110 | ETIMEDOUT | Connection timed out | Network / wait timeout | socket connect, futex timeout |
| 111 | ECONNREFUSED | Connection refused | Remote port closed | connect to closed port |

## Syscall return value convention

```
Negative errno  →  error:   return Err(SyscallError::EINVAL)
Zero            →  success with no value
Positive        →  success with value (fd number, bytes written, etc.)
```

In StarryOS, `SyscallResult = Result<isize, SyscallError>`.
The glue layer converts `Err(e)` → `-(e as isize)`.

## Choosing the right errno

```
Invalid argument value or range  →  EINVAL
Invalid user pointer             →  EFAULT
Operation not implemented        →  ENOSYS  (use sparingly; prefer EOPNOTSUPP)
Permission denied (capability)   →  EPERM
Permission denied (mode bits)    →  EACCES
fd is not valid                  →  EBADF
Alloc failed                     →  ENOMEM
Path not found                   →  ENOENT
```
