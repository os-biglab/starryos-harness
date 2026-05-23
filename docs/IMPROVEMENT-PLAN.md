# os-biglab-plugin 完善方案

> 基于 4 个参考项目的分析，结合 StarryOS/ArceOS/Axvisor 项目特点，制定本完善方案。

---

## 一、参考项目对比分析

### 1. starry-harness (v1.5.0)

**定位**: StarryOS 专用竞赛级工程 harness

| 维度 | 特点 |
|------|------|
| 核心理念 | **Linux 定义正确性** -- 每个测试必须先在 Docker Linux 上通过 |
| 技能数量 | 9 个 (hunt-bugs, audit-kernel, benchmark, test-app, review-quality, report, evolve, start-submission, check-upstream) |
| Agent 数量 | 3 个 (kernel-reviewer, linux-comparator, bug-triager) |
| 脚本数量 | 16 个 (pipeline.sh, linux-ref-test.sh, stress-test.sh, lock-order-graph.py, pattern-scanner.py, abi-check.py, rust_analyzer.py 等) |
| 核心创新 | 反幻觉协议(7 级验证)、模式进化(patterns.json)、Rust 所有权感知静态分析、自演化循环 |
| 持久状态 | strategy.json(策略)、journal.md(日志)、known.json(缺陷登记)、patterns.json(检测规则) |
| 评审流水线 | 按严重性缩放轮数(P3:3轮 → P0:9轮)，独立子 agent 评审 |
| 竞赛适配 | 5 类缺陷分类、性能基准、应用兼容性、上游 PR 准备 |

**借鉴价值**: Linux-first 测试纪律、反幻觉协议、模式进化机制、确定性工具优先

---

### 2. tgoskits-plugin (v0.1.0)

**定位**: TGOSKits 项目级 Claude Code 插件

| 维度 | 特点 |
|------|------|
| 核心理念 | **上下文隔离** -- Fresh Eyes Protocol 防止自审偏见 |
| Agent 数量 | 6 个 (pr-review, bug-hunt, impl, test-gen, self-evolve, driver-audit) |
| Hook 数量 | 4 个生命周期点 (SessionStart, PreToolUse, PostToolUse, Stop) |
| 脚本数量 | 12 个 (docker-check.py, pre-pr-gate.py, post-tool-use-log.py, review-gate.py, stop-hook.py, local-ci.sh, syscall-diff.py 等) |
| 核心创新 | Fresh Eyes Protocol、自演化 agent、PR 门控、活动日志、会话结束日志生成 |
| 依赖管理 | 依赖 superpowers + pr-review-toolkit，SessionStart 验证 |
| CI 矩阵 | 3 OS × 4 架构，Docker 镜像缓存，哈希触发重建 |

**借鉴价值**: Fresh Eyes Protocol、PR 门控 hook、活动日志系统、依赖验证

---

### 3. Auto-OS

**定位**: AI 驱动的内核自动缺陷发现与修复系统

| 维度 | 特点 |
|------|------|
| 核心理念 | **双 Agent 闭环** -- Debugger 发现 + Executor 修复 |
| 架构 | Python 调度内核 + 文件系统 IPC + TUI 仪表板 |
| Agent | 2 个 (debugger, executor) + 自主编排调度 |
| 测试系统 | 4 层测试 (L1: AI 生成 C 测试, L2: LTP 子集, L3: 集成测试, L4: 竞赛官方) |
| 核心创新 | 自主运行闭环、结构化 Issue 生命周期、基于 patch 的开发模型、自宿主编排 |
| 成果 | 3.5 小时发现 245 个问题，修复 244 个，426 个提交 |

**借鉴价值**: 双 Agent 闭环模式、结构化 Issue 管理、多层测试体系

---

### 4. polyglot-agent-harness

**定位**: 跨 IDE 的可移植 AI 工程 harness

| 维度 | 特点 |
|------|------|
| 核心理念 | **一份规范，多端运行** -- AGENTS.md 为唯一真相源 |
| 支持工具 | Claude Code / Cursor / Trae / Codex CLI |
| 技能数量 | 7 个 (experiment-guard, pr-workflow, report-generator, test-authoring, auto-skill-maintainer, completion-examiner, harness-overview) |
| 核心创新 | 自动技能维护、强制技能声明协议、证据驱动完成模型、Docker 感知预检 |

