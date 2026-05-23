# os-biglab-plugin 场景化使用指南

> 本文档覆盖 StarryOS 开发中的 4 个核心场景，每个场景给出具体步骤和示例对话。
> 与 tgoskits 内置技能互补：内置技能处理项目细节，本插件提供系统化工作流和自动化工具。

---

## 场景一：运行时 Bug 调试

### 适用情况

- QEMU 启动后出现 kernel panic
- syscall 返回错误值 / 行为不符合 Linux 语义
- 程序挂起、死锁、无响应
- Page fault / Illegal instruction
- 编译通过但运行时崩溃

### 步骤

#### 1. 启动 QEMU 并捕获日志

```bash
# 方式 A: 同时输出到终端和日志文件
cargo xtask starry qemu --arch riscv64 2>&1 | tee /tmp/os_run.log

# 方式 B: 仅输出到日志文件 (后台运行)
cargo xtask starry qemu --arch riscv64 > /tmp/os_run.log 2>&1 &

# 方式 C: 使用 debugcon 日志 (推荐，信息更丰富)
# 确保 .starry.toml 中启用了 debugcon feature
cargo xtask starry qemu --arch riscv64 2>&1 | tee /tmp/debugcon.log
```

#### 2. 描述问题给 Claude

```
# 示例 1: panic
QEMU 启动后出现 panic:
panicked at os/StarryOS/kernel/src/task/run_queue.rs:456:18:
called `Option::unwrap()` on a `None` value

# 示例 2: 行为异常
getxattr 调用返回 ENOSYS，但 Linux 上这个 syscall 是正常工作的

# 示例 3: 挂起
StarryOS 启动后卡住不动，没有输出任何内容

# 示例 4: 直接给日志文件
请分析 /tmp/os_run.log 中的错误
```

#### 3. Claude 自动执行

Claude 会自动调用 `parse-qemu-log.py` 或 `os-debug` 技能:

```
Claude:
1. 运行 parse-qemu-log.py 解析日志
   → 提取 panic 位置: run_queue.rs:456
   → 提取 PC/sepc 地址
   → 建议 addr2line 命令

2. 读取源码定位问题
   → 读 run_queue.rs:456 附近代码
   → 追踪调用链: 哪个函数传入了 None

3. 分析根因
   → Root cause: blocked_resched 中 AxWaker 的 wake_by_ref 
     导致 spurious wakeup，wait_queue 中出现重复 entry

4. 建议修复
   → 在 blocked_resched 中添加 double-add 检查

5. 验证修复
   → cargo fmt --package starry-kernel
   → cargo xtask clippy --package starry-kernel
   → 重新运行 QEMU 测试
```

#### 4. 对于复杂问题，使用 kernel-debugger agent

```
@kernel-debugger 
StarryOS 在 SMP=2 时偶发死锁，SMP=1 时正常。
日志在 /tmp/debugcon.log，请分析可能的死锁点。
```

kernel-debugger 会:
- 只读分析，不修改代码
- 追踪锁的获取顺序
- 检查是否有可能的 AB-BA 死锁
- 输出: Root cause / Suggested fix / Files to modify

#### 5. 并发问题专项调试

```
这个问题在 SMP=1 时正常，SMP=2 时才出现，请检查并发安全性。
```

Claude 会:
- 追踪所有共享状态的访问点
- 检查锁的保护范围
- 分析是否存在 data race 或 atomicity violation
- 参考 tgoskits 内置的 `starryos-debug` 技能中的已知 panic 模式

### 工具链

| 工具 | 来源 | 用途 |
|------|------|------|
| `parse-qemu-log.py` | os-biglab-plugin | 解析 QEMU 日志，提取错误信息 |
| `os-debug` skill | os-biglab-plugin | 结构化调试工作流 |
| `starryos-debug` skill | tgoskits 内置 | StarryOS 特定的 panic 模式和修复 |
| `kernel-debugger` agent | os-biglab-plugin | 深度诊断，只读分析 |
| `auto-fmt.sh` hook | os-biglab-plugin | 编辑后自动格式化 |
| `pre-pr-gate.sh` hook | os-biglab-plugin | push 前 clippy 零警告检查 |

