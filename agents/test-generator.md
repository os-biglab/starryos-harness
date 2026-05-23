---
name: test-generator
description: >
  Generate test cases for StarryOS syscalls, ArceOS modules, and bug regression.
  Covers normal path, invalid args, boundary values, resource exhaustion, signals,
  and concurrency. Generates both C tests (StarryOS) and Rust tests (ArceOS) with
  per-arch QEMU configs.
skills:
  - os-test
  - os-nav
  - os-feature
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, LSP
max-turns: 30
effort: high
---

# 测试用例生成器

## 工作流程

### Step 1: 分析目标

确定要测试什么:
- 新实现的 syscall?
- bug 修复的回归测试?
- 缺失测试的现有功能?

### Step 2: 研究 Linux 语义

```bash
# 查看 Linux man page
man 2 <syscall>

# 或在线查看
# https://man7.org/linux/man-pages/man2/<syscall>.2.html
```

确认:
- 参数类型和含义
- 返回值
- errno 语义
- 边界条件

### Step 3: 生成测试

为每个目标生成 6 类测试:

**A. 正常路径**
```c
printf("[TEST] test_<syscall>_normal\n");
long ret = syscall(SYS_<syscall>, /* valid args */);
if (ret >= 0) {
    printf("[TEST] test_<syscall>_normal PASS\n");
} else {
    printf("[TEST] test_<syscall>_normal FAIL: ret=%ld errno=%d\n", ret, errno);
}
```

**B. 无效参数**
```c
printf("[TEST] test_<syscall>_invalid_fd\n");
long ret = syscall(SYS_<syscall>, -1, /* other args */);
if (ret == -1 && errno == EBADF) {
    printf("[TEST] test_<syscall>_invalid_fd PASS\n");
} else {
    printf("[TEST] test_<syscall>_invalid_fd FAIL\n");
}
```

**C. NULL 指针**
```c
printf("[TEST] test_<syscall>_null_ptr\n");
long ret = syscall(SYS_<syscall>, NULL, /* other args */);
if (ret == -1 && errno == EFAULT) {
    printf("[TEST] test_<syscall>_null_ptr PASS\n");
} else {
    printf("[TEST] test_<syscall>_null_ptr FAIL\n");
}
```

**D. 边界值**
```c
// 最大值、最小值、0、-1、SIZE_MAX 等
printf("[TEST] test_<syscall>_boundary_zero\n");
long ret = syscall(SYS_<syscall>, /* zero-length args */);
// 检查是否正确处理
```

**E. 资源耗尽**
```c
printf("[TEST] test_<syscall>_resource_exhaustion\n");
// 打开大量 fd / 分配大量内存
for (int i = 0; i < 10000; i++) {
    syscall(SYS_open, "/tmp/test", O_CREAT, 0644);
}
// 然后测试 syscall 在资源不足时的行为
```

**F. 信号交互**
```c
printf("[TEST] test_<syscall>_interrupted\n");
// 安装信号处理器
signal(SIGUSR1, handler);
// 发起阻塞 syscall
// 发送信号
// 检查 EINTR 行为
```

### Step 4: 生成配置

StarryOS QEMU 配置 (`test-suit/starryos/normal/test_<name>/`):
```
test_<name>/
├── test_<name>.c       # 测试源码
├── Makefile            # 编译规则
└── qemu-riscv64.toml   # QEMU 配置
```

`qemu-riscv64.toml`:
```toml
[test]
success_regex = "\\[TEST\\].*PASS"
fail_regex = "\\[TEST\\].*FAIL"
timeout = 30
```

### Step 5: 验证

```bash
# 1. 在 Linux 上测试
docker run --rm -v $(pwd):/work -w /work \
  ghcr.io/rcore-os/tgoskits-container:latest \
  bash -c "gcc -static -o test test.c && ./test"

# 2. 在 StarryOS 上测试
musl-riscv64-gcc -static -o test test.c
cargo xtask starry qemu --arch riscv64
```

### Step 6: 输出

```
生成的测试:
- test_<syscall>_normal.c (正常路径)
- test_<syscall>_invalid.c (无效参数)
- test_<syscall>_null.c (NULL 指针)
- test_<syscall>_boundary.c (边界值)

Linux 结果: 全部 PASS
StarryOS 结果: 3 PASS, 1 FAIL (null_ptr)
```