**借鉴价值**: 自动技能维护机制、证据驱动完成模型、强制技能声明

---

## 二、os-biglab-plugin 现状分析

### 已完成

| 组件 | 数量 | 状态 |
|------|------|------|
| Skills | 5 个 (os-debug, os-feature, os-review, os-nav, starryos-debug) | ✅ 完整 |
| Agents | 3 个 (kernel-debugger, os-architect, code-reviewer) | ✅ 完整 |
| Hooks | 2 个 (PostToolUse auto-fmt, SessionStart init) | ⚠️ 基础 |
| Monitors | 1 个 (qemu-log-watcher) | ⚠️ 基础 |
| Scripts | 4 个 (auto-fmt.sh, auto-clippy.sh, gen-syscall.py, parse-qemu-log.py) | ⚠️ 基础 |
| Plugin manifest | .claude-plugin/plugin.json | ✅ 完整 |

### 缺失项

| 缺失维度 | 严重性 | 说明 |
|----------|--------|------|
| 测试技能 | 🔴 高 | 无系统化测试工作流 (对比 starry-harness 的 hunt-bugs + test-app) |
| 缺陷管理 | 🔴 高 | 无缺陷登记、分类、跟踪 (对比 tgoskits-plugin 的 bug-hunt agent) |
| PR 工作流 | 🔴 高 | 无 PR 准备、评审、门控 (对比 starry-harness 的 start-submission) |
| 基准测试 | 🟡 中 | 无性能基准测试工作流 (对比 starry-harness 的 benchmark) |
| Linux 对照 | 🔴 高 | 无 Docker Linux 参考测试 (starry-harness 的核心理念) |
| 自演化 | 🟡 中 | 无技能自动发现与改进机制 |
| 反幻觉协议 | 🟡 中 | 无验证等级、无幻觉防护 |
| 模式检测 | 🟡 中 | 无静态分析模式扫描 (starry-harness 的 pattern-scanner.py) |
| 持久状态 | 🟡 中 | 无策略文件、日志、缺陷登记表 |
| CI 集成 | 🟡 中 | 无本地 Docker CI 运行 |
| 活动日志 | 🟡 中 | 无编辑活动跟踪 (tgoskits-plugin 的 post-tool-use-log.py) |
| PR 门控 | 🟡 中 | 无 PR/push 前置检查 (tgoskits-plugin 的 pre-pr-gate.py) |
| 路径硬编码 | 🟠 低 | auto-fmt.sh/auto-clippy.sh 硬编码 `/workspace` |
| 测试覆盖 | 🟠 低 | 插件自身无测试 |
| 停止钩子 | 🟠 低 | 无会话结束处理 (对比 tgoskits-plugin 的 stop-hook.py) |

---

## 三、完善方案

### 总体设计原则

1. **保留现有**: 5 个 Skills、3 个 Agents 已有良好基础，不推翻重来
2. **借鉴精华**: 从 4 个参考中选取最适合 StarryOS 的模式
3. **针对改进**: 结合 StarryOS 特点 (3 OS × 4 架构、cargo xtask 构建系统、workspace 成员 239 个)
4. **确保可用**: 每个改进都提供完整的使用说明

---

### Phase 1: 核心能力补全 (高优先级)

#### 1.1 新增 Skill: `os-test` -- 系统化测试工作流 ✅ 已实现

**来源借鉴**: starry-harness 的 `hunt-bugs` + `test-app` + `benchmark`

**设计**:
- 6 阶段测试流程: 选择目标 → Linux 参考测试 → StarryOS 测试 → 对比分析 → 缺陷报告 → 回归验证
- 4 种测试类型: Std / ArceOS QEMU / StarryOS QEMU / 并发压测
- **Linux-first 纪律**: 每个测试必须先在 Docker Linux 上通过

**文件**: `skills/os-test/SKILL.md` ✅ + 3 个 references ✅

#### 1.2 新增 Agent: `bug-hunter` -- 缺陷发现与分类 ✅ 已实现

