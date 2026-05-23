---
name: os-test
description: >
  Systematic testing workflow for StarryOS/ArceOS/Axvisor. Covers syscall unit tests,
  application compatibility, performance benchmarks, and concurrency stress tests.
  Enforces Linux-first discipline: every test must pass on Docker Linux before trusting StarryOS results.
  Use when the user wants to run tests, write test cases, validate a fix, or check regression.
  Triggers: "test", "run test", "write test", "validate", "regression", "QEMU test",
  "测试", "运行测试", "写测试", "验证修复", "回归测试", "cargo xtask test"
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, LSP
effort: high
---

# 系统化测试工作流

## 核心原则

**Linux 定义正确性**: 每个测试必须先在 Docker Linux 上通过，再在 StarryOS 上运行。
如果测试在 Linux 上失败，说明测试本身有 bug，不是内核的问题。

## 测试类型

### A. Std 测试 (宿主机)

```bash
# 运行所有 std 测试
cargo xtask test

# 运行特定 crate 的测试
cargo test -p <crate-name>
```

适用: 组件层 (components/) 中不依赖 OS 的纯 Rust 代码。

### B. ArceOS QEMU 测试

```bash
# 运行所有 ArceOS 测试
cargo xtask arceos test

# 运行特定测试
cargo xtask arceos qemu --package ax-helloworld --arch aarch64
```

适用: ArceOS 模块和 API 测试。测试用例在 `test-suit/arceos/`。

### C. StarryOS QEMU 测试

```bash
# 准备 rootfs
cargo xtask starry rootfs --arch riscv64

# 运行 StarryOS
cargo xtask starry qemu --arch riscv64

# 运行测试套件
cargo xtask starry test
```

适用: syscall 测试、应用兼容性测试。测试用例在 `test-suit/starryos/`。

### D. 并发压测

```bash
# 多 SMP 配置测试
for smp in 1 2 4; do
  cargo xtask starry qemu --arch riscv64 --smp $smp
done
```

适用: 检测 SMP 相关的并发问题 (SMP=1 正常, SMP>1 失败 → 并发 bug)。

## 测试流程

### Step 1: 选择目标

确认要测试什么:
- 新实现的 syscall?
- bug 修复的回归验证?
- 应用兼容性?

### Step 2: Linux 参考测试 (如果适用)

对于 syscall 测试，先在 Docker Linux 上验证:

```bash
# 在 Docker 中编译和运行
docker run --rm -v $(pwd):/work -w /work \
  ghcr.io/rcore-os/tgoskits-container:latest \
  gcc -static -o test_binary test.c && ./test_binary
```

或使用 musl 静态编译 (更接近 StarryOS 环境):
```bash
musl-gcc -static -o test_binary test.c
# 用 qemu-user 在 x86_64 上运行
qemu-x86_64 ./test_binary
```

记录 Linux 上的输出作为参考。

### Step 3: StarryOS 测试

```bash
# 编译测试程序
musl-riscv64-gcc -static -o test_binary test.c

# 注入 rootfs
# 将 test_binary 放入 rootfs 目录

# 运行
cargo xtask starry qemu --arch riscv64
# 在 StarryOS 中执行 test_binary
```

### Step 4: 对比分析

比较 Linux 和 StarryOS 的输出:
- 返回值是否一致?
- errno 是否一致?
- 副作用是否一致 (文件内容、信号行为等)?

### Step 5: 缺陷报告

如果发现差异，生成结构化报告:
```
## 缺陷报告
- Syscall: getxattr
- Linux 行为: 返回 10, errno=0
- StarryOS 行为: 返回 -1, errno=ENOSYS
- 根因: getxattr 未实现 (stub 返回 ENOSYS)
- 测试文件: test_getxattr.c
```

### Step 6: 回归验证

修复后重新运行测试，确认:
- 原来的测试现在通过
- 没有引入新的回归

## 编写测试

### C 测试模板 (StarryOS)

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <sys/syscall.h>

int main() {
    // 测试正常路径
    printf("[TEST] test_getxattr_normal\n");
    char buf[256];
    long ret = syscall(SYS_getxattr, "/tmp/test", "user.test", buf, sizeof(buf));
    if (ret >= 0) {
        printf("[TEST] test_getxattr_normal PASS\n");
    } else {
        printf("[TEST] test_getxattr_normal FAIL: errno=%d\n", errno);
    }

    // 测试错误参数
    printf("[TEST] test_getxattr_null_path\n");
    ret = syscall(SYS_getxattr, NULL, "user.test", buf, sizeof(buf));
    if (ret == -1 && errno == EFAULT) {
        printf("[TEST] test_getxattr_null_path PASS\n");
    } else {
        printf("[TEST] test_getxattr_null_path FAIL: ret=%ld errno=%d\n", ret, errno);
    }

    return 0;
}
```

### 输出格式

测试程序必须输出 `[TEST] <name> PASS` 或 `[TEST] <name> FAIL: <reason>`。
这是 QEMU 日志解析和 CI 自动化的基础。

### ArceOS Rust 测试

```rust
// test-suit/arceos/rust/my_test/src/main.rs
#![no_std]
#![no_main]

use axstd::println;

#[no_mangle]
fn main() -> i32 {
    println!("[TEST] test_alloc_normal");
    let v = alloc::vec![1u8; 1024];
    if v.len() == 1024 {
        println!("[TEST] test_alloc_normal PASS");
    } else {
        println!("[TEST] test_alloc_normal FAIL");
        return 1;
    }
    0
}
```

对应的 QEMU 配置:
```toml
# test-suit/arceos/rust/my_test/qemu-riscv64.toml]
packages = ["ax-hello-world"]
build_args = ["--features", "my-feature"]
success_regex = "\\[TEST\\].*PASS"
fail_regex = "\\[TEST\\].*FAIL"
```

## 工具链

| 工具 | 用途 |
|------|------|
| `cargo xtask test` | std 测试 |
| `cargo xtask arceos test` | ArceOS QEMU 测试 |
| `cargo xtask starry test` | StarryOS QEMU 测试 |
| `cargo xtask starry qemu --arch <arch>` | 手动 QEMU 运行 |
| `cargo xtask starry rootfs --arch <arch>` | 准备 rootfs |
| `parse-qemu-log.py` | 解析 QEMU 日志 |
| `gen-syscall.py` | 生成 syscall 代码 (含测试模板) |

## 参考文件

- [test-pipeline.md](references/test-pipeline.md) -- 完整测试流水线
- [linux-comparison.md](references/linux-comparison.md) -- Docker Linux 对照方法
- [test-templates.md](references/test-templates.md) -- 测试代码模板
