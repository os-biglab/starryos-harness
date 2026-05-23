---
name: os-pr-workflow
description: >
  PR preparation and submission workflow for tgoskits. Covers branch setup, local CI
  validation (fmt, clippy zero-warning, sync-lint, std tests, QEMU tests), PR description
  generation, and submission guidance. Never auto-submits PRs.
  Use when the user wants to prepare a PR, validate before push, generate PR description,
  or check CI readiness.
  Triggers: "PR", "pull request", "prepare PR", "submit", "push", "CI check",
  "提交PR", "准备PR", "检查CI", "可以提交了吗", "clippy过了吗"
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, LSP
effort: high
---

# PR 准备工作流

## 核心原则

1. **永远不自动提交 PR** -- 只准备和验证，最终提交由用户手动完成
2. **clippy 零警告** -- tgoskits 硬性要求，任何 warning 都阻塞
3. **基于 dev 分支** -- PR 必须基于 upstream/dev

## 工作流

### Phase 1: 分支准备

确认分支状态:
```bash
# 当前分支
git branch --show-current

# 与 upstream/dev 的差异
git log --oneline upstream/dev...HEAD

# 如果需要同步
git fetch upstream
git rebase upstream/dev
```

### Phase 2: 本地 CI 验证

按顺序执行，任何一步失败都停止:

```bash
# Step 1: 格式检查
cargo fmt --all -- --check

# Step 2: clippy (零警告)
cargo xtask clippy --since upstream/dev

# Step 3: sync-lint (原子序检查)
cargo xtask sync-lint --since upstream/dev

# Step 4: std 测试
cargo xtask test

# Step 5: QEMU 测试 (至少一个架构)
cargo xtask starry qemu --arch riscv64
```

如果任何步骤失败:
- fmt 失败 → `cargo fmt --all` 自动修复
- clippy 失败 → 分析每个 warning 并修复
- sync-lint 失败 → 检查 Ordering::Relaxed 使用
- test 失败 → 分析测试输出
- QEMU 失败 → 使用 os-debug 技能诊断

### Phase 3: 生成 PR 描述

基于变更内容生成 PR 描述:

```markdown
## 标题
<type>(<scope>): <description>
# type: feat/fix/refactor/test/docs/chore
# scope: starry-syscall, arceos-alloc, driver-virtio, etc.

## 概述
<1-2 句描述变更的目的>

## 修改内容
- <具体修改 1>
- <具体修改 2>

## 测试
- [x] cargo fmt --all -- --check
- [x] cargo xtask clippy (零警告)
- [x] cargo xtask sync-lint
- [x] cargo xtask test
- [x] QEMU <arch> 测试通过

## 关联
- <相关 issue/PR/文档>
```

### Phase 4: 提交指导

告诉用户执行:
```bash
# 推送分支
git push origin <branch>

# 创建 PR (手动)
gh pr create --base dev --title "<title>" --body "<body>"
```

## PR 规范

| 要求 | 说明 |
|------|------|
| 标题格式 | `type(scope): content` (英文, Conventional Commits) |
| 正文语言 | 中文 |
| 基础分支 | `dev` (不是 main) |
| AI 声明 | 不添加 AI/agent 签名 |
| clippy | 零警告 |
| 同步 | 修改代码后更新 PR 描述 |

## 快速检查

用户问"可以提交了吗"时，执行:
```bash
cargo fmt --all -- --check && \
cargo xtask clippy --since upstream/dev && \
echo "READY TO PUSH"
```

## 参考文件

- [pr-template.md](references/pr-template.md) -- PR 模板
