# strategy.json Schema

## 完整结构

```json
{
  "version": 1,
  "last_updated": "2026-05-23T10:00:00Z",
  "coverage": {
    "syscalls_tested": 45,
    "syscalls_total": 204,
    "coverage_pct": 22.1,
    "by_category": {
      "fs": {"tested": 15, "total": 60},
      "mm": {"tested": 8, "total": 25},
      "task": {"tested": 10, "total": 30},
      "signal": {"tested": 5, "total": 20},
      "net": {"tested": 3, "total": 40},
      "time": {"tested": 4, "total": 15},
      "misc": {"tested": 0, "total": 14}
    }
  },
  "bugs": {
    "found": 12,
    "fixed": 10,
    "open": 2,
    "by_severity": {
      "P0": {"found": 2, "fixed": 2, "open": 0},
      "P1": {"found": 5, "fixed": 4, "open": 1},
      "P2": {"found": 4, "fixed": 3, "open": 1},
      "P3": {"found": 1, "fixed": 1, "open": 0}
    },
    "by_category": {
      "concurrency": {"found": 3, "fixed": 3},
      "memory": {"found": 2, "fixed": 2},
      "semantic": {"found": 5, "fixed": 4},
      "validation": {"found": 2, "fixed": 1}
    }
  },
  "benchmarks": {
    "measured": 22,
    "fast": 15,
    "slow": 5,
    "bottleneck": 2,
    "worst": [
      {"name": "write_1mb", "ratio": 8.5, "category": "io"},
      {"name": "ctx_switch", "ratio": 5.2, "category": "scheduling"}
    ]
  },
  "analysis_queue": [
    {
      "target": "os/StarryOS/kernel/src/syscall/net.rs",
      "reason": "Low coverage, 0/40 net syscalls tested",
      "priority": 2,
      "estimated_effort": "medium"
    }
  ],
  "review_history": [
    {
      "date": "2026-05-23",
      "target": "signal.rs",
      "findings": 2,
      "fixed": 2,
      "new_rules": 1
    }
  ],
  "next_priorities": [
    "Fix P1 validation bug in mmap",
    "Add net syscall tests",
    "Optimize write throughput"
  ]
}
```

## 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `coverage.syscalls_tested` | int | 已测试的 syscall 数量 |
| `coverage.coverage_pct` | float | 覆盖率百分比 |
| `bugs.found` | int | 累计发现的 bug 数 |
| `bugs.fixed` | int | 累计修复的 bug 数 |
| `benchmarks.bottleneck` | int | 性能瓶颈项数量 |
| `analysis_queue` | array | 待分析的目标列表 |
| `next_priorities` | array | 下一步优先事项 |
