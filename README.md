# os-biglab — Claude Code Plugin for OS Development

A comprehensive Claude Code plugin for developing the TGOSKits OS framework (ArceOS / StarryOS / Axvisor).

## Plugin Structure

```
os-biglab-plugin/
├── .claude-plugin/plugin.json   # Plugin manifest
├── skills/                      # 9 skills
│   ├── os-benchmark/            # Performance benchmarking
│   ├── os-debug/                # Kernel debugging
│   ├── os-evolve/               # Self-evolving orchestrator
│   ├── os-feature/              # Feature implementation
│   ├── os-learn/                # OS learning document generator
│   ├── os-nav/                  # Codebase navigation
│   ├── os-pr-workflow/          # PR preparation workflow
│   ├── os-review/               # Code review (with anti-hallucination)
│   ├── os-test/                 # Systematic testing
│   ├── os-upstream-sync/        # Upstream sync (rebase/conflict/squash)
│   └── starryos-debug/          # StarryOS-specific debug
├── agents/                      # 5 agents
│   ├── bug-hunter.md            # Bug discovery and classification
│   ├── code-reviewer.md         # Read-only review agent
│   ├── kernel-debugger.md       # Read-only diagnostic agent
│   ├── os-architect.md          # Design + implement agent
│   └── test-generator.md        # Test case generator
├── hooks/hooks.json             # SessionStart + PostToolUse + PreToolUse + Stop
├── monitors/monitors.json       # QEMU log watcher
├── scripts/                     # 8 scripts
│   ├── abi-check.py             # Syscall ABI checker
│   ├── activity-logger.py       # Edit/Write activity logger
│   ├── auto-clippy.sh           # Targeted clippy check
│   ├── auto-fmt.sh              # Auto cargo fmt on edit
│   ├── gen-syscall.py           # Syscall boilerplate generator
│   ├── lock-order-graph.py      # Lock order analysis + deadlock detection
│   ├── parse-qemu-log.py        # QEMU log parser
│   ├── pattern-scanner.py       # Pattern-based code scanner
│   ├── pre-pr-gate.sh           # Clippy zero-warning gate for push
│   └── session-stop.py          # Session summary generator
└── docs/
    ├── IMPROVEMENT-PLAN.md      # Improvement plan and roadmap
    ├── SCENARIOS.md             # Scenario-based usage guide
    ├── USAGE-GUIDE.md           # Detailed usage instructions
    └── os-biglab-patterns/
        └── patterns.json        # Evolvable detection rules
```

---

## Skills

### `/os-biglab:os-debug`

Structured debugging workflow for kernel panics, page faults, syscall errors, deadlocks, and build failures.

**Trigger phrases:** debug, panic, crash, page fault, kernel fault, hang, deadlock, QEMU not responding, backtrace, exception

**Features:**
- Classifies the failure type from error output
- Step-by-step diagnosis for each failure category
- GDB connection workflow for interactive debugging
- Integrates `parse-qemu-log.py` to analyse captured logs

### `/os-biglab:os-feature`

Guided implementation of new OS features with architecture-specific patterns.

**Trigger phrases:** add syscall, implement syscall, new module, new driver, add feature, implement, port, missing syscall

**Features:**
- New StarryOS syscall: dispatch entry + implementation + user-pointer safety
- New ArceOS module: Cargo.toml template + crate_interface setup
- New device driver: BlockDriverOps / NetDriverOps implementation
- VFS and MM extension patterns
- Generates syscall boilerplate via `gen-syscall.py`

### `/os-biglab:os-review`

Eight-dimensional code review checklist for kernel code.

**Trigger phrases:** review, audit, check safety, code review, PR review, unsafe review, is this correct

**Dimensions:** unsafe code, concurrency/locking, memory management, error handling, performance, platform compatibility, API correctness, test coverage

### `/os-biglab:os-nav`

Navigate and understand the TGOSKits codebase.

**Trigger phrases:** where is, find, how does, understand, explain, which crate, navigate, trace, what handles

**Features:**
- Directory map with purpose annotations
- Find-by-feature quick reference table
- `crate_interface` mechanism explanation
- Execution flow tracing (boot sequence, syscall dispatch)
- LSP-assisted navigation guidance

---

## Agents

### `kernel-debugger`

Read-only diagnostic agent. Uses `os-debug` + `os-nav` skills. Cannot modify files. Returns structured diagnosis: root cause, suggested fix, files to modify.

Best for: deep bug investigation without risk of accidental code changes.

### `os-architect`

Design + implementation agent. Uses `os-feature` + `os-nav` skills. Can read and write code. Enforces project conventions, runs fmt/clippy after changes.

Best for: implementing a new syscall or module end-to-end.

### `code-reviewer`

Read-only review agent. Uses `os-review` + `os-nav` skills. Returns a structured report with Critical / Warning / NIT findings.

