# 评审流水线

## 严重性缩放

评审轮数和 token 预算随 bug 严重性缩放:

| 严重性 | 评审轮数 | Token 预算 |
|--------|---------|-----------|
| P3 | 3 轮 | ~3K |
| P2 | 4 轮 | ~6K |
| P1 | 5-6 轮 | ~10K |
| P0 | 7-9 轮 | ~20K |

## 评审流程

### Round 1: 自查

修复者自己检查:
- fmt + clippy 通过
- 复现测试在修复前失败、修复后通过
- 无回归

### Round 2: kernel-reviewer agent

启动独立的 `kernel-reviewer` agent (Fresh Eyes Protocol):
- 不共享实现上下文
- 只读审查
- 输出: Critical / Warning / NIT

### Round 3: 回归检查

```bash
cargo xtask test
cargo xtask starry qemu --arch riscv64
```

### Round 4: (P0/P1) 独立重新推导

对于 P0/P1 级别的修复:
- 启动另一个 agent，只看 bug 描述
- 独立推导修复方案
- 与实际修复对比

### Round 5: (P0) 综合

综合所有评审意见:
- 不是投票，是综合
- 评审有否决权

## 收敛评估

| 信心度 | 条件 |
|--------|------|
| HIGH | 所有轮次通过，无 Critical finding |
| MEDIUM | 有 Warning 但已修复 |
| LOW | 存在未解决的 Critical |

## Stop Hook

如果修复被提出但评审流水线未完成，会话结束时阻塞:
```
WARNING: Fix proposed but review pipeline not completed.
         Complete review before closing session.
```
