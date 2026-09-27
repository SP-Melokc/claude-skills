# Build Recipe: clang BPF + libbpf cross-compile

Assumes target is aarch64 (QEMU guest / embedded board), host is x86_64 Ubuntu.

## 1. Compile BPF program → bytecode (arch-independent)

```bash
K=<kernel source tree>

clang -target bpf -g -O2 -D__TARGET_ARCH_arm64 \
  -I$K/tools/lib \
  -I$K/tools/include/uapi \
  -I$K/include/uapi \
  -I$K/arch/arm64/include/uapi \
  -I$K/arch/arm64/include \
  -I$K/tools/include \
  -c prog.bpf.c -o prog.bpf.o
```

Key points:
- `-target bpf` is architecture-independent — host clang works fine, no cross-clang needed.
- **`-I $K/tools/lib` (NOT `$K/tools/lib/bpf`)** — so `#include <bpf/bpf_helpers.h>` resolves to `tools/lib/bpf/bpf_helpers.h`.
- `-D__TARGET_ARCH_arm64` matters only if you use arch-sensitive helpers (endian, `bpf_probe_read` wrappers in `bpf_tracing.h`); harmless otherwise.

## 2. Build libbpf for the target arch

```bash
cd $K/tools/lib/bpf
make CROSS_COMPILE=aarch64-linux-gnu- -j$(nproc)   # → libbpf.a
```

> [!warning] Must use `CROSS_COMPILE`, not `CC`
> `make CC=aarch64-linux-gnu-gcc` changes only the compiler; `ld` stays x86_64 → `ld: error adding symbols: file in wrong format`. `CROSS_COMPILE=aarch64-linux-gnu-` swaps CC/LD/AR together. The default `all` target builds both `.a` and `.so`; the `.so` step fails if aarch64 libelf is missing — that's fine, you only need `libbpf.a`.

libbpf needs `libelf.h` (arch-independent header) at *compile* time → `apt install libelf-dev` (amd64 is enough for the header).

## 3. Cross-compile the loader (static)

```bash
aarch64-linux-gnu-gcc -static -O2 \
  -I$K/tools/lib -I$K/tools/include/uapi -I$K/include/uapi \
  -I$K/arch/arm64/include/uapi -I$K/arch/arm64/include -I$K/tools/include \
  -o loader loader.c \
  $K/tools/lib/bpf/libbpf.a \
  /path/to/aarch64/libelf.a \
  /path/to/aarch64/libz.a \
  -lpthread
```

Static linking makes the binary self-contained (runs in a busybox/musl rootfs with no glibc `.so` deps). Needs aarch64 `libelf.a` + `libz.a`.

## 4. Get aarch64 libelf.a / libz.a WITHOUT multiarch pain

`apt install libelf-dev:arm64` drags in `libc6-dev:arm64 → linux-libc-dev:arm64`, which version-conflicts with the host amd64. Bypass it:

```bash
apt download libelf-dev:arm64 zlib1g-dev:arm64    # download only, no dep resolution
dpkg-deb -x libelf-dev_*_arm64.deb /tmp/arm64x
dpkg-deb -x zlib1g-dev_*_arm64.deb /tmp/arm64x
# → /tmp/arm64x/usr/lib/aarch64-linux-gnu/libelf.a  and  libz.a
```

## 5. apt source fix (jammy arm64 lives on ports)

`archive.ubuntu.com` only carries amd64/i386 for jammy; arm64 is on `ports.ubuntu.com`. Add:

```
deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports jammy main restricted universe multiverse
deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports jammy-updates main restricted universe multiverse
deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports jammy-security main restricted universe multiverse
```

If `archive.ubuntu.com` returns 404 for random amd64 packages (e.g. libxml2), it's DNS hijacked to a partial CDN — switch amd64 sources to a clean mirror (e.g. aliyun).

## 6. Run in QEMU (aarch64 guest)

Repack the rootfs cpio with the loader + `.bpf.o` + an `rdinit` script, then:

```bash
qemu-system-aarch64 -M virt -cpu cortex-a53 -smp 4 -m 1G \
  -kernel $K/arch/arm64/boot/Image -initrd rootfs.cpio \
  -append "console=ttyAMA0 root=/dev/ram rdinit=/demo.sh loglevel=4" \
  -display none -serial file:/tmp/serial.log -monitor none -no-reboot
```

Mount tracefs in the guest before running (libbpf reads the tracepoint `id` from there):

```sh
mkdir -p /sys/kernel/tracing && mount -t tracefs tracefs /sys/kernel/tracing
```
