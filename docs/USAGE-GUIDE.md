# os-biglab-plugin 使用指南

> 本指南说明如何在 Claude Code 中安装、配置和使用 os-biglab 插件。

---

## 一、安装方式

### 方式 1: 插件目录模式 (推荐开发阶段)

```bash
# 在 tgoskits 项目目录下启动 Claude Code
cd /path/to/tgoskits
claude --plugin-dir /path/to/os-biglab-plugin
```

### 方式 2: 项目级安装

```bash
# 在 tgoskits 项目目录下安装
claude plugin install /path/to/os-biglab-plugin --scope project
```

安装后会在 tgoskits 项目的 `.claude/settings.json` 中添加插件引用。

### 方式 3: 全局安装

```bash
claude plugin install /path/to/os-biglab-plugin --scope user
```

---

## 二、验证安装

启动 Claude Code 后，应该看到:

```
[os-biglab] plugin ready
```

检查插件是否加载:

```
# 在 Claude Code 中输入
/skills
```

应该看到以下技能列表:
- os-debug
- os-feature
- os-review
- os-nav
- starryos-debug
- os-test (Phase 1 完成后)
- os-pr-workflow (Phase 1 完成后)
- os-benchmark (Phase 3 完成后)
- os-evolve (Phase 3 完成后)

---

## 三、技能使用

### 3.1 os-debug -- 内核调试

**触发方式**: 直接描述问题，或使用 `/os-debug`

```
# 示例对话
QEMU 启动后出现 panic: panicked at src/mm/page_table.rs:123

# 或者
/os-debug PageFault at address 0xffff800010000000
```

**工作流程**:
1. 自动分类问题 (A-F 类)
2. 读取 QEMU 日志 (`/tmp/os_run.log`)
3. 定位源码
4. 建议修复方案

**配合工具**:
- `parse-qemu-log.py` 解析 QEMU 日志
- `qemu-log-watcher` 监控器自动捕获错误
- 参考文件: panic-patterns.md, errno-table.md, gdb-workflow.md

### 3.2 os-feature -- 功能实现

**触发方式**: 描述要实现的功能

```
# 示例对话
我需要为 StarryOS 添加 getxattr syscall

# 或者
为 ArceOS 添加一个新的 axgpu 模块

# 或者
添加 VirtIO GPU 驱动
```

**支持的子系统**:
- A: StarryOS 新 syscall
- B: ArceOS 新模块
- C: 新设备驱动
- D: VFS / 文件系统扩展
- E: 内存管理变更

**配合工具**:
- `gen-syscall.py` 生成 syscall 模板代码
- 参考文件: syscall-guide.md, module-guide.md, driver-guide.md

### 3.3 os-review -- 代码评审

**触发方式**: 请求评审，或在 PR 准备阶段自动触发

```
# 示例对话
请评审 os/StarryOS/kernel/syscall/fs.rs 的修改

# 或者
审查这个 PR 的并发安全性
```

**8 维评审**:
1. unsafe 代码
2. 并发与锁
3. 内存管理
4. 错误处理
5. 性能
6. 平台兼容性
7. API 正确性
8. 测试覆盖

**输出格式**:
```
Summary: ...
Critical issues: (阻塞合并)
Warnings: (应该修复)
Nitpicks: (可选)
Verdict: APPROVE / REQUEST_CHANGES / NEEDS_DISCUSSION
```

### 3.4 os-nav -- 代码导航

**触发方式**: 询问代码结构

```
# 示例对话
StarryOS 的 syscall 分发在哪里？

# 或者
找到所有使用 crate_interface 的地方

# 或者
追踪从 _start 到 main 的执行流
```

**功能**:
- 模块依赖图
- 按功能查找入口文件
- crate_interface 调用链
- 执行流追踪
- LSP 辅助导航

### 3.5 starryos-debug -- StarryOS 专用调试

**触发方式**: StarryOS 特定问题

```
# 示例对话
StarryOS debugcon 日志显示 AxWaker panic

# 或者
PTY 输出延迟严重
```

**特色**:
- debugcon 日志分析
- 4 种已知 panic 模式修复
- cargo fmt/clippy 工作流
- 关键文件路径速查

---

## 四、Agent 使用

### 4.1 kernel-debugger -- 内核诊断专家

```
# 自动触发，或手动调用
@kernel-debugger 分析这个 page fault 的根因
```

**特点**: 只读，不修改代码，输出结构化诊断报告

### 4.2 os-architect -- 架构设计与实现

```
# 自动触发，或手动调用
@os-architect 设计并实现 getxattr syscall
```

**特点**: 可读写代码，遵循最小侵入原则

### 4.3 code-reviewer -- 代码审查

