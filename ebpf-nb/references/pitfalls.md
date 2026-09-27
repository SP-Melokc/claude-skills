# Pitfalls: error → root cause → fix

## Quick table

| Error / symptom | Root cause | Fix |
|---|---|---|
| `invalid bpf_context access off=4 size=4` | tracepoint ctx: `off < sizeof(void*)` forbidden | PID via `bpf_get_current_pid_tgid()>>32`; only access offset >= 8 |
| `ld: error adding symbols: file in wrong format` | cross-compile set `CC` but not `LD` | use `CROSS_COMPILE=aarch64-linux-gnu-` |
| `bpf/bpf_helpers.h file not found` | include path wrong | `-I tools/lib` (parent of `bpf/`), not `-I tools/lib/bpf` |
| `btf_vmlinux is malformed` | kernel has no BTF; libbpf still probes it | **harmless warning**, ignore (unless you need CO-RE/fentry) |
| `libelf-dev:arm64 无法定位` | jammy arm64 is on ports, not archive | add `ports.ubuntu.com/ubuntu-ports` source |
| `libc6-dev:arm64 依赖 linux-libc-dev:arm64` | multiarch -dev package version conflict | `apt download` + `dpkg-deb -x` to extract `.a` only |
| `archive.ubuntu.com ... 404` (random pkgs) | DNS hijacked to partial CDN | switch to clean mirror (aliyun) |
| `BPF program load failed: -EACCES` | verifier rejected (read the log), OR unprivileged BPF disabled | fix the verifier error; or `sysctl kernel.unprivileged_bpf_disabled` |
| `-EPERM` on `bpf()` | no `CAP_BPF`/`CAP_SYS_ADMIN` | run as root / grant caps |

## Deep dive 1: tracepoint context access

`kernel/trace/bpf_trace.c` → `tp_prog_is_valid_access()`:

```c
if (off < sizeof(void *) || off >= PERF_MAX_TRACE_SIZE)   // off >= 8 on arm64
	return false;
if (type != BPF_READ)                                     // read-only
	return false;
if (off % size != 0)                                      // natural alignment
	return false;
```

Consequence: the `struct trace_entry` header (offsets 0–7: `type/flags/preempt_count/pid`) is **unreadable**. To get the PID, use the `bpf_get_current_pid_tgid()` helper (reads `current`, not the ctx). Data fields (`id` @8, `args[0]` @16 …) are fine.

The verifier log tells you exactly which instruction and offset failed — read the `-- BEGIN PROG LOAD LOG --` block.

## Deep dive 2: cross-compile tools

`make CC=aarch64-linux-gnu-gcc` in the kernel's `tools/` build only overrides `CC`. The linker invoked for the intermediate `-in.o` / `.so` steps is still the host `ld`, which can't link aarch64 objects. `CROSS_COMPILE=aarch64-linux-gnu-` makes the build use `aarch64-linux-gnu-{gcc,ld,ar,objcopy}` consistently.

## Deep dive 3: BTF vs no-BTF

- **With BTF** (`CONFIG_DEBUG_INFO_BTF=y` + `pahole`): use `#include "vmlinux.h"` for CO-RE (compile once, run on any kernel). Enables fentry/fexit, `bpftool btf dump`.
- **Without BTF**: hand-write the tracepoint/kprobe context struct. Fine for a fixed kernel you control (like a QEMU demo); no CO-RE, no fentry.

The `btf_vmlinux is malformed` line appears whenever libbpf tries to load kernel BTF and finds none — it's not the cause of a load failure; the real error is elsewhere in the log.

## Deep dive 4: `-EACCES` has two meanings

1. Verifier rejected the program → the log has `-- BEGIN PROG LOAD LOG --` with the specific reason. Fix the program.
2. Verifier passed but the load was denied for policy reasons → check `CONFIG_BPF_UNPRIV_DEFAULT_OFF` / `sysctl kernel.unprivileged_bpf_disabled`. If running as a non-root user, you need root or `CAP_BPF`.