**来源借鉴**: tgoskits-plugin 的 `bug-hunt` + starry-harness 的 `bug-triager`

**设计**:
- 两维度分类: 根因 × 表现
- 5 阶段工作流: 发现 → 复现 → 修复 → 验证 → 报告
- 强制 Synchronization Boundary Audit (并发缺陷时)
- 按严重性分级: P0 → P3

**文件**: `agents/bug-hunter.md` ✅

#### 1.3 新增 Skill: `os-pr-workflow` -- PR 准备与评审 ✅ 已实现

**来源借鉴**: starry-harness 的 `start-submission` + tgoskits-plugin 的 `pr-prep` 命令

**设计**:
- 5 阶段: 分支准备 → 编码 → CI 验证 → 独立评审 → PR 提交
- CI 门控: fmt → clippy → sync-lint → std tests → QEMU tests
- PR 模板: 中文正文 + Conventional Commits 标题
- **永远不自动提交 PR**

**文件**: `skills/os-pr-workflow/SKILL.md` ✅ + references ✅

#### 1.4 修复路径硬编码 ✅ 已实现

**问题**: `auto-fmt.sh` 和 `auto-clippy.sh` 硬编码 `/workspace`

**修复**: 使用 `${CLAUDE_PROJECT_DIR}` 环境变量，回退到 `git rev-parse --show-toplevel`

#### 1.5 新增 Skill: `os-learn` -- OS 学习文档生成 ✅ 已实现

**设计**:
- 基于 StarryOS/ArceOS/Axvisor 源码生成结构化学习文档
- 支持: syscall 机制、进程管理、内存管理、信号处理、文件系统、网络、驱动模型
- 输出: 概述 → 执行流程 → 关键数据结构 → 关键函数 → Linux 对比 → 代码导航表 → 动手实验
- 支持跨 OS 对比 (ArceOS vs StarryOS vs Axvisor)

**文件**: `skills/os-learn/SKILL.md` ✅

#### 1.6 新增 Skill: `os-upstream-sync` -- 上游同步 ✅ 已实现

**设计**:
- 三种工作流: 标准 Rebase / Squash 重写 / 冲突深度解决
- 自动验证: fmt → clippy → sync-lint → test
- 冲突分析: 识别冲突类型 (API 变更/文件移动/逻辑冲突/依赖变更)
- 输出同步报告

**文件**: `skills/os-upstream-sync/SKILL.md` ✅

---

### Phase 2: 工程纪律加强 (中优先级)

#### 2.1 新增 Hook: PreToolUse -- PR 门控 ✅ 已实现

**来源借鉴**: tgoskits-plugin 的 `pre-pr-gate.py`

**功能**:
- 拦截 `gh pr create` 和 `git push` 命令
- Gate 1: 禁止直接推 main/master/dev 分支
- Gate 2: `cargo fmt --all -- --check` 必须通过
- Gate 3: `cargo xtask clippy --since HEAD~1` **零警告** (tgoskits 硬性要求)

**文件**: `scripts/pre-pr-gate.sh` ✅

**关键设计**: tgoskits 要求 clippy 不能出现任何 warning，这是提交前的硬性门控。clippy 检查使用增量模式 (`--since HEAD~1`) 以加快速度。

#### 2.2 新增 Hook: PostToolUse -- 活动日志 ✅ 已实现

**来源借鉴**: tgoskits-plugin 的 `post-tool-use-log.py`

**功能**: 记录 Edit/Write 操作到 `docs/os-biglab-logs/activity.md`，自动去重

**文件**: `scripts/activity-logger.py` ✅

#### 2.3 新增 Hook: Stop -- 会话结束处理 ✅ 已实现

**来源借鉴**: tgoskits-plugin 的 `stop-hook.py`

**功能**: 从活动生成会话总结 (修改文件列表、活动时间线)

**文件**: `scripts/session-stop.py` ✅

#### 2.4 新增 Monitor: `git-change-tracker`

**来源借鉴**: starry-harness 的 `change-tracker.py`

