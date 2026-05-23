---
name: os-upstream-sync
description: >
  Sync local branch with upstream/dev for PR submission. Handles fetch, rebase,
  conflict resolution, squash rewrite, and post-sync verification (fmt, clippy, tests).
  Use when the user wants to rebase onto upstream/dev, resolve rebase conflicts,
  squash commits for a clean PR, or check sync status.
  Triggers: "rebase", "sync", "upstream", "conflict", "squash", "clean up commits",
  "同步", "rebase到最新", "解决冲突", "整理提交", "准备PR"
allowed-tools: Read, Grep, Glob, Bash, Edit, Write
effort: medium
---

# Upstream 同步工作流

将本地分支与 upstream/dev 同步，准备 PR 提交。

## 前置检查

在开始前确认:
1. 当前在正确的分支上 (`git branch --show-current`)
2. 没有未提交的修改 (`git status`)
3. remote `upstream` 已配置 (`git remote -v`)

如果 upstream 未配置:
```bash
git remote add upstream https://github.com/rcore-os/tgoskits.git
```

## 工作流 A: 标准 Rebase

适用于: 分支历史干净，只需要更新到最新 upstream。

### Step 1: 获取最新 upstream
```bash
git fetch upstream
git log --oneline upstream/dev -5  # 确认获取成功
```

### Step 2: 查看差异
```bash
# 当前分支与 upstream/dev 的差异
git log --oneline HEAD...upstream/dev --left-right
# left (>): 本地独有提交
# right (<): upstream 独有提交
```

### Step 3: 执行 rebase
```bash
git rebase upstream/dev
```

### Step 4: 处理冲突 (如有)

逐个文件解决:
```bash
# 查看冲突文件
git status

# 编辑冲突文件，解决冲突标记
# <<<<<<< HEAD (你的修改)
# ======= (upstream 的修改)
# >>>>>>> upstream/dev

# 解决后
git add <resolved-file>
git rebase --continue
```

**冲突分析策略**:
- 读取冲突文件的双方修改
- 理解 upstream 修改的意图 (通常是对 API 的改进或 bug 修复)
- 适配本地修改到新的 API/接口
- 如果不确定如何解决，询问用户

### Step 5: 验证
```bash
cargo fmt --all -- --check
cargo xtask clippy --since upstream/dev
cargo xtask sync-lint --since upstream/dev
cargo xtask test
```

### Step 6: 更新远程
```bash
git push --force-with-lease
```

## 工作流 B: Squash 重写

适用于: 分支历史太乱，想在 upstream/dev 基础上重写为干净的提交。

### Step 1: 记录当前修改
```bash
# 查看所有修改的文件
git diff upstream/dev...HEAD --stat

# 查看修改内容 (用于后续恢复)
git diff upstream/dev...HEAD > /tmp/my-changes.patch
```

### Step 2: 创建新分支
```bash
# 保存旧分支名
OLD_BRANCH=$(git branch --show-current)

# 从 upstream/dev 创建新分支
git checkout -b ${OLD_BRANCH}-clean upstream/dev
```

### Step 3: 应用修改

方式 A: 按文件恢复
```bash
# 从旧分支检出修改过的文件
git checkout $OLD_BRANCH -- path/to/file1.rs
git checkout $OLD_BRANCH -- path/to/file2.rs
```

方式 B: 使用 patch
```bash
git apply /tmp/my-changes.patch
```

方式 C: cherry-pick 特定提交
```bash
git cherry-pick <commit-hash>
```

### Step 4: 提交
```bash
git add -A
git commit -m "feat(scope): description"
```

### Step 5: 验证 (同工作流 A Step 5)

### Step 6: 替换原分支
```bash
# 切回原分支
git checkout $OLD_BRANCH

# 重置到新分支
git reset --hard ${OLD_BRANCH}-clean

# 删除临时分支
git branch -D ${OLD_BRANCH}-clean

# 更新远程
git push --force-with-lease
```

## 工作流 C: 冲突深度解决

当 rebase 冲突复杂时:

### 分析冲突类型

| 冲突类型 | 解决策略 |
|---------|---------|
| API 签名变更 | 适配本地调用到新签名 |
| 文件移动/重命名 | 确认新路径，调整 import |
| 逻辑冲突 | 分析双方意图，合并逻辑 |
| 依赖变更 | 更新 Cargo.toml |

### 具体操作

```
# 用户说: rebase 到 upstream/dev 时有冲突

Claude:

1. 分析冲突
$ git diff --name-only --diff-filter=U

2. 逐个读取冲突文件
→ 读取每个冲突标记的上下文
→ 理解 upstream 修改的意图
→ 理解本地修改的意图

3. 建议解决方案
→ 如果是 API 变更: "upstream 把 read() 的签名从 (fd, buf, count)
   改成了 (fd, buf, count, flags)，你的代码需要适配"
→ 如果是逻辑冲突: "upstream 修复了 xxx bug，你的修改也涉及同一区域，
   建议合并两者的逻辑"

4. 执行解决
→ 编辑冲突文件
→ git add <file>
→ git rebase --continue

5. 验证
→ cargo fmt + clippy + test
```

## 常见问题

### rebase 后编译失败

```
Claude:
1. 读取编译错误
2. 通常是 upstream 改了 API，本地代码需要适配
3. 修复编译错误
4. cargo fmt + clippy
5. 继续 rebase
```

### rebase 后 clippy 报错

```
Claude:
1. 运行 cargo xtask clippy --since upstream/dev
2. 分析每个 warning
3. 修复 (tgoskits 要求零警告)
4. git add + rebase --continue
```

### 不确定是否需要 squash

```
# 问用户:
你的分支有多少个 commit？
$ git log --oneline upstream/dev...HEAD

如果:
- 1-3 个: 直接 rebase 即可
- 4-10 个: 考虑 squash 相关的 commit
- 10+ 个: 建议 squash 成 1-2 个干净的 commit
```

## 输出格式

同步完成后，报告:
```
## 同步完成

- 基础分支: upstream/dev (commit abc1234)
- 本地提交: 1 个 (feat(starry-syscall): add getxattr)
- 冲突: 无 / 已解决 N 个
- 验证:
  - [x] cargo fmt --all -- --check
  - [x] cargo xtask clippy (零警告)
  - [x] cargo xtask sync-lint
  - [x] cargo xtask test
- 远程: 已更新 (force-with-lease)

可以准备提交 PR 了。
```
