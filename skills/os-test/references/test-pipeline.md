# 测试流水线详解

## 流水线总览

```
源码修改
  ↓
cargo fmt --all -- --check          ← 格式检查
  ↓
cargo xtask clippy --since <ref>    ← clippy 零警告
  ↓
cargo xtask sync-lint --since <ref> ← 原子序检查
  ↓
cargo xtask test                     ← std 测试
  ↓
cargo xtask arceos test             ← ArceOS QEMU 测试 (4 架构)
  ↓
cargo xtask starry test             ← StarryOS QEMU 测试 (4 架构)
  ↓
全部通过 → 可以提交 PR
```

## 各阶段详解

### 1. 格式检查

```bash
cargo fmt --all -- --check
```

检查所有 workspace 成员的代码格式。`--check` 模式只检查不修改。

如果失败:
```bash
cargo fmt --all  # 自动修复格式
```

### 2. Clippy 检查

```bash
# 增量模式 (PR 场景，只检查变更)
cargo xtask clippy --since origin/dev

# 全量模式
cargo xtask clippy --all

# 单个 crate
cargo xtask clippy --package starry-kernel
```

tgoskits 要求 **零警告**。任何 warning 都会阻塞 CI。

常见 clippy 问题:
- 未使用的变量/导入
- 不必要的 clone/copy
- 可以简化的 match/if 表达式
- unsafe 代码中的未定义行为风险

### 3. Sync-lint 检查

```bash
cargo xtask sync-lint --since origin/dev
```

检查可疑的 `Ordering::Relaxed` 使用。在内核代码中，错误的原子序可能导致:
- 多核数据竞争
- 编译器/CPU 指令重排问题

### 4. Std 测试

```bash
cargo xtask test
```

运行 `scripts/test/std_crates.csv` 中列出的 crate 的宿主机测试。

新增 crate 需要手动加入 CSV:
```csv
crate-name,description
axalloc,Memory allocator
```

### 5. ArceOS QEMU 测试

```bash
cargo xtask arceos test
```

遍历 `test-suit/arceos/` 下的所有测试用例，对每个用例:
1. 读取 `qemu-*.toml` 配置
2. 编译内核
3. 启动 QEMU
4. 等待输出匹配 `success_regex` 或 `fail_regex`
5. 报告结果

### 6. StarryOS QEMU 测试

```bash
cargo xtask starry test
```

类似 ArceOS 测试，但针对 `test-suit/starryos/` 下的用例。

测试分组:
- `normal/` -- 常规测试
- `stress/` -- 压力测试
- `syscall/` -- syscall 测试

## 架构矩阵

| 架构 | 目标三元组 | QEMU 命令 |
|------|-----------|----------|
| riscv64 | `riscv64gc-unknown-none-elf` | `qemu-system-riscv64` |
| aarch64 | `aarch64-unknown-none-softfloat` | `qemu-system-aarch64` |
| x86_64 | `x86_64-unknown-none` | `qemu-system-x86_64` |
| loongarch64 | `loongarch64-unknown-none-softfloat` | `qemu-system-loongarch64` |

默认在 riscv64 上快速迭代，架构相关代码变更时交叉验证。
