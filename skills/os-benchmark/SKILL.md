---
name: os-benchmark
description: >
  Performance benchmarking for StarryOS. Compares syscall latency, I/O throughput,
  context switch time, memory allocation, filesystem ops, and multicore scaling against
  Linux baseline. Classifies results as FAST/SLOW/BOTTLENECK.
  Use when the user wants to measure performance, compare against Linux, find bottlenecks,
  or validate optimization improvements.
  Triggers: "benchmark", "performance", "latency", "throughput", "slow", "bottleneck",
  "性能", "基准测试", "优化", "慢", "卡顿"
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, LSP
effort: high
---

# 性能基准测试工作流

## 7 阶段流程

### Phase 1: 选择基准

确定要测试的类别:

| 类别 | 指标 | 示例 |
|------|------|------|
| syscall 延迟 | 单次调用时间 (ns) | read/write/getpid |
| I/O 吞吐 | bytes/sec | 文件读写、网络 |
| 上下文切换 | 切换时间 (ns) | 线程切换 |
| 内存分配 | 分配时间 (ns) | malloc/free |
| 文件系统 | ops/sec | open/close/stat |
| 多核扩展 | 加速比 | 1/2/4 核对比 |

### Phase 2: Linux 基线

在 Docker Linux 中运行相同的基准:

```bash
docker run --rm -v $(pwd):/work -w /work \
  ghcr.io/rcore-os/tgoskits-container:latest \
  ./benchmark_binary
```

记录 Linux 结果作为基线。

### Phase 3: StarryOS 测试

```bash
# 编译基准程序
musl-riscv64-gcc -static -O2 -o benchmark_binary benchmark.c

# 注入 rootfs 并运行
cargo xtask starry qemu --arch riscv64
```

### Phase 4: 对比分析

| 分类 | 阈值 | 说明 |
|------|------|------|
| FAST | ≤ 1.5x Linux | 可接受 |
| SLOW | 1.5x - 5x Linux | 需要关注 |
| BOTTLENECK | > 5x Linux | 必须优化 |

### Phase 5: 性能分析

对 BOTTLENECK 项:
- 追踪热点路径
- 检查锁争用
- 分析内存分配模式
- 检查不必要的拷贝

### Phase 6: 优化

针对瓶颈实施优化，每次只改一个点。

### Phase 7: 重测验证

优化后重新运行基准，确认改善幅度。

## 基准测试模板

```c
/*
 * 基准测试: syscall 延迟
 * 编译: musl-riscv64-gcc -static -O2 -o bench_syscall bench_syscall.c
 */
#include <stdio.h>
#include <time.h>
#include <unistd.h>
#include <sys/syscall.h>

#define ITERATIONS 100000

static inline long now_ns() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000000000L + ts.tv_nsec;
}

int main() {
    long start, end;

    // getpid - 最轻量的 syscall
    start = now_ns();
    for (int i = 0; i < ITERATIONS; i++) {
        syscall(SYS_getpid);
    }
    end = now_ns();
    printf("[BENCH] getpid: %ld ns/op (%d iterations)\n",
           (end - start) / ITERATIONS, ITERATIONS);

    // read(0, NULL, 0) - 应该快速返回
    start = now_ns();
    for (int i = 0; i < ITERATIONS; i++) {
        syscall(SYS_read, 0, NULL, 0);
    }
    end = now_ns();
    printf("[BENCH] read(0,NULL,0): %ld ns/op (%d iterations)\n",
           (end - start) / ITERATIONS, ITERATIONS);

    // write(1, "", 0) - 应该快速返回
    start = now_ns();
    for (int i = 0; i < ITERATIONS; i++) {
        syscall(SYS_write, 1, "", 0);
    }
    end = now_ns();
    printf("[BENCH] write(1,\"\",0): %ld ns/op (%d iterations)\n",
           (end - start) / ITERATIONS, ITERATIONS);

    return 0;
}
```

## 参考文件

- [benchmark-suite.md](references/benchmark-suite.md) -- 完整基准测试目录
