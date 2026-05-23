# QEMU + GDB Debug Workflow

## 1. Start QEMU in wait-for-GDB mode

```bash
# StarryOS riscv64
cargo xtask starry qemu -t riscv64 -- -s -S

# StarryOS aarch64
cargo xtask starry qemu -t aarch64 -- -s -S

# ArceOS riscv64
cargo xtask arceos qemu -t riscv64 -a <app> -- -s -S
```

`-s` opens a GDB server on TCP port 1234.  
`-S` freezes the CPU at startup so GDB can set breakpoints before anything runs.

## 2. Connect GDB in another terminal

### riscv64
```bash
riscv64-unknown-elf-gdb \
  target/riscv64gc-unknown-none-elf/release/starry \
  -ex "target remote :1234" \
  -ex "set disassemble-next-line auto"
```

### aarch64
```bash
aarch64-unknown-elf-gdb \
  target/aarch64-unknown-none/release/starry \
  -ex "target remote :1234"
```

### x86_64
```bash
gdb \
  target/x86_64-unknown-none/release/starry \
  -ex "target remote :1234"
```

## 3. Common GDB commands

| Command | Description |
|---------|-------------|
| `c` / `continue` | Resume execution |
| `bt` / `backtrace` | Print call stack |
| `b <function>` | Set breakpoint at function |
| `b <file>:<line>` | Set breakpoint at source line |
| `b *0xADDR` | Set breakpoint at raw address |
| `d <num>` | Delete breakpoint by number |
| `info break` | List all breakpoints |
| `si` / `stepi` | Single-step one machine instruction |
| `ni` / `nexti` | Next instruction (step over calls) |
| `p <expr>` | Print value of expression |
| `p/x <expr>` | Print as hex |
| `x/10i $pc` | Disassemble 10 instructions at PC |
| `x/4gx $sp` | Print 4 quadwords at stack pointer |
| `info reg` | Show all registers |
| `info threads` | Show all CPU threads (harts) |
| `thread N` | Switch to thread/hart N |
| `thread apply all bt` | Backtrace all harts (deadlock analysis) |
| `watch *0xADDR` | Break on memory write |
| `rwatch *0xADDR` | Break on memory read |
| `awatch *0xADDR` | Break on read or write |
| `set scheduler-locking off` | Allow all harts to run (default) |
| `set scheduler-locking on` | Only current hart runs |

## 4. Useful breakpoints for OS debugging

```gdb
# Catch all panics
b rust_begin_unwind

# Catch page fault handler (riscv64 StarryOS)
b handle_page_fault

# Catch syscall entry
b handle_syscall

# Catch specific syscall by number (if dispatch is a match)
# Set bp at dispatch, then condition on syscall number register (a7 on riscv)
b syscall_dispatch
condition 1 $a7 == 9   # e.g., syscall 9 = mmap
```

## 5. Finding a kernel symbol address

```bash
# From host, before launching QEMU
nm target/riscv64gc-unknown-none-elf/release/starry | grep <symbol>
# or
riscv64-unknown-elf-objdump -t target/.../starry | grep <symbol>
```

## 6. Crash dump analysis without GDB

If you have a raw register dump in the log:
1. Note `sepc` (riscv) / `elr` (aarch64) / `rip` (x86) — that's the crash PC
2. Map to symbol:
   ```bash
   addr2line -e target/riscv64gc-unknown-none-elf/release/starry -f 0x<PC>
   ```
3. Or use objdump:
   ```bash
   riscv64-unknown-elf-objdump -d target/.../starry | grep -B5 '<PC without leading 0x>'
   ```

## 7. QEMU monitor commands

```bash
# Start QEMU with monitor on stdio
cargo xtask starry qemu -t riscv64 -- -monitor stdio

# In the QEMU monitor:
(qemu) info cpus          # show all vCPUs and their PC
(qemu) info registers     # dump registers of current vCPU
(qemu) info mem           # show memory map
(qemu) stop               # pause all vCPUs
(qemu) cont               # resume
(qemu) x/10 0xADDR        # examine memory
```
