#!/usr/bin/env python3
"""
ABI checker: compares StarryOS syscall argument counts against Linux SYSCALL_DEFINE arities.
Reports mismatches with Linux signatures.

Usage:
    python3 abi-check.py <starry-syscall-mod-rs>
    python3 abi-check.py os/StarryOS/kernel/src/syscall/mod.rs
"""

import sys
import re
from pathlib import Path


# StarryOS syscall dispatch pattern: number => function(args[0], args[1], ...)
STARRY_DISPATCH = re.compile(
    r'(\d+)\s*/\*\s*SYS_(\w+)\s*\*/\s*=>\s*(\w+)\(([^)]*)\)'
)

# Also match: number => function(args[0], args[1], ...)
STARRY_DISPATCH_ALT = re.compile(
    r'(\d+)\s*=>\s*(\w+)\(([^)]*)\)'
)


# Linux syscall arities (common subset, verifiable at elixir.bootlin.com/linux/v6.12)
# Format: "SYSCALL_NAME": (arity, linux_signature)
LINUX_ARITIES = {
    "READ": (3, "sys_read(unsigned int fd, char __user *buf, size_t count)"),
    "WRITE": (3, "sys_write(unsigned int fd, const char __user *buf, size_t count)"),
    "OPEN": (3, "sys_open(const char __user *filename, int flags, umode_t mode)"),
    "CLOSE": (1, "sys_close(unsigned int fd)"),
    "STAT": (2, "sys_stat(const char __user *filename, struct stat __user *statbuf)"),
    "FSTAT": (2, "sys_fstat(unsigned int fd, struct stat __user *statbuf)"),
    "LSTAT": (2, "sys_lstat(const char __user *filename, struct stat __user *statbuf)"),
    "POLL": (3, "sys_poll(struct pollfd __user *ufds, unsigned int nfds, int timeout)"),
    "LSEEK": (3, "sys_lseek(unsigned int fd, off_t offset, unsigned int whence)"),
    "MMAP": (6, "sys_mmap(unsigned long addr, unsigned long len, unsigned long prot, unsigned long flags, unsigned long fd, unsigned long pgoff)"),
    "MPROTECT": (3, "sys_mprotect(unsigned long start, size_t len, unsigned long prot)"),
    "MUNMAP": (2, "sys_munmap(unsigned long start, size_t length)"),
    "BRK": (1, "sys_brk(unsigned long brk)"),
    "IOCTL": (3, "sys_ioctl(unsigned int fd, unsigned int cmd, unsigned long arg)"),
    "PREAD64": (4, "sys_pread64(unsigned int fd, char __user *buf, size_t count, loff_t pos)"),
    "PWRITE64": (4, "sys_pwrite64(unsigned int fd, const char __user *buf, size_t count, loff_t pos)"),
    "READV": (3, "sys_readv(unsigned long fd, const struct iovec __user *vec, unsigned long vlen)"),
    "WRITEV": (3, "sys_writev(unsigned long fd, const struct iovec __user *vec, unsigned long vlen)"),
    "SCHED_YIELD": (0, "sys_sched_yield()"),
    "MREMAP": (5, "sys_mremap(unsigned long addr, unsigned long old_len, unsigned long new_len, unsigned long flags, unsigned long new_addr)"),
    "MSYNC": (3, "sys_msync(unsigned long start, size_t length, int flags)"),
    "MINCORE": (3, "sys_mincore(unsigned long start, size_t length, unsigned char __user *vec)"),
    "MADVISE": (3, "sys_madvise(unsigned long start, size_t length, int behavior)"),
    "SHMGET": (3, "sys_shmget(key_t key, size_t size, int shmflg)"),
    "SHMAT": (3, "sys_shmat(int shmid, char __user *shmaddr, int shmflg)"),
    "SHMCTL": (3, "sys_shmctl(int shmid, int cmd, struct shmid_ds __user *buf)"),
    "DUP": (1, "sys_dup(unsigned int fildes)"),
    "DUP2": (2, "sys_dup2(unsigned int oldfd, unsigned int newfd)"),
    "DUP3": (3, "sys_dup3(unsigned int oldfd, unsigned int newfd, int flags)"),
    "NANOSLEEP": (2, "sys_nanosleep(struct timespec __user *rqtp, struct timespec __user *rmtp)"),
    "GETITIMER": (2, "sys_getitimer(int which, struct itimerval __user *value)"),
    "ALARM": (1, "sys_alarm(unsigned int seconds)"),
    "SETITIMER": (3, "sys_setitimer(int which, struct itimerval __user *value, struct itimerval __user *ovalue)"),
    "GETPID": (0, "sys_getpid()"),
    "GETPPID": (0, "sys_getppid()"),
    "GETUID": (0, "sys_getuid()"),
    "GETEUID": (0, "sys_geteuid()"),
    "GETGID": (0, "sys_getgid()"),
    "GETEGID": (0, "sys_getegid()"),
    "GETTID": (0, "sys_gettid()"),
    "CLONE": (5, "sys_clone(unsigned long, unsigned long, int __user *, int __user *, unsigned long)"),
    "FORK": (0, "sys_fork()"),
    "VFORK": (0, "sys_vfork()"),
    "EXECVE": (3, "sys_execve(const char __user *filename, const char __user *const __user *argv, const char __user *const __user *envp)"),
    "EXIT": (1, "sys_exit(int error_code)"),
    "EXIT_GROUP": (1, "sys_exit_group(int error_code)"),
    "WAIT4": (4, "sys_wait4(pid_t pid, int __user *stat_addr, int options, struct rusage __user *ru)"),
    "KILL": (2, "sys_kill(pid_t pid, int sig)"),
    "TKILL": (2, "sys_tkill(int pid, int sig)"),
    "TGKILL": (3, "sys_tgkill(pid_t tgid, int pid, int sig)"),
    "RT_SIGACTION": (4, "sys_rt_sigaction(int, const struct sigaction __user *, struct sigaction __user *, size_t)"),
    "RT_SIGPROCMASK": (4, "sys_rt_sigprocmask(int how, sigset_t __user *set, sigset_t __user *oset, size_t sigsetsize)"),
    "RT_SIGRETURN": (0, "sys_rt_sigreturn()"),
    "SOCKET": (3, "sys_socket(int, int, int)"),
    "CONNECT": (3, "sys_connect(int, struct sockaddr __user *, int)"),
    "ACCEPT": (3, "sys_accept(int, struct sockaddr __user *, int __user *)"),
    "SENDTO": (6, "sys_sendto(int, void __user *, size_t, unsigned int, struct sockaddr __user *, int)"),
    "RECVFROM": (6, "sys_recvfrom(int, void __user *, size_t, unsigned int, struct sockaddr __user *, int __user *)"),
    "BIND": (3, "sys_bind(int, struct sockaddr __user *, int)"),
    "LISTEN": (2, "sys_listen(int, int)"),
    "GETSOCKNAME": (3, "sys_getsockname(int, struct sockaddr __user *, int __user *)"),
    "GETPEERNAME": (3, "sys_getpeername(int, struct sockaddr __user *, int __user *)"),
    "SOCKETPAIR": (4, "sys_socketpair(int, int, int, int __user *)"),
    "SETSOCKOPT": (5, "sys_setsockopt(int fd, int level, int optname, char __user *optval, int optlen)"),
    "GETSOCKOPT": (5, "sys_getsockopt(int fd, int level, int optname, char __user *optval, int __user *optlen)"),
    "EPOLL_CREATE": (1, "sys_epoll_create(int size)"),
    "EPOLL_CREATE1": (1, "sys_epoll_create1(int flags)"),
    "EPOLL_CTL": (4, "sys_epoll_ctl(int epfd, int op, int fd, struct epoll_event __user *event)"),
    "EPOLL_WAIT": (4, "sys_epoll_wait(int epfd, struct epoll_event __user *events, int maxevents, int timeout)"),
    "PIPE": (1, "sys_pipe(int __user *fildes)"),
    "PIPE2": (2, "sys_pipe2(int __user *fildes, int flags)"),
    "SELECT": (5, "sys_select(int n, fd_set __user *inp, fd_set __user *outp, fd_set __user *exp, struct timeval __user *tvp)"),
    "PSELECT6": (6, "sys_pselect6(int, fd_set __user *, fd_set __user *, fd_set __user *, struct timespec __user *, void __user *)"),
    "GETCWD": (2, "sys_getcwd(char __user *buf, unsigned long size)"),
    "CHDIR": (1, "sys_chdir(const char __user *filename)"),
    "FCHDIR": (1, "sys_fchdir(unsigned int fd)"),
    "MKDIR": (2, "sys_mkdir(const char __user *pathname, umode_t mode)"),
    "RMDIR": (1, "sys_rmdir(const char __user *pathname)"),
    "UNLINK": (1, "sys_unlink(const char __user *pathname)"),
    "LINK": (2, "sys_link(const char __user *oldname, const char __user *newname)"),
    "RENAME": (2, "sys_rename(const char __user *oldname, const char __user *newname)"),
    "GETDENTS64": (3, "sys_getdents64(unsigned int fd, struct linux_dirent64 __user *dirent, unsigned int count)"),
    "READLINK": (3, "sys_readlink(const char __user *path, char __user *buf, int bufsiz)"),
    "SYMLINK": (2, "sys_symlink(const char __user *old, const char __user *new)"),
    "CHMOD": (2, "sys_chmod(const char __user *filename, umode_t mode)"),
    "FCHMOD": (2, "sys_fchmod(unsigned int fd, umode_t mode)"),
    "CHOWN": (3, "sys_chown(const char __user *filename, uid_t user, gid_t group)"),
    "FCHOWN": (3, "sys_fchown(unsigned int fd, uid_t user, gid_t group)"),
    "UMASK": (1, "sys_umask(int mask)"),
    "GETTIMEOFDAY": (2, "sys_gettimeofday(struct timeval __user *tv, struct timezone __user *tz)"),
    "CLOCK_GETTIME": (2, "sys_clock_gettime(clockid_t which_clock, struct timespec __user *tp)"),
    "CLOCK_SETTIME": (2, "sys_clock_settime(clockid_t which_clock, const struct timespec __user *tp)"),
    "CLOCK_GETRES": (2, "sys_clock_getres(clockid_t which_clock, struct timespec __user *tp)"),
    "FUTEX": (6, "sys_futex(u32 __user *uaddr, int op, u32 val, struct timespec __user *utime, u32 __user *uaddr2, u32 val3)"),
    "OPENAT": (4, "sys_openat(int dfd, const char __user *filename, int flags, umode_t mode)"),
    "MKDIRAT": (3, "sys_mkdirat(int dfd, const char __user *pathname, umode_t mode)"),
    "NEWFSTATAT": (4, "sys_newfstatat(int dfd, const char __user *filename, struct stat __user *statbuf, int flag)"),
    "UNLINKAT": (3, "sys_unlinkat(int dfd, const char __user *pathname, int flag)"),
    "RENAMEAT": (4, "sys_renameat(int olddfd, const char __user *oldname, int newdfd, const char __user *newname)"),
    "RENAMEAT2": (5, "sys_renameat2(int olddfd, const char __user *oldname, int newdfd, const char __user *newname, unsigned int flags)"),
    "READLINKAT": (4, "sys_readlinkat(int dfd, const char __user *pathname, char __user *buf, int bufsiz)"),
    "SYMLINKAT": (3, "sys_symlinkat(const char __user *oldname, int newdfd, const char __user *newname)"),
    "FACCESSAT": (3, "sys_faccessat(int dfd, const char __user *filename, int mode)"),
    "FACCESSAT2": (4, "sys_faccessat2(int dfd, const char __user *filename, int mode, int flags)"),
    "PREAD64": (4, "sys_pread64(unsigned int fd, char __user *buf, size_t count, loff_t pos)"),
    "PWRITE64": (4, "sys_pwrite64(unsigned int fd, const char __user *buf, size_t count, loff_t pos)"),
    "GETXATTR": (4, "sys_getxattr(const char __user *path, const char __user *name, void __user *value, size_t size)"),
    "LGETXATTR": (4, "sys_lgetxattr(const char __user *path, const char __user *name, void __user *value, size_t size)"),
    "FGETXATTR": (4, "sys_fgetxattr(int fd, const char __user *name, void __user *value, size_t size)"),
    "SETXATTR": (5, "sys_setxattr(const char __user *path, const char __user *name, const void __user *value, size_t size, int flags)"),
    "LSETXATTR": (5, "sys_lsetxattr(const char __user *path, const char __user *name, const void __user *value, size_t size, int flags)"),
    "FSETXATTR": (5, "sys_fsetxattr(int fd, const char __user *name, const void __user *value, size_t size, int flags)"),
    "LISTXATTR": (3, "sys_listxattr(const char __user *path, char __user *list, size_t size)"),
    "LLISTXATTR": (3, "sys_llistxattr(const char __user *path, char __user *list, size_t size)"),
    "FLISTXATTR": (3, "sys_flistxattr(int fd, char __user *list, size_t size)"),
    "REMOVEXATTR": (2, "sys_removexattr(const char __user *path, const char __user *name)"),
    "LREMOVEXATTR": (2, "sys_lremovexattr(const char __user *path, const char __user *name)"),
    "FREMOVEXATTR": (2, "sys_fremovexattr(int fd, const char __user *name)"),
}