**功能**:
- 监控 git diff，识别变更影响的子系统
- 交叉引用已知缺陷 (known.json)
- 当变更影响并发路径时，衰减并发发现的置信度

**文件**: `monitors/git-change-tracker.json`

#### 2.5 反幻觉协议 ✅ 已实现

**来源借鉴**: starry-harness 的 verification-discipline (7 级验证)

**设计**: 7 级验证体系，只报告 1-5 级证据，7 种常见幻觉陷阱文档

**文件**: `skills/os-review/references/anti-hallucination.md` ✅

#### 2.6 确定性分析脚本 ✅ 已实现

**来源借鉴**: starry-harness 的 `lock-order-graph.py` + `pattern-scanner.py` + `abi-check.py`

**已实现**:
1. `scripts/lock-order-graph.py` ✅ -- 锁序图构建，死锁检测
2. `scripts/pattern-scanner.py` ✅ -- 模式扫描器 (基于 patterns.json)
3. `scripts/abi-check.py` ✅ -- syscall ABI 一致性检查 (100+ Linux syscall 参考表)
4. `docs/os-biglab-patterns/patterns.json` ✅ -- 9 条默认检测规则

---

### Phase 3: 高级能力 (中低优先级)

#### 3.1 新增 Skill: `os-benchmark` -- 性能基准测试 ✅ 已实现

**设计**: 7 阶段流程，6 类基准，FAST/SLOW/BOTTLENECK 分类

**文件**: `skills/os-benchmark/SKILL.md` ✅ + references ✅

#### 3.2 自演化机制 ✅ 已实现

**设计**: 两种模式 (自主/人工驱动)，7 条不可违反的原则，策略文件维护

**文件**: `skills/os-evolve/SKILL.md` ✅ + references ✅

#### 3.3 新增 Agent: `test-generator` -- 测试用例生成 ✅ 已实现

**设计**: 6 类测试 (正常/无效参数/NULL/边界/资源耗尽/信号)，生成 per-arch QEMU 配置

**文件**: `agents/test-generator.md` ✅

#### 3.4 持久状态管理

**来源借鉴**: starry-harness 的 strategy.json + journal.md + known.json

**新增数据文件**:
```
docs/os-biglab-state/
├── strategy.json              # 覆盖率、有效性指标、分析队列、优先级
├── journal.md                 # 运行工作日志
├── known.json                 # 缺陷登记表 (per-syscall 状态)
└── patterns.json              # 可进化的检测规则 (9 条默认规则)
```

#### 3.5 Docker CI 本地运行

**来源借鉴**: tgoskits-plugin 的 `local-ci.sh` + `docker-ci.toml`

**设计**:
- 支持 quick/full/fmt/clippy/starry/arceos/axvisor 范围
- 支持 aarch64/riscv64/x86_64/loongarch64/all 架构
- Docker 镜像: `ghcr.io/rcore-os/tgoskits-container:latest`
- 哈希触发重建 (Dockerfile + rust-toolchain.toml)

**文件**: `scripts/local-ci.sh` + `config/docker-ci.toml`

---

### Phase 4: 现有组件增强

#### 4.1 增强 `os-debug` 技能

- 集成反幻觉协议 (参考 starry-harness)
- 添加并发缺陷复现技巧 (参考 starry-harness 的 concurrency-reproduction.md)
- 添加 QEMU + GDB 高级调试工作流

#### 4.2 增强 `os-review` 技能

- 添加反幻觉协议检查
- 添加 Rust 所有权感知分析 (参考 starry-harness 的 rust_analyzer.py)
- 评审信心评分 (0-100)

#### 4.3 增强 `starryos-debug` 技能

- 添加更多 panic 模式 (参考 Auto-OS 的发现)
- 集成 parse-qemu-log.py 输出
- 添加 debugcon 日志高级过滤

#### 4.4 增强 `kernel-debugger` agent

- 添加强制输出格式: "Root cause:" / "Evidence:" / "Suggested fix:" / "Files to modify:"
- 添加验证等级声明 (反幻觉协议)
- 添加并发审计步骤

#### 4.5 增强 `code-reviewer` agent

