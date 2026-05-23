---
name: starryos-debug
description: Debug StarryOS / ArceOS kernel issues using QEMU debugcon log, cargo fmt, and clippy. Use when the user reports a kernel panic, TUI lag, epoll/poll/select regression, wrong syscall behavior, compile error after rebase, or asks to run fmt/clippy on kernel code. Covers the full loop: read debugcon.log → identify root cause → patch → fmt → clippy → verify.
---

# StarryOS Kernel Debug

完整调试循环：`debugcon log → 定位问题 → 修复 → fmt → clippy → 验证`。

---

## 1. QEMU debugcon 日志

### 启用方式

`cargo starry qemu` 默认已在 QEMU 命令行里加了 `-debugcon file:/tmp/debugcon.log`。
内核侧：`starry-kernel/Cargo.toml` 里 `ax-log = { workspace = true, features = ["debugcon-only"] }` 可把 warn/error 级别日志只路由到 debugcon，不输出到串口终端。

### 读取 log

```bash
# 实时追踪（QEMU 运行中）
tail -f /tmp/debugcon.log

# 查看全量
cat /tmp/debugcon.log

# 过滤 panic / error
grep -E "panicked|WARN|ERROR" /tmp/debugcon.log

# 只看进程生命周期（fork/exec/exit）
grep -E "do_clone|sys_execve|exit with code" /tmp/debugcon.log
```

### log 格式

```
[  0.362873 0:8 starry_kernel::syscall::task::clone:291] do_clone: ...
```

字段顺序：`[时间戳_秒.微秒  cpu_id:task_id  模块路径:行号] 消息`

### debugcon-only feature

只想把 warn+ 日志写到 debugcon、串口保持干净时，在 `ax-log/Cargo.toml` 里：

```toml
[features]
debugcon-only = []
```

在 `ax-log/src/lib.rs` 的 `Log::log()` 里用：

```rust
#[cfg(not(all(target_arch = "x86_64", feature = "debugcon-only")))]
let uart_enabled = true;
#[cfg(all(target_arch = "x86_64", feature = "debugcon-only"))]
let uart_enabled = false;
```

然后把所有 `__print_impl(...)` 调用包在 `if uart_enabled { ... }` 里。

---

## 2. 常见 panic 模式与定位

### 2.1 Re-entrant mutex panic

```
panicked at os/StarryOS/kernel/src/task/user.rs:38:52:
assertion left != right failed: Thread(N) tried to acquire mutex it already owns.
```

**根因模式**：`AxWaker::wake_by_ref()` 对 `WaitQueue::wait_until` 里阻塞的任务发出 spurious 唤醒 → 任务重入 `blocked_resched` 时 `in_wait_queue` 未清零 → 被 double-add 到等待队列 → `notify_one_with` 把 owner_id 写成该任务的 ID → 任务再次加锁时撞上自己。

**定位**：在 debugcon.log 里找 panicked，向上找最近的 `do_clone` / `sys_execve` 确定哪个任务出问题；再看 `task::user.rs` 报错行附近的互斥量加锁逻辑。

**通用修法（run_queue.rs `blocked_resched`）**：

```rust
if !curr.in_wait_queue() {
    curr.set_in_wait_queue(true);
    wq_guard.push_back(curr.clone());
}
```

### 2.2 AxWaker preemptive wakeup

`AxWaker::wake_by_ref()` 里 `resched=false` 会让 I/O 事件最多延迟一个 timer tick（10 ms，100 Hz 时钟）。改成 `resched=true` 可立即抢占：

```rust
// os/arceos/modules/axtask/src/future/mod.rs
fn wake_by_ref(self: &Arc<Self>) {
    if let Some(task) = self.task.upgrade() {
        let mut rq = select_run_queue::<NoPreemptIrqSave>(&task);
        *self.woke.lock() = true;
        rq.unblock_task(task, true);   // true = preemptive
    }
}
```

### 2.3 编译错误：API 重命名（rebase 后）

rebase 后上游可能重命名接口，典型例子：

```
error[E0599]: no method named `poll_events` found for struct `Arc<Epoll>`
help: there is a method `poll_events_with` with a similar name
```

在 `syscall/io_mpx/epoll.rs` 里把旧调用替换成新签名：

