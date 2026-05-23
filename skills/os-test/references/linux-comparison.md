# Docker Linux 对照测试

## 原则

**Linux 定义正确性**: 每个 syscall 测试必须先在 Linux 上通过。
如果测试在 Linux 上失败，说明测试本身有 bug。

## 环境准备

### Docker 镜像

```bash
docker pull ghcr.io/rcore-os/tgoskits-container:latest
```

包含: Ubuntu 24.04, Rust nightly, QEMU 10.2.1, musl 交叉编译器。

### 编译测试程序

```bash
# x86_64 静态编译 (Docker Linux 内运行)
docker run --rm -v $(pwd):/work -w /work \
  ghcr.io/rcore-os/tgoskits-container:latest \
  gcc -static -o test_binary test.c

# riscv64 静态编译 (qemu-user 运行)
docker run --rm -v $(pwd):/work -w /work \
  ghcr.io/rcore-os/tgoskits-container:latest \
  riscv64-linux-gnu-gcc -static -o test_binary test.c
```

## 运行 Linux 参考测试

### 方式 A: Docker 直接运行 (x86_64)

```bash
docker run --rm -v $(pwd):/work -w /work \
  ghcr.io/rcore-os/tgoskits-container:latest \
  ./test_binary
```

### 方式 B: qemu-user 运行 (跨架构)

```bash
# riscv64
qemu-riscv64-static ./test_binary

# aarch64
qemu-aarch64-static ./test_binary
```

### 方式 C: qemu-system 完整启动

```bash
# 构建最小 Linux rootfs
docker run --rm -v $(pwd):/work -w /work \
  ghcr.io/rcore-os/tgoskits-container:latest \
  bash -c "
    mkdir -p rootfs/bin rootfs/lib
    cp test_binary rootfs/bin/
    cd rootfs && find . | cpio -o -H newc | gzip > ../rootfs.cpio
  "

# QEMU 启动
qemu-system-riscv64 \
  -machine virt \
  -kernel Image \
  -initrd rootfs.cpio \
  -append "console=ttyS0 init=/bin/test_binary" \
  -nographic
```

## 记录参考输出

每次 Linux 测试后，记录:
```
测试: test_getxattr_normal
Linux 输出:
  [TEST] test_getxattr_normal PASS
  返回值: 10
  errno: 0
```

这个记录是 StarryOS 对比的基准。

## 对比方法

| 维度 | 检查点 |
|------|--------|
| 返回值 | syscall 返回值是否一致 |
| errno | 错误时 errno 是否一致 |
| 输出 | stdout/stderr 输出是否一致 |
| 副作用 | 文件内容、信号、进程状态是否一致 |
| 边界 | NULL 指针、0 长度、溢出值的处理是否一致 |

## 常见差异

| 差异类型 | 说明 | 处理方式 |
|---------|------|---------|
| ENOSYS | syscall 未实现 | 需要实现 |
| errno 不同 | 错误码映射不一致 | 需要修复 |
| 返回值不同 | 语义理解不一致 | 需要对齐 Linux |
| 输出格式不同 | printf 格式差异 | 通常可接受 |