```
# 自动触发，或手动调用
@code-reviewer 审查 os/StarryOS/kernel/signal.rs 的修改
```

**特点**: 只读，8 维评审，输出结构化报告

### 4.4 bug-hunter -- 缺陷发现 (Phase 1 新增)

```
@bug-hunter 在 os/StarryOS/kernel/ 中搜索潜在的并发缺陷
```

**特点**: 两维度分类，5 阶段工作流

### 4.5 test-generator -- 测试生成 (Phase 3 新增)

```
@test-generator 为 getxattr syscall 生成测试用例
```

**特点**: 生成 C 测试 + per-arch QEMU 配置

---

## 五、Hook 自动行为

### 5.1 自动格式化 (PostToolUse)

每次编辑 `.rs` 文件后，自动运行 `cargo fmt --package <crate>`。

**行为**: 无需手动触发，编辑代码后自动生效。

### 5.2 插件初始化 (SessionStart)

启动 Claude Code 时自动:
- 使脚本可执行
- 打印 `[os-biglab] plugin ready`

### 5.3 PR 门控 (PreToolUse) ✅ 已实现

执行 `gh pr create` 或 `git push` 前自动检查:
- 禁止直接推 main/master/dev 分支
- `cargo fmt --all -- --check` 必须通过
- `cargo xtask clippy` **零警告** (tgoskits 硬性要求，任何 warning 都会阻塞 push)

如果检查失败，push 会被阻塞并提示修复方法。

### 5.4 活动日志 (PostToolUse) -- Phase 2 新增

每次编辑文件后自动记录到 `docs/os-biglab-logs/activity.md`

### 5.5 会话结束 (Stop) -- Phase 2 新增

会话结束时自动生成工作总结

---

## 六、Monitor 自动行为

### 6.1 qemu-log-watcher

当 `os-debug` 技能被激活时，自动监控 `/tmp/os_run.log`，捕获:
- `panicked at`
- `PageFault`, `InstructionFault`, `LoadFault`, `StoreFault`
- `IllegalInstruction`, `SIGSEGV`, `kernel BUG`
- `ERROR`, `WARN`

### 6.2 git-change-tracker -- Phase 2 新增

自动监控 git diff，识别变更影响的子系统

---

## 七、脚本使用

### 7.1 gen-syscall.py -- 生成 syscall 模板

```bash
python3 scripts/gen-syscall.py \
  --name getxattr \
  --nr 192 \
  --args "path: *const u8, name: *const u8, value: *mut u8, size: usize" \
  --category fs
```

输出:
1. `mod.rs` 分发表条目
2. `fs.rs` 实现函数框架

### 7.2 parse-qemu-log.py -- 解析 QEMU 日志

```bash
# 从文件解析
python3 scripts/parse-qemu-log.py /tmp/os_run.log

# 从管道解析
qemu-system-riscv64 ... 2>&1 | python3 scripts/parse-qemu-log.py
```

输出: 结构化错误报告，按严重性分组

### 7.3 auto-fmt.sh -- 自动格式化

```bash
# 通常由 PostToolUse hook 自动调用
# 手动调用:
echo '{"tool_input":{"file_path":"/path/to/file.rs"}}' | bash scripts/auto-fmt.sh
```

### 7.4 auto-clippy.sh -- 自动 clippy

```bash
# 带参数调用
bash scripts/auto-clippy.sh axalloc

# 从管道调用
echo '{"tool_input":{"file_path":"/path/to/file.rs"}}' | bash scripts/auto-clippy.sh
```

### 7.5 lock-order-graph.py -- 锁序分析 (Phase 2 新增)

```bash
python3 scripts/lock-order-graph.py os/StarryOS/kernel/
```

输出: 锁序有向图，检测死锁环

### 7.6 pattern-scanner.py -- 模式扫描 (Phase 2 新增)

```bash
python3 scripts/pattern-scanner.py os/StarryOS/kernel/
```

输出: 基于 patterns.json 规则的扫描结果

### 7.7 local-ci.sh -- 本地 Docker CI (Phase 3 新增)

```bash
# 快速检查 (fmt + clippy)
bash scripts/local-ci.sh quick

# 完整 CI
bash scripts/local-ci.sh full

# 仅 StarryOS 测试
bash scripts/local-ci.sh starry --arch riscv64

# 指定架构
bash scripts/local-ci.sh full --arch aarch64
```

---

## 八、典型工作流

### 8.1 实现新 syscall

```
1. @os-architect 我需要实现 getxattr syscall
   → os-architect 调用 os-feature 技能
   → 使用 gen-syscall.py 生成模板
   → 实现具体逻辑

2. 请运行测试
   → os-test 技能 (Phase 1)
   → 先在 Docker Linux 上测试
   → 再在 StarryOS QEMU 上测试
   → 对比结果

3. @code-reviewer 评审我的实现
   → os-review 技能
   → 8 维评审

4. 准备 PR
   → os-pr-workflow 技能 (Phase 1)
   → fmt → clippy → tests → review → PR
```