---

## 场景二：OS 学习文档生成

### 适用情况

- 想理解某个子系统的实现原理
- 想追踪某个功能的完整执行流
- 想学习 OS 概念如何在 StarryOS 中落地
- 想理解两个模块之间的交互关系

### 使用方式

直接向 Claude 描述你想学习的内容:

```
# 示例 1: 学习 syscall 机制
请帮我生成一份学习文档，讲解 StarryOS 的 syscall 机制：
- 从用户态程序调用 libc 开始，到内核处理的完整流程
- 涉及的关键数据结构和函数
- 与 Linux 的异同
- 结合具体代码位置

# 示例 2: 学习信号处理
我想深入理解 StarryOS 的信号(signal)处理机制，请生成学习文档

# 示例 3: 学习内存管理
请帮我理解 StarryOS 的虚拟内存管理：
- 页表是如何构建的
- mmap 的完整实现流程
- 与 ArceOS axmm 模块的关系

# 示例 4: 学习调度器
StarryOS 的任务调度器是如何工作的？请从 axtask 到 run_queue 追踪完整流程

# 示例 5: 学习驱动模型
请解释 tgoskits 的四层驱动模型(Driver Core / Capability Boundary / OS Glue / Runtime)，
结合 drivers/ 下的具体例子
```

### Claude 会生成的文档结构

```markdown
# StarryOS 信号处理机制

## 1. 概述
信号(signal)是 Unix 系统中进程间通信的基本机制...

## 2. 执行流程
用户态 kill() → libc syscall → trap handler → 
sys_kill() → send_signal() → ...

### 2.1 用户态入口
- 文件: os/StarryOS/kernel/src/syscall/signal.rs
- 函数: sys_kill(), sys_tkill(), sys_tgkill()
- 关键代码: ...

### 2.2 信号投递
- 文件: components/starry-signal/src/lib.rs
- 函数: send_signal()
- 数据结构: SignalQueue, SigInfo
- ...

### 2.3 信号处理
- ...

## 3. 关键数据结构
- SigInfo: 信号信息
- SignalQueue: 信号队列
- SignalHandler: 处理函数注册
- ...

## 4. 与 Linux 的对比
| 特性 | Linux | StarryOS | 差异说明 |
|------|-------|----------|---------|
| ... | ... | ... | ... |

## 5. 代码导航
| 功能 | 文件 | 函数 |
|------|------|------|
| 信号发送 | kernel/src/syscall/signal.rs | sys_kill |
| ... | ... | ... |

## 6. 动手实验
在 QEMU 中运行以下测试观察信号行为:
```c
// 测试代码
#include <signal.h>
...
```

## 7. 延伸阅读
- Linux man 7 signal
- StarryOS 源码: components/starry-signal/
- ArceOS 调度: os/arceos/modules/axtask/
```

### 高级用法

```
# 对比学习: 同一概念在三个 OS 中的实现
请对比 ArceOS、StarryOS、Axvisor 中的任务调度实现，生成对比学习文档

# 追踪特定机制
请从 cargo xtask starry qemu 的启动过程开始，追踪到第一个用户程序执行的完整流程

# 结合实验
请帮我写一个测试程序，演示 StarryOS 的 mmap 机制，并解释每一步的内核行为
```

### 工具链

| 工具 | 来源 | 用途 |
|------|------|------|
| `os-nav` skill | os-biglab-plugin | 代码导航，模块依赖图 |
| `os-feature` skill | os-biglab-plugin | 理解功能实现模式 |
| `kernel-debugger` agent | os-biglab-plugin | 只读深度分析 |
| tgoskits AGENTS.md | tgoskits | 项目架构和约定 |

---

## 场景三：与 upstream/dev 同步

### 适用情况

- 本地有修改，需要 rebase 到最新的 upstream/dev
- 需要提交 PR，要求分支基于最新 upstream
- rebase 后有冲突需要解决
- rebase 后需要验证编译和 clippy