- 添加 Fresh Eyes Protocol (参考 tgoskits-plugin 的 CPI-06)
- 添加 5 维质量门控 (参考 starry-harness 的 review-quality)
- 添加评审信心评分

---

## 四、新增文件清单

### Skills (新增 4 个)

| 路径 | 说明 |
|------|------|
| `skills/os-test/SKILL.md` | 系统化测试工作流 |
| `skills/os-test/references/test-pipeline.md` | 测试流水线说明 |
| `skills/os-test/references/linux-comparison.md` | Docker Linux 对照方法 |
| `skills/os-test/references/test-templates.md` | C 测试模板 |
| `skills/os-pr-workflow/SKILL.md` | PR 准备与评审工作流 |
| `skills/os-pr-workflow/references/pr-template.md` | PR 模板 |
| `skills/os-benchmark/SKILL.md` | 性能基准测试 |
| `skills/os-benchmark/references/benchmark-suite.md` | 基准测试目录 |
| `skills/os-evolve/SKILL.md` | 自演化编排器 |
| `skills/os-evolve/references/strategy-schema.md` | 策略 schema |
| `skills/os-evolve/references/review-pipeline.md` | 评审协议 |

### Agents (新增 2 个)

| 路径 | 说明 |
|------|------|
| `agents/bug-hunter.md` | 缺陷发现与分类 |
| `agents/test-generator.md` | 测试用例生成 |

### Hooks (新增 3 个脚本)

| 路径 | 说明 | 状态 |
|------|------|------|
| `scripts/pre-pr-gate.sh` | PR 门控 (clippy 零警告 + fmt + 分支保护) | ✅ 已实现 |
| `hooks/scripts/activity-logger.py` | 活动日志 | 待实现 |
| `hooks/scripts/session-stop.py` | 会话结束处理 | 待实现 |

### Scripts (新增 4 个)

| 路径 | 说明 |
|------|------|
| `scripts/lock-order-graph.py` | 锁序图 + 死锁检测 |
| `scripts/pattern-scanner.py` | 模式扫描器 |
| `scripts/abi-check.py` | syscall ABI 检查 |
| `scripts/local-ci.sh` | 本地 Docker CI |

### References (新增 2 个到现有技能)

| 路径 | 说明 |
|------|------|
| `skills/os-review/references/anti-hallucination.md` | 反幻觉协议 |
| `skills/os-review/references/concurrency-reproduction.md` | 并发复现技巧 |

### Data Files (新增 2 个)

| 路径 | 说明 |
|------|------|
| `docs/os-biglab-patterns/patterns.json` | 可进化检测规则 |
| `config/docker-ci.toml` | Docker CI 配置 |

### 现有文件修改

| 路径 | 修改内容 | 状态 |
|------|----------|------|
| `scripts/auto-fmt.sh` | 修复路径硬编码，使用 `${CLAUDE_PROJECT_DIR}` | ✅ 已实现 |
| `scripts/auto-clippy.sh` | 修复路径硬编码，使用 `${CLAUDE_PROJECT_DIR}` | ✅ 已实现 |
| `hooks/hooks.json` | 添加 PreToolUse 钩子 (clippy 门控) | ✅ 已实现 |
| `monitors/monitors.json` | 添加 git-change-tracker 监控器 | 待实现 |

---

## 五、当前实现状态 ✅ 全部完成