```rust
// 旧
epoll.poll_events(&mut kevents)

// 新（poll_events_with 写回方式）
epoll.poll_events_with(maxevents, |index, event| {
    kevents[index] = event;
    Ok(())
})
```

### 2.4 PTY/TUI 输出延迟（ldisc 缓冲区太小）

现象：jcode TUI 输入/输出明显卡顿，shell 命令完成后很久才出现提示符。

根因：`ldisc.rs` 里 `BUF_SIZE = 80`，PTY 底层 `slave_to_master` 是 4096 字节。每次 `poll_read()` 只能搬运 80 字节，500 字节的 shell 输出需要 7 次 epoll 轮次（Tokio 用 EPOLLET）。

修法：把 `BUF_SIZE` 提升到 4096，`SimpleReader::poll()` 改成循环排空：

```rust
const LINE_BUF_SIZE: usize = 128;   // 行处理 scratch buffer
const BUF_SIZE: usize = 4096;        // ring buffer，与 PTY_BUF_SIZE 对齐

// SimpleReader::poll()
pub fn poll(&mut self) {
    loop {
        if self.buf_tx.vacant_len() == 0 { break; }
        let read = self.reader.read(&mut self.read_buf);
        if read == 0 { break; }
        let pushed = self.buf_tx.push_slice(&self.read_buf[..read]);
        if pushed < read { break; }
    }
}
```

---

## 3. cargo fmt

**只格式化 kernel 包**（最常用）：

```bash
cd /workspace/os
cargo fmt --package starry-kernel
```

**格式化整个 workspace**（慎用，影响范围广）：

```bash
cd /workspace
cargo fmt
```

fmt 不输出任何内容时表示成功（`echo $?` 应为 0）。

---

## 4. cargo clippy

**只检查 kernel 包，x86_64 target**：

```bash
cd /workspace/os
cargo clippy --package starry-kernel --target x86_64-unknown-none 2>&1 | grep -E "^error|^warning\[|Finished"
```

**看完整输出**（含所有 warning 上下文）：

```bash
cargo clippy --package starry-kernel --target x86_64-unknown-none 2>&1 | tail -40
```

### 常见 clippy warning 处理

| warning | 处理方式 |
|---|---|
| `dead_code` on a public method | 加 `#[allow(dead_code)]`（若该方法确实无调用者但需要保留接口） |
| `unused_variable` | 加 `_` 前缀或删除 |
| `clippy::unnecessary_...` | 按提示简化，或 `#[allow(clippy::...)]` 并说明原因 |

---

## 5. 调试后的提交流程

1. 确认 `cargo build` 无 error。
2. 运行 `cargo fmt --package starry-kernel`。
3. 运行 `cargo clippy --package starry-kernel --target x86_64-unknown-none`，确认 `Finished` 行前无 `error[`。
4. 只 stage 与 OS 修改相关的文件：

   ```bash
   git diff --name-only  # 查看有哪些改动
   git add os/arceos/... os/StarryOS/...
   # 不要 git add .gitignore AGENTS.md 等非 OS 文件
   ```

5. 提交：

   ```bash
   git commit -m "fix(component): 简短描述修复内容"
   ```

---

## 6. 快速参考：关键文件路径

| 关注点 | 路径 |
|---|---|
| AxWaker（异步 I/O 唤醒）| `os/arceos/modules/axtask/src/future/mod.rs` |
| 运行队列 / blocked_resched | `os/arceos/modules/axtask/src/run_queue.rs` |
| TTY / PTY ldisc | `os/StarryOS/kernel/src/pseudofs/dev/tty/terminal/ldisc.rs` |
| PTY master/slave 创建 | `os/StarryOS/kernel/src/pseudofs/dev/tty/pty.rs` |
| epoll 实现 | `os/StarryOS/kernel/src/file/epoll.rs` |
| epoll syscall | `os/StarryOS/kernel/src/syscall/io_mpx/epoll.rs` |
| poll_io（异步 I/O helper）| `os/arceos/modules/axtask/src/future/poll.rs` |
| ax-log（日志 / debugcon）| `os/arceos/modules/axlog/src/lib.rs` |
| TCP 连接轮询 | `os/arceos/modules/axnet-ng/src/tcp.rs` |
| 进程退出 / SIGCHLD | `os/StarryOS/kernel/src/task/ops.rs` |
| waitpid | `os/StarryOS/kernel/src/syscall/task/wait.rs` |
