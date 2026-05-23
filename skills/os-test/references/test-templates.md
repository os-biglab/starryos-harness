# 测试代码模板

## C 测试模板 (StarryOS syscall)

```c
/*
 * 测试: <syscall_name> 基本功能
 * 编译: musl-riscv64-gcc -static -o test_<name> test_<name>.c
 * 期望: [TEST] test_<name> PASS
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <sys/syscall.h>

/* 辅助宏 */
#define TEST_BEGIN(name) printf("[TEST] %s\n", name)
#define TEST_PASS(name)  printf("[TEST] %s PASS\n", name)
#define TEST_FAIL(name, fmt, ...) \
    printf("[TEST] %s FAIL: " fmt "\n", name, ##__VA_ARGS__)

int main() {
    /* 测试 1: 正常路径 */
    TEST_BEGIN("test_<syscall>_normal");
    long ret = syscall(SYS_<syscall>, /* args */);
    if (ret >= 0) {
        TEST_PASS("test_<syscall>_normal");
    } else {
        TEST_FAIL("test_<syscall>_normal", "ret=%ld errno=%d", ret, errno);
    }

    /* 测试 2: NULL 指针 */
    TEST_BEGIN("test_<syscall>_null_ptr");
    ret = syscall(SYS_<syscall>, NULL /* args */);
    if (ret == -1 && errno == EFAULT) {
        TEST_PASS("test_<syscall>_null_ptr");
    } else {
        TEST_FAIL("test_<syscall>_null_ptr", "ret=%ld errno=%d expected EFAULT", ret, errno);
    }

    /* 测试 3: 无效 fd */
    TEST_BEGIN("test_<syscall>_bad_fd");
    ret = syscall(SYS_<syscall>, -1 /* args */);
    if (ret == -1 && errno == EBADF) {
        TEST_PASS("test_<syscall>_bad_fd");
    } else {
        TEST_FAIL("test_<syscall>_bad_fd", "ret=%ld errno=%d expected EBADF", ret, errno);
    }

    return 0;
}
```

## ArceOS Rust 测试模板

```rust
// test-suit/arceos/rust/<test_name>/src/main.rs
#![no_std]
#![no_main]

extern crate alloc;

use axstd::println;

fn test_alloc_basic() -> bool {
    println!("[TEST] test_alloc_basic");
    let v = alloc::vec![42u8; 1024];
    if v.len() == 1024 && v[0] == 42 {
        println!("[TEST] test_alloc_basic PASS");
        true
    } else {
        println!("[TEST] test_alloc_basic FAIL");
        false
    }
}

fn test_alloc_large() -> bool {
    println!("[TEST] test_alloc_large");
    let v = alloc::vec![0u8; 1024 * 1024]; // 1MB
    if v.len() == 1024 * 1024 {
        println!("[TEST] test_alloc_large PASS");
        true
    } else {
        println!("[TEST] test_alloc_large FAIL");
        false
    }
}

#[no_mangle]
fn main() -> i32 {
    let mut pass = true;
    pass &= test_alloc_basic();
    pass &= test_alloc_large();
    if pass { 0 } else { 1 }
}
```

对应的 `Cargo.toml`:
```toml
[package]
name = "test-alloc-basic"
version = "0.1.0"
edition = "2021"

[dependencies]
axstd = { path = "../../../../os/arceos/ulib/std", features = ["alloc"] }
```

对应的 QEMU 配置 (`qemu-riscv64.toml`):
```toml
[qemu]
args = "-machine virt -cpu rv64"

[build]
packages = ["test-alloc-basic"]

[test]
success_regex = "\\[TEST\\].*PASS"
fail_regex = "\\[TEST\\].*FAIL"
timeout = 30
```

## 并发测试模板

```c
/*
 * 并发测试: 检测 SMP 相关的 data race
 * 编译: musl-riscv64-gcc -static -lpthread -o test_concurrent test_concurrent.c
 */
#include <stdio.h>
#include <pthread.h>
#include <stdatomic.h>

#define NUM_THREADS 4
#define NUM_ITERS 10000

atomic_int counter = 0;

void *increment(void *arg) {
    (void)arg;
    for (int i = 0; i < NUM_ITERS; i++) {
        atomic_fetch_add(&counter, 1);
    }
    return NULL;
}

int main() {
    printf("[TEST] test_concurrent_atomic\n");

    pthread_t threads[NUM_THREADS];
    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_create(&threads[i], NULL, increment, NULL);
    }
    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }

    int expected = NUM_THREADS * NUM_ITERS;
    if (atomic_load(&counter) == expected) {
        printf("[TEST] test_concurrent_atomic PASS\n");
    } else {
        printf("[TEST] test_concurrent_atomic FAIL: got %d expected %d\n",
               atomic_load(&counter), expected);
    }
    return 0;
}
```

## Shell 测试模板

```bash
#!/bin/sh
# test-suit/starryos/normal/test_file_ops/run.sh

echo "[TEST] test_file_create"
echo "hello" > /tmp/test_file
if [ -f /tmp/test_file ]; then
    echo "[TEST] test_file_create PASS"
else
    echo "[TEST] test_file_create FAIL"
fi

echo "[TEST] test_file_read"
content=$(cat /tmp/test_file)
if [ "$content" = "hello" ]; then
    echo "[TEST] test_file_read PASS"
else
    echo "[TEST] test_file_read FAIL: got '$content'"
fi

rm -f /tmp/test_file
```