```
os-biglab-plugin/
├── .claude-plugin/plugin.json        # ✅
├── README.md                         # ✅
│
├── agents/ (5 个)                    # ✅ 全部实现
│   ├── bug-hunter.md                 # 缺陷发现与分类
│   ├── code-reviewer.md              # 代码审查
│   ├── kernel-debugger.md            # 内核诊断
│   ├── os-architect.md               # 架构设计+实现
│   └── test-generator.md             # 测试用例生成
│
├── hooks/hooks.json                  # ✅ 4 个生命周期点
│   SessionStart → chmod + echo ready
│   PostToolUse → auto-fmt + activity-logger
│   PreToolUse → clippy zero-warning gate
│   Stop → session summary
│
├── scripts/ (10 个)                  # ✅ 全部实现
│   ├── abi-check.py                  # syscall ABI 检查
│   ├── activity-logger.py            # 活动日志
│   ├── auto-clippy.sh                # clippy 检查
│   ├── auto-fmt.sh                   # 自动格式化
│   ├── gen-syscall.py                # syscall 代码生成
│   ├── lock-order-graph.py           # 锁序分析+死锁检测
│   ├── parse-qemu-log.py             # QEMU 日志解析
│   ├── pattern-scanner.py            # 模式扫描器
│   ├── pre-pr-gate.sh                # PR 门控 (clippy 零警告)
│   └── session-stop.py               # 会话总结
│
├── skills/ (10 个)                   # ✅ 全部实现
│   ├── os-benchmark/                 # 性能基准测试
│   ├── os-debug/                     # 内核调试
│   ├── os-evolve/                    # 自演化编排
│   ├── os-feature/                   # 功能实现
│   ├── os-learn/                     # OS 学习文档生成
│   ├── os-nav/                       # 代码导航
│   ├── os-pr-workflow/               # PR 准备工作流
│   ├── os-review/                    # 代码评审 (+反幻觉协议)
│   ├── os-test/                      # 系统化测试
│   ├── os-upstream-sync/             # 上游同步
│   └── starryos-debug/               # StarryOS 专用调试
│
├── monitors/monitors.json            # ✅ QEMU 日志监控
│
└── docs/                             # ✅ 全部文档
    ├── IMPROVEMENT-PLAN.md
    ├── USAGE-GUIDE.md
    ├── SCENARIOS.md
    └── os-biglab-patterns/patterns.json
```

---

## 六、与参考项目的差异化改进

### 1. StarryOS 三合一架构支持

starry-harness 仅关注 StarryOS，而 os-biglab-plugin 需要同时支持 **ArceOS + StarryOS + Axvisor** 三个系统。改进:
- 测试技能支持三种 OS 的不同测试模式
- PR 工作流根据变更的 OS 自动调整 CI 矩阵
- 缺陷分类覆盖 Axvisor 特有的虚拟化缺陷类型

### 2. cargo xtask 深度集成

所有脚本使用 `cargo xtask` 而非原始 cargo 命令，与 StarryOS 构建系统完全对齐:
- `cargo xtask clippy --package <crate>` 替代 `cargo clippy`
- `cargo xtask test` 替代 `cargo test`
- `cargo xtask starry qemu --arch <arch>` 替代手动 QEMU 启动

### 3. 239 成员 workspace 感知

StarryOS workspace 有 239 个成员，规模远超普通项目。改进:
- 增量 clippy: `cargo xtask clippy --since <ref>` 仅检查变更
- 智能测试选择: 根据变更文件映射到受影响的测试
- 依赖图分析: 识别变更的级联影响

### 4. 四架构统一测试

支持 aarch64/riscv64/x86_64/loongarch64，比 starry-harness 多一个架构:
- 默认在 riscv64 上快速迭代
- 架构相关代码变更时自动交叉验证
- per-arch QEMU 配置生成

### 5. 中文优先的报告系统

参考 tgoskits-plugin 和 Auto-OS 的中文报告传统:
- PR body 使用中文
- 缺陷报告使用中文
- 工作日志使用中文
- 评审注释使用中文行内评论

### 6. 插件自测试

参考 tgoskits-plugin 的测试脚本 (test_preamble_consistency.sh, test_frontmatter_tools.sh):
- 验证所有 agent 前置声明一致性
- 验证所有技能 frontmatter 工具声明
- 验证所有脚本可执行性

---

## 七、实施顺序

| 阶段 | 内容 | 预计工作量 |
|------|------|-----------|
| Phase 1 | 核心能力补全 (os-test, bug-hunter, os-pr-workflow, 路径修复) | 高 |
| Phase 2 | 工程纪律加强 (hooks, monitors, 反幻觉, 确定性脚本) | 中 |
| Phase 3 | 高级能力 (os-benchmark, os-evolve, test-generator, 持久状态, Docker CI) | 中 |
| Phase 4 | 现有组件增强 (5 个现有技能/agent 增强) | 低 |

建议从 Phase 1 开始，每完成一个阶段即可投入使用并获得反馈。