### 8.2 调试内核 panic

```
1. QEMU 报错: panicked at src/task/run_queue.rs:456
   → 自动触发 qemu-log-watcher
   → 自动触发 os-debug 技能

2. @kernel-debugger 分析这个 panic
   → 读取源码，定位问题
   → 输出: Root cause, Suggested fix, Files to modify

3. 应用修复

4. 验证修复
   → 运行测试
   → 检查无回归
```

### 8.3 代码评审

```
1. @code-reviewer 审查这个 PR
   → Fresh Eyes Protocol (Phase 2 增强)
   → 独立子 agent 上下文
   → 8 维评审
   → 评审信心评分

2. 处理评审意见
   → 修改代码
   → 重新评审

3. 提交 PR
   → PR 门控检查
   → 自动生成 PR 模板
```

---

## 九、环境要求

### 必需

- Claude Code CLI (最新版)
- Rust nightly (版本见 tgoskits/rust-toolchain.toml)
- QEMU (支持 riscv64/aarch64/x86_64/loongarch64)
- musl 交叉编译器 (musl-gcc, musl-riscv64-gcc 等)

### 推荐

- Docker (用于 Linux 参考测试和 CI)
- tree-sitter Python 包 (用于 AST 级静态分析)
- Textual Python 包 (用于 TUI 仪表板，Phase 3)

### Docker 镜像

```bash
# 拉取 CI 镜像
docker pull ghcr.io/rcore-os/tgoskits-container:latest
```

---

## 十、配置文件

### plugin.json

```json
{
  "name": "os-biglab",
  "description": "OS development harness for StarryOS/ArceOS/Axvisor",
  "version": "1.0.0",
  "keywords": ["os", "kernel", "arceos", "starryos", "axvisor", "riscv", "aarch64", "debug", "syscall"]
}
```

### hooks.json (当前实际配置)

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "chmod +x ${CLAUDE_PLUGIN_ROOT}/scripts/*.sh ${CLAUDE_PLUGIN_ROOT}/scripts/*.py 2>/dev/null; echo '[os-biglab] plugin ready'"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/auto-fmt.sh"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/pre-pr-gate.sh",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

**关键点**:
- PreToolUse hook 拦截所有 Bash 命令，但只对 `gh pr create` 和 `git push` 生效
- clippy 零警告是 tgoskits 的硬性要求，任何 warning 都会阻塞 push
- hook 超时设为 5 秒，避免阻塞正常操作

---

## 十一、故障排查

### 插件未加载

```bash
# 检查插件目录是否正确
ls -la /path/to/os-biglab-plugin/.claude-plugin/plugin.json

# 检查 hooks.json 格式
python3 -c "import json; json.load(open('/path/to/os-biglab-plugin/hooks/hooks.json'))"

# 以调试模式启动
claude --plugin-dir /path/to/os-biglab-plugin --verbose
```

### 自动格式化不工作

```bash
# 检查脚本权限
ls -la /path/to/os-biglab-plugin/scripts/auto-fmt.sh

# 手动测试
echo '{"tool_input":{"file_path":"/path/to/test.rs"}}' | bash /path/to/os-biglab-plugin/scripts/auto-fmt.sh
```

### QEMU 监控器不工作

```bash
# 确保日志文件存在
ls -la /tmp/os_run.log

# 手动测试 QEMU 日志重定向
cargo xtask starry qemu --arch riscv64 2>&1 | tee /tmp/os_run.log
```

---

## 十二、与 tgoskits 内置技能的关系

tgoskits 项目本身已有 9 个内置技能 (在 `.claude/skills/` 下):

| tgoskits 内置技能 | os-biglab 对应技能 | 关系 |
|-------------------|-------------------|------|
| starryos-debug | starryos-debug | 互补 (os-biglab 版更详细) |
| cross-kernel-driver | os-feature/driver-guide | 互补 |
| arceos-test-adapter | os-test (新增) | 互补 |
| starry-test-suit | os-test (新增) | 互补 |
| review-single-pr | os-review | 互补 |
| review-open-prs | os-pr-workflow (新增) | 互补 |
| update-std-tests | os-test (新增) | 互补 |
| board-uboot-fsck-repair | (无对应) | 独立功能 |
| crates-io-owner | (无对应) | 独立功能 |

**建议**: 两者可以共存，os-biglab-plugin 提供更系统化的工作流，tgoskits 内置技能提供项目特定的细节。在使用时根据具体场景选择。