### 步骤

#### 1. 告诉 Claude 你的目标

```
# 示例 1: 简单 rebase
我需要把当前分支 rebase 到最新的 upstream/dev

# 示例 2: 重写分支
我的分支太乱了，我想在最新的 upstream/dev 基础上重写(squash)我的修改

# 示例 3: 解决冲突
我 rebase 到 upstream/dev 时遇到了冲突，请帮我解决

# 示例 4: 检查同步状态
请检查我当前分支和 upstream/dev 的差异，告诉我需要同步什么
```

#### 2. Claude 执行同步流程

```
Claude:

Step 1: 获取最新 upstream
$ git fetch upstream
$ git log --oneline upstream/dev -5

Step 2: 检查当前分支状态
$ git status
$ git log --oneline HEAD...upstream/dev --left-right

Step 3: 执行 rebase
$ git rebase upstream/dev

Step 4: 如果有冲突
→ 列出冲突文件
→ 逐个分析冲突原因
→ 建议解决方案
→ 解决后 git rebase --continue

Step 5: 验证
$ cargo fmt --all -- --check
$ cargo xtask clippy --since upstream/dev
$ cargo xtask sync-lint --since upstream/dev
$ cargo xtask test

Step 6: 确认结果
→ 分支现在基于最新的 upstream/dev
→ fmt/clippy/test 全部通过
→ 可以准备提交 PR
```

#### 3. 冲突解决策略

```
Claude:

冲突文件: os/StarryOS/kernel/src/syscall/fs.rs
冲突原因: upstream 修改了 read() 的签名，你的 getxattr 实现依赖旧签名

解决方案:
1. 保留 upstream 的新签名
2. 适配你的 getxattr 实现到新接口
3. 验证编译通过

需要你确认: 采用方案 1 还是其他方式？
```

#### 4. Squash 重写分支

```
# 如果分支太乱，想在 upstream/dev 上重写
请帮我把当前分支的修改 squash 成一个干净的 commit，
基于最新的 upstream/dev
```

```
Claude:

Step 1: 记录当前修改
$ git diff upstream/dev...HEAD --stat

Step 2: 创建临时分支
$ git checkout -b tmp-clean upstream/dev

Step 3: 应用修改
$ git checkout my-branch -- os/StarryOS/kernel/src/syscall/fs.rs
$ git checkout my-branch -- os/StarryOS/kernel/src/syscall/mod.rs

Step 4: 提交
$ git add -A
$ git commit -m "feat(starry-syscall): add getxattr syscall support"

Step 5: 验证
$ cargo fmt --all -- --check
$ cargo xtask clippy --since upstream/dev

Step 6: 替换原分支
$ git branch -D my-branch
$ git branch -m my-branch
```

### 注意事项

- rebase 前确保本地修改已 commit (不要丢失工作)
- rebase 后 `git push --force-with-lease` 更新远程分支
- tgoskits 要求 PR 基于 `dev` 分支 (不是 main)
- clippy 零警告是硬性要求

---

## 场景四：PR 提交

### 适用情况

- 代码修改完成，准备提交 PR
- 需要本地 CI 验证
- 需要生成 PR 描述

### 步骤

#### 1. 本地 CI 验证 (push 前必须通过)

```
# Claude 会自动执行，或你手动运行:

# 1. 格式检查
cargo fmt --all -- --check

# 2. clippy (零警告)
cargo xtask clippy --since upstream/dev

# 3. sync-lint (检查 Relaxed 原子序)
cargo xtask sync-lint --since upstream/dev

# 4. std 测试
cargo xtask test

# 5. QEMU 测试 (至少一个架构)
cargo xtask starry qemu --arch riscv64
```

**push 前门控**: 插件的 `pre-pr-gate.sh` hook 会在你执行 `git push` 或 `gh pr create` 时自动检查:
- 不允许直接推 main/master/dev
- `cargo fmt --all -- --check` 必须通过
- `cargo xtask clippy` 必须零警告

如果检查失败，push 会被阻塞。

#### 2. 准备 PR 描述

