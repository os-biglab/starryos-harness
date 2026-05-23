# 基准测试目录

## Syscall 延迟

| 测试 | 说明 | 关键指标 |
|------|------|---------|
| bench_getpid | 最轻量 syscall | ns/op |
| bench_read_empty | read(0,NULL,0) | ns/op |
| bench_write_empty | write(1,"",0) | ns/op |
| bench_clock_gettime | 时间获取 | ns/op |
| bench_sched_yield | 调度让出 | ns/op |

## I/O 吞吐

| 测试 | 说明 | 关键指标 |
|------|------|---------|
| bench_write_sequential | 顺序写文件 | MB/s |
| bench_read_sequential | 顺序读文件 | MB/s |
| bench_write_random | 随机写 | IOPS |
| bench_read_random | 随机读 | IOPS |

## 上下文切换

| 测试 | 说明 | 关键指标 |
|------|------|---------|
| bench_ctx_switch_pipe | pipe 通信切换 | ns/switch |
| bench_ctx_switch_signal | 信号触发切换 | ns/switch |
| bench_ctx_switch_futex | futex 唤醒 | ns/switch |

## 内存分配

| 测试 | 说明 | 关键指标 |
|------|------|---------|
| bench_mmap_4k | 4K mmap | ns/op |
| bench_mmap_1m | 1M mmap | ns/op |
| bench_brk_small | brk 小分配 | ns/op |

## 文件系统

| 测试 | 说明 | 关键指标 |
|------|------|---------|
| bench_open_close | open+close | ops/sec |
| bench_stat | stat 单文件 | ops/sec |
| bench_readdir | 读目录 1000 文件 | ops/sec |
| bench_create_unlink | 创建+删除 | ops/sec |

## 多核扩展

| 测试 | 说明 | 关键指标 |
|------|------|---------|
| bench_smp_scaling | 1/2/4 核对比 | 加速比 |
| bench_atomic_inc | 原子递增争用 | ns/op |
| bench_spin_lock | 自旋锁争用 | ns/op |
