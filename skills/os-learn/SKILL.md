---
name: os-learn
description: >
  Generate structured OS learning documents from the StarryOS/ArceOS/Axvisor codebase.
  Use when the user wants to understand a subsystem, learn how an OS concept is implemented,
  trace execution flows, compare implementations across the three OSes, or generate study material.
  Triggers: "learn", "understand", "explain how", "study", "tutorial", "walkthrough",
  "how does X work", "teach me", "生成学习文档", "帮我理解", "讲解", "学习"
allowed-tools: Read, Grep, Glob, Bash, LSP
effort: medium
---

# OS 学习文档生成器

为用户生成结构化的 OS 学习文档，基于 StarryOS/ArceOS/Axvisor 源码。

## 工作流程

### Phase 1: 确定学习目标

向用户确认:
1. **主题**: 具体的 OS 概念或子系统
2. **深度**: 入门概述 / 深入分析 / 源码级追踪
3. **范围**: 单个 OS / 跨 OS 对比
4. **输出**: 内联讲解 / 独立文档文件

### Phase 2: 代码探索

根据主题探索相关代码:

**Syscall 机制**:
- 入口: `os/StarryOS/kernel/src/syscall/mod.rs` (分发表)
- 分类文件: `fs.rs`, `mm.rs`, `task.rs`, `signal.rs`, `net.rs`, `time.rs`, `misc.rs`, `io.rs`
- trap handler: `os/StarryOS/kernel/src/trap/` 或各架构 HAL
- 用户指针: `UserInPtr`, `UserOutPtr` (components/starry-vm/)

**进程管理**:
- 进程: `components/starry-process/`
- 线程/任务: `os/arceos/modules/axtask/`
- 调度器: `os/arceos/modules/axtask/src/run_queue.rs`
- 上下文切换: `components/axcpu/`

**内存管理**:
- 虚拟内存: `components/starry-vm/`
- 页表: `components/page_table_multiarch/`
- 分配器: `os/arceos/modules/axalloc/`
- 内存集: `components/memory_set/`
- mmap: `os/StarryOS/kernel/src/syscall/mm.rs`

**信号处理**:
- 信号: `components/starry-signal/`
- syscall: `os/StarryOS/kernel/src/syscall/signal.rs`
- trampoline: 各架构 `trap.rs`

**文件系统**:
- VFS: `os/arceos/modules/axfs/` 或 `axfs-ng/`
- syscall: `os/StarryOS/kernel/src/syscall/fs.rs`
- 文件描述符: `os/StarryOS/kernel/src/fs/`

**网络**:
- 网络栈: `os/arceos/modules/axnet/` 或 `axnet-ng/`
- syscall: `os/StarryOS/kernel/src/syscall/net.rs`

**驱动模型**:
- 四层架构: `drivers/` 下的 `blk/`, `net/`, `serial/` 等
- 接口: `drivers/interface/rdif-*`
- 平台: `platform/`
- 参考: `skills/cross-kernel-driver/references/architecture.md`

**设备树/平台**:
- 平台抽象: `components/axplat/`
- 平台实现: `platform/`
- 配置: `.axconfig.toml`

### Phase 3: 生成文档

输出结构:

```markdown
# {主题} - StarryOS 实现分析

## 1. 概述
- 这个机制解决什么问题
- 在 OS 中的角色
- 与 Linux 的对应关系

## 2. 执行流程
- 从用户态到内核态的完整路径
- 每一步标注: 文件:行号
- 用 → 箭头连接调用链

## 3. 关键数据结构
- 每个结构体/枚举的用途
- 字段含义
- 生命周期

## 4. 关键函数
- 每个核心函数的签名、参数、返回值
- 实现要点
- 边界条件处理

## 5. 与 Linux 的对比
| 特性 | Linux | StarryOS | 差异说明 |

## 6. 代码导航表
| 功能 | 文件 | 函数 | 行号 |

## 7. 动手实验
- 可运行的测试代码
- QEMU 命令
- 预期输出

## 8. 延伸阅读
- 相关源码路径
- Linux man pages
- 论文/文档链接
```

### Phase 4: 交互深化

生成文档后，询问用户:
- 哪部分需要更深入的分析
- 是否需要对比其他 OS 的实现
- 是否需要生成实验代码
- 是否需要追踪其他相关机制

## 文档生成规则

1. **基于代码，不猜测**: 所有结论必须有源码支撑，标注文件:行号
2. **执行流优先**: 先讲清楚"代码怎么跑"，再讲"代码怎么写"
3. **对比 Linux**: 每个概念都与 Linux 对比，帮助建立映射
4. **可实验**: 尽量提供可运行的代码让用户亲手验证
5. **渐进深入**: 从概述开始，逐层深入到实现细节

## 跨 OS 对比

当用户要求对比三个 OS 时:

| OS | 定位 | 关键差异 |
|----|------|---------|
| ArceOS | 模块化 unikernel | 提供基础模块 (axtask, axmm, axfs 等) |
| StarryOS | Linux 兼容宏内核 | 基于 ArceOS 模块，添加 syscall/进程/信号 |
| Axvisor | Type-1 虚拟机监控器 | 基于 ArceOS 模块，添加 vCPU/VM 管理 |

对比维度:
- 同一模块在三个 OS 中的角色差异
- 共享组件的使用方式
- 独有功能的实现