```
请帮我准备 PR 描述，修改是添加 getxattr syscall
```

```
Claude 生成的 PR 描述:

标题: feat(starry-syscall): add getxattr syscall support

正文 (中文):
## 概述
为 StarryOS 添加 getxattr (extended attributes) syscall 支持。

## 修改内容
- 在 syscall 分发表中注册 getxattr (nr=192)
- 实现 sys_getxattr 函数，支持读取文件扩展属性
- 处理 UserInPtr/UserOutPtr 用户态指针

## 测试
- [x] cargo fmt --all -- --check
- [x] cargo xtask clippy (零警告)
- [x] cargo xtask test
- [x] QEMU riscv64 运行测试

## 关联
- Linux man 2 getxattr
```

#### 3. 提交 PR

```bash
# 推送分支
git push origin my-branch

# 创建 PR (或由 Claude 生成 gh 命令)
gh pr create --base dev --title "feat(starry-syscall): add getxattr syscall support" --body "..."
```

### PR 规范 (tgoskits 要求)

| 要求 | 说明 |
|------|------|
| 标题格式 | Conventional Commits: `type(scope): content` (英文) |
| 正文语言 | 中文 |
| 基础分支 | `dev` (不是 main) |
| AI 声明 | 不添加 AI/agent 签名 |
| clippy | 零警告 |
| fmt | 通过 |
| 同步 | PR 创建后，修改代码需更新 PR 描述 |

---

## 场景五：跨架构验证

### 适用情况

- 修改了架构相关代码 (HAL, 页表, 信号 trampoline)
- 需要在多个架构上验证

### 步骤

```
请在 riscv64 和 aarch64 上验证这个修改
```

```
Claude:

# riscv64
$ cargo xtask starry qemu --arch riscv64
→ 通过

# aarch64
$ cargo xtask starry qemu --arch aarch64
→ 通过

两个架构均通过验证。
```

---

## 场景六：添加新测试用例

### 适用情况

- 为新实现的 syscall 添加测试
- 为发现的 bug 编写回归测试

### 使用 tgoskits 内置技能

```
# StarryOS 测试
/starry-test-suit 为 getxattr 添加测试用例

# ArceOS 测试
/arceos-test-adapter 为 axalloc 添加测试
```

### 使用插件工具

```
# 生成测试模板
请为 getxattr syscall 生成测试用例，覆盖正常路径、错误参数、边界值
```

Claude 会参考 `os-test/references/test-templates.md` (Phase 1 实现后) 生成 C 测试代码。

---

## 快速参考

### 一句话触发

| 你说 | Claude 做什么 |
|------|-------------|
| "QEMU 出 panic 了" | 自动解析日志，定位问题 |
| "请分析 /tmp/os_run.log" | 运行 parse-qemu-log.py |
| "帮我理解 XXX 机制" | 生成 OS 学习文档 |
| "rebase 到 upstream/dev" | 执行同步流程 |
| "准备 PR" | 本地 CI + PR 描述生成 |
| "clippy 报错了" | 分析 warning 并修复 |
| "@kernel-debugger 分析这个问题" | 启动只读诊断 agent |
| "@os-architect 实现 XXX" | 启动设计+实现 agent |

### 命令速查

```bash
# 构建
cargo xtask starry build --arch riscv64
cargo xtask arceos build --arch aarch64

# 运行
cargo xtask starry qemu --arch riscv64
cargo xtask arceos qemu --arch aarch64 --package ax-helloworld

# 测试
cargo xtask test                    # std 测试
cargo xtask starry test             # StarryOS QEMU 测试
cargo xtask arceos test             # ArceOS QEMU 测试

# 检查
cargo fmt --all -- --check          # 格式
cargo xtask clippy --since HEAD~1   # clippy (增量)
cargo xtask clippy --all            # clippy (全量)
cargo xtask sync-lint --since HEAD~1 # 原子序检查

# Git
git fetch upstream                   # 获取上游
git rebase upstream/dev              # 同步
git push --force-with-lease          # 更新远程 (rebase 后)
```