Best for: pre-merge audits and PR reviews.

---

## Hooks

| Event | Trigger | Action |
|-------|---------|--------|
| `PostToolUse` | Write or Edit a `.rs` file | Runs `cargo fmt` on the crate automatically |
| `SessionStart` | Session begins | Makes scripts executable; prints ready message |

The auto-fmt hook finds the nearest `Cargo.toml`, extracts the crate name, and runs `cargo fmt --package <crate>`. Runs silently; only prints crate name on success.

---

## Monitors

| Monitor | Activated | What it watches |
|---------|-----------|----------------|
| `qemu-log-watcher` | When `os-debug` skill is invoked | Tails `/tmp/os_run.log` for panics, faults, errors |

To use the monitor, first start QEMU redirecting output to the log file:
```bash
cargo xtask starry qemu -t riscv64 2>&1 | tee /tmp/os_run.log
```

---

## Scripts

### `parse-qemu-log.py`

Analyse a QEMU / kernel log file and produce a structured error report.

```bash
# From a file
python3 os-biglab-plugin/scripts/parse-qemu-log.py /tmp/os_run.log

# From a pipe
cargo xtask starry qemu -t riscv64 2>&1 | python3 os-biglab-plugin/scripts/parse-qemu-log.py

# Exit code: 0 = no errors found, 1 = errors found
```

Detects: panics, page faults, instruction faults, exceptions, OOM, deadlocks, kernel BUGs.
Extracts: PC/sepc address and suggests `addr2line` command.

### `gen-syscall.py`

Generate StarryOS syscall boilerplate: dispatch entry + implementation skeleton.

```bash
python3 os-biglab-plugin/scripts/gen-syscall.py \
  --name getxattr \
  --nr 8 \
  --args "path:*const u8,name:*const u8,value:*mut u8,size:usize" \
  --category fs
```

Outputs ready-to-paste code for `mod.rs` (dispatch) and the category file (implementation), with correct `UserInPtr`/`UserOutPtr` wrappers for pointer arguments.

### `auto-clippy.sh`

Run targeted clippy on a specific crate:

```bash
# By crate name
./os-biglab-plugin/scripts/auto-clippy.sh starry-kernel

# Or just: (uses xtask)
cargo xtask clippy --package starry-kernel
```

---

## Installation

```bash
# Load plugin for this session
claude --plugin-dir /path/to/os-biglab-plugin

# Or install project-scoped (persists across sessions)
claude plugin install /path/to/os-biglab-plugin --scope project
```

---

## Documentation

- [docs/SCENARIOS.md](docs/SCENARIOS.md) -- **场景化使用指南** (bug 调试、OS 学习、upstream 同步、PR 提交)
- [docs/COMPARISON-REPORT.md](docs/COMPARISON-REPORT.md) -- **对比分析报告** (与参考项目的增量改进和优势)
- [docs/USAGE-GUIDE.md](docs/USAGE-GUIDE.md) -- 详细功能说明
- [docs/IMPROVEMENT-PLAN.md](docs/IMPROVEMENT-PLAN.md) -- 完善方案和路线图

## Roadmap

**全部实现完成:**
- 10 个 Skills (os-debug, os-feature, os-learn, os-nav, os-pr-workflow, os-review, os-test, os-upstream-sync, os-benchmark, os-evolve, starryos-debug)
- 5 个 Agents (kernel-debugger, os-architect, code-reviewer, bug-hunter, test-generator)
- 10 个 Scripts (auto-fmt, auto-clippy, pre-pr-gate, parse-qemu-log, gen-syscall, abi-check, lock-order-graph, pattern-scanner, activity-logger, session-stop)
- 4 个 Hooks (SessionStart, PostToolUse, PreToolUse, Stop)
- 反幻觉协议 (7 级验证体系)
- 场景化使用指南 (6 个核心场景)

---

## Development workflow example

```
You: "There's a kernel panic when running the mmap test"

Claude (auto-invokes os-debug):
  1. Asks you to run: cargo xtask starry qemu -t riscv64 2>&1 | tee /tmp/os_run.log
  2. Runs parse-qemu-log.py to extract the panic site
  3. Reads the source file at the panic line
  4. Traces back to root cause
  5. Suggests exact fix

You: "Add support for sys_getxattr syscall"

Claude (auto-invokes os-feature):
  1. Looks up syscall number and Linux semantics
  2. Runs gen-syscall.py to generate boilerplate
  3. Implements the function with UserInPtr for user pointers
  4. Adds dispatch entry in mod.rs
  5. Runs cargo fmt + clippy to verify
  6. Suggests adding a test case

You: "Review this PR before I merge"

Claude (auto-invokes os-review):
  1. Reads all modified files
  2. Applies 8-dimension checklist
  3. Returns structured report: Critical / Warning / NIT / Verdict
```
