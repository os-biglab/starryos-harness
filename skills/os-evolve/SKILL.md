---
name: os-evolve
description: >
  Self-evolving orchestrator for continuous kernel improvement. Runs scan/audit/fix loops,
  maintains persistent strategy state, generates new detection rules from discovered bugs.
  Two modes: autonomous (system picks targets) and human-driven (top 5 recommendations).
  Use when the user wants to systematically improve kernel quality, find areas to work on,
  or run an automated improvement loop.
  Triggers: "evolve", "improve", "auto", "what should I work on", "find issues",
  "自动改进", "系统化提升", "找问题", "下一步做什么"
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, LSP
effort: high
---

# 自演化编排器

## 工作模式

### 模式 A: 人工驱动

用户选择目标，技能提供工具和工作流。

```
用户: 我应该做什么来改进 StarryOS?
Claude: 根据当前状态，推荐以下 5 个方向:
1. 补充 getxattr 系列 syscall (覆盖率低)
2. 修复 run_queue 中的并发问题 (P0)
3. 优化 syscall 延迟 (当前是 Linux 的 3x)
4. 添加 epoll 边界测试
5. 审查 unsafe 块的 SAFETY 注释
你想从哪个开始?
```

### 模式 B: 自主编排

系统自动选择目标，运行循环。

```
用户: 自动运行一轮改进
Claude:
  Round 1:
    1. pattern-scanner.py 扫描 → 发现 3 个新的 P2 问题
    2. 选择最高优先级: catch-all-match-arm in signal.rs
    3. 分析 → 修复 → 验证
    4. 更新 strategy.json

  Round 2:
    ...
```

## 7 条不可违反的原则

1. **Linux 定义正确性** -- 每个行为以 Linux 为准
2. **先测试再修复** -- 先写复现测试，再修代码
3. **先有证据再声称** -- 只报告有证据的问题
4. **一轮一个 bug** -- 不要一次修多个不相关的问题
5. **先有 harness 再有 patch** -- 每轮产出可复用的测试资产
6. **确定性工具优先** -- 用脚本扫描，不要只靠 LLM 推理
7. **评审有否决权** -- 独立评审可以打回修改

## 策略文件

维护 `docs/os-biglab-state/strategy.json`:

```json
{
  "coverage": {
    "syscalls_tested": 45,
    "syscalls_total": 204,
    "coverage_pct": 22
  },
  "bugs": {
    "found": 12,
    "fixed": 10,
    "open": 2
  },
  "categories": {
    "concurrency": {"found": 3, "fixed": 3},
    "memory": {"found": 2, "fixed": 2},
    "semantic": {"found": 5, "fixed": 4},
    "validation": {"found": 2, "fixed": 1}
  },
  "benchmarks": {
    "fast": 15,
    "slow": 5,
    "bottleneck": 2
  },
  "next_priorities": [
    "Fix remaining validation bugs",
    "Add epoll boundary tests",
    "Optimize write throughput"
  ]
}
```

## 反思周期

每 3-5 轮运行一次反思:
- 综合跨领域模式
- 生成新的检测规则 (更新 patterns.json)
- 更新优先级
- 生成进度报告

## 参考文件

- [strategy-schema.md](references/strategy-schema.md) -- strategy.json schema
- [review-pipeline.md](references/review-pipeline.md) -- 评审协议