def parse_starry_syscalls(mod_rs_path):
    """Parse StarryOS syscall dispatch table."""
    content = Path(mod_rs_path).read_text()
    syscalls = {}

    for m in STARRY_DISPATCH.finditer(content):
        nr = int(m.group(1))
        name = m.group(2)
        func = m.group(3)
        args_str = m.group(4).strip()
        arity = len([a for a in args_str.split(",") if a.strip()]) if args_str else 0
        syscalls[name] = {"nr": nr, "func": func, "arity": arity}

    for m in STARRY_DISPATCH_ALT.finditer(content):
        nr = int(m.group(1))
        func = m.group(2)
        args_str = m.group(3).strip()
        arity = len([a for a in args_str.split(",") if a.strip()]) if args_str else 0
        # Try to extract name from func (e.g., sys_read -> READ)
        if func.startswith("sys_"):
            name = func[4:].upper()
            if name not in syscalls:
                syscalls[name] = {"nr": nr, "func": func, "arity": arity}

    return syscalls


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 abi-check.py <starry-syscall-mod-rs>")
        sys.exit(1)

    mod_rs = Path(sys.argv[1])
    if not mod_rs.exists():
        print(f"Error: {mod_rs} not found")
        sys.exit(1)

    starry = parse_starry_syscalls(mod_rs)

    mismatches = []
    matches = 0
    unknown = []

    for name, info in sorted(starry.items()):
        if name in LINUX_ARITIES:
            linux_arity, linux_sig = LINUX_ARITIES[name]
            if info["arity"] != linux_arity:
                mismatches.append({
                    "name": name,
                    "starry_arity": info["arity"],
                    "linux_arity": linux_arity,
                    "linux_sig": linux_sig,
                    "starry_func": info["func"],
                })
            else:
                matches += 1
        else:
            unknown.append(name)

    # Report
    print(f"## ABI Check Results\n")
    print(f"StarryOS syscalls: {len(starry)}")
    print(f"Matched against Linux: {matches}")
    print(f"Mismatches: {len(mismatches)}")
    print(f"Not in reference table: {len(unknown)}")
    print()

    if mismatches:
        print("### Argument Count Mismatches\n")
        print("| Syscall | StarryOS | Linux | Linux Signature |")
        print("|---------|----------|-------|-----------------|")
        for m in mismatches:
            print(f"| {m['name']} | {m['starry_arity']} | {m['linux_arity']} | `{m['linux_sig']}` |")
        print()
        sys.exit(1)

    if unknown:
        print(f"### Unknown syscalls (not in reference): {', '.join(unknown[:20])}")
        if len(unknown) > 20:
            print(f"  ... and {len(unknown) - 20} more")
        print()

    print("All checked syscalls match Linux arities.")
    sys.exit(0)


if __name__ == "__main__":
    main()
