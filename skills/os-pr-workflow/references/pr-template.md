# PR 模板

## 标题格式

```
type(scope): description
```

### type 类型

| type | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `refactor` | 重构 (不改变行为) |
| `test` | 测试相关 |
| `docs` | 文档 |
| `chore` | 构建/工具/依赖 |
| `perf` | 性能优化 |

### scope 示例

| scope | 说明 |
|-------|------|
| `starry-syscall` | StarryOS syscall |
| `starry-signal` | 信号处理 |
| `starry-vm` | 虚拟内存 |
| `arceos-alloc` | ArceOS 内存分配 |
| `arceos-task` | ArceOS 任务管理 |
| `driver-virtio` | VirtIO 驱动 |
| `driver-blk` | 块设备驱动 |
| `component-axplat` | 平台抽象 |

### 示例标题

```
feat(starry-syscall): add getxattr syscall support
fix(starry-signal): prevent SIGSTOP from killing process
refactor(arceos-task): extract run_queue into separate module
test(starry-vm): add mmap boundary tests
```

## 正文模板 (中文)

```markdown
## 概述

<1-2 句话描述这个 PR 做了什么，为什么需要这个变更>

## 修改内容

- <具体修改 1: 文件/模块 + 做了什么>
- <具体修改 2>
- <具体修改 3>

## 测试

- [x] `cargo fmt --all -- --check`
- [x] `cargo xtask clippy --since upstream/dev` (零警告)
- [x] `cargo xtask sync-lint --since upstream/dev`
- [x] `cargo xtask test`
- [x] `cargo xtask starry qemu --arch riscv64` 测试通过
- [ ] (可选) `cargo xtask starry qemu --arch aarch64` 测试通过

## 关联

- <相关 issue>
- <相关 PR>
- <Linux man page 链接>
```

## Bug 修复模板

```markdown
## 概述

修复 <syscall/模块> 中的 <问题描述>。

## 根因

<技术根因分析>

## 修复方案

<修复描述>

## 复现

修复前:
```
<错误输出>
```

修复后:
```
<正确输出>
```

## 测试

- [x] 本地 CI 全部通过
- [x] 复现测试现在通过
- [x] 无回归
```

## 新功能模板

```markdown
## 概述

为 StarryOS 添加 <功能> 支持。

## 实现

### <子功能 1>
- 文件: <path>
- 说明: <实现细节>

### <子功能 2>
- 文件: <path>
- 说明: <实现细节>

## 与 Linux 的对比

| 特性 | Linux | StarryOS | 差异 |
|------|-------|----------|------|
| ... | ... | ... | ... |

## 测试

- [x] 单元测试: <测试文件>
- [x] 集成测试: <测试场景>
- [x] 本地 CI 全部通过
```
