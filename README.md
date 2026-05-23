# os-biglab — Claude Code Plugin for OS Development

A comprehensive Claude Code plugin for developing the TGOSKits OS framework (ArceOS / StarryOS / Axvisor).

## Plugin Structure

```
os-biglab-plugin/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest
├── skills/
│   ├── os-debug/                # Kernel debugging skill
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── panic-patterns.md    # Common panic messages & fixes
│   │       ├── errno-table.md       # Linux errno quick reference
│   │       └── gdb-workflow.md      # QEMU + GDB step-by-step
│   ├── os-feature/              # Feature implementation skill
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── syscall-guide.md     # StarryOS syscall patterns
│   │       ├── module-guide.md      # ArceOS module creation
│   │       └── driver-guide.md      # Device driver development
│   ├── os-review/               # Code review skill
│   │   ├── SKILL.md
│   │   └── references/
│   │       └── review-checklist.md  # Full OS review checklist
│   └── os-nav/                  # Codebase navigation skill
│       ├── SKILL.md
│       └── references/
│           └── module-map.md        # Module dependency graph
├── agents/
│   ├── kernel-debugger.md       # Read-only diagnostic agent
│   ├── os-architect.md          # Design + implement agent
│   └── code-reviewer.md         # Read-only review agent
├── hooks/
│   └── hooks.json               # Auto-fmt on Rust file write/edit
├── monitors/
│   └── monitors.json            # QEMU log watcher (on os-debug)
└── scripts/
    ├── auto-fmt.sh              # Hook: cargo fmt on edited crate
    ├── auto-clippy.sh           # Manual: targeted clippy check
    ├── parse-qemu-log.py        # Analyse QEMU/OS log for errors
    └── gen-syscall.py           # Generate syscall boilerplate
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

## Installation (local dev)

```bash
# Load plugin for this session
claude --plugin-dir /workspace/os-biglab-plugin

# Or install project-scoped (persists across sessions)
claude plugin install /workspace/os-biglab-plugin --scope project
```

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
