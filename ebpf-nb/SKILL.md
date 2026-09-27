---
name: ebpf-nb
description: Develop, debug, and explain eBPF programs. Covers program types (tracepoint/kprobe/socket filter/XDP/fentry) and the kernel config each requires, the write → clang → libbpf → load → attach workflow, cross-compilation (especially aarch64), and common verifier errors and their fixes. Use when the user asks to write/run/debug an eBPF program, trace a syscall or kernel function, or hits a BPF verifier/load error. Trigger on: "eBPF", "BPF 程序", "tracepoint", "kprobe", "追踪 syscall", "写个 ebpf demo", "bpf verifier 报错", "invalid bpf_context access", "CO-RE", "BTF", "libbpf 交叉编译", "ringbuf", "bpf_printk".
---

# eBPF Assistant (ebpf-nb)

Guide for developing, debugging, and explaining eBPF programs. The user is "Master" — an ARM64 kernel engineer (BSP/stability) who is expanding from memory management into the broader kernel, now touching tracing/observability. Master often wants to *run* a demo in QEMU, not just read theory.

## When to use

- Master asks to write an eBPF program (trace a syscall, count events, filter packets).
- Master hits a BPF load/verifier error and needs the root cause.
- Master asks which hook (tracepoint vs kprobe vs socket filter) fits a goal.
- Master needs to cross-compile BPF + loader for aarch64 (QEMU guest, embedded board).

## Core model: program type → kernel config

The single most common confusion is **"CONFIG_BPF=y" ≠ "tracing works"**. eBPF core (VM/verifier/JIT) and the *hooks* are separate switches:

| Hook (program type) | `SEC("...")` | Required config | Context |
|---|---|---|---|
| tracepoint | `tracepoint/<cat>/<name>` | `FTRACE` (+`FTRACE_SYSCALLS` for syscalls), `BPF_EVENTS` | `trace_event_raw_*` struct |
| kprobe / kretprobe | `kprobe/<func>` / `kretprobe/<func>` | `KPROBES`, `BPF_EVENTS` | `struct pt_regs *` |
| raw tracepoint | `raw_tracepoint/<name>` | `FTRACE`, `BPF_EVENTS` | `struct bpf_raw_tracepoint_args` |
| fentry / fexit | `fentry/<func>` / `fexit/<func>` | `BPF_JIT` + `FUNCTION_TRACER` + **BTF** | function args |
| socket filter | (attach via `SO_ATTACH_BPF`) | `NET` + `PACKET` | `struct __sk_buff *` |
| XDP | `xdp` | driver XDP support | `struct xdp_md *` |
| cgroup skb | `cgroup_skb/...` | `CGROUP_BPF` | `struct __sk_buff *` |

**Decision rule:** syscall tracing → tracepoint (`sys_enter_*`); arbitrary function hooking → kprobe; hooking a function cheaply with typed args → fentry (needs BTF); packet filtering → socket filter/XDP. See [references/program-types.md](references/program-types.md) for details.

## Workflow (write → compile → load → run)

1. **Check the target kernel's config first** — grep `CONFIG_BPF`, `CONFIG_KPROBES`, `CONFIG_FTRACE`, `CONFIG_DEBUG_INFO_BTF`. This determines *everything* (which hooks work, whether CO-RE is possible).
2. **Write the BPF program** — a `.bpf.c` with `SEC("...")` + maps. Decide BTF vs no-BTF: if the kernel has BTF and you want CO-RE, `#include "vmlinux.h"`; otherwise hand-write the context struct.
3. **Compile to bytecode** with clang (target `bpf` is arch-independent):
   ```
   clang -target bpf -g -O2 -I <kernel>/tools/lib -I <kernel>/tools/include/uapi \
     -I <kernel>/include/uapi -I <kernel>/arch/<arch>/include/uapi ... -c prog.bpf.c -o prog.bpf.o
   ```
4. **Write the loader** with libbpf (`bpf_object__open_file` → `bpf_object__load` → `bpf_program__attach_*` → consume ringbuf/map).
5. **Cross-compile the loader** if the target arch differs. Use `CROSS_COMPILE`, not `CC` (see pitfalls).
6. **Run**: mount tracefs if using tracepoints, run loader, trigger events, read output.

## Pitfalls (the ones that actually bite)

Full table in [references/pitfalls.md](references/pitfalls.md). The top three:

1. **`invalid bpf_context access off=4 size=4`** — for tracepoint programs, `tp_prog_is_valid_access()` requires `off >= sizeof(void *)` (8 on arm64). The `struct trace_entry` header (first 8 bytes, incl. `pid`) is off-limits. Get PID via `bpf_get_current_pid_tgid() >> 32`, not `ctx->common_pid`.

2. **`ld: error adding symbols: file in wrong format`** — cross-compiling libbpf/loader with only `CC=aarch64-linux-gnu-gcc` leaves the linker as host x86_64. Use `make CROSS_COMPILE=aarch64-linux-gnu-`.

3. **`bpf/bpf_helpers.h file not found`** — the include path must be the *parent* of the `bpf/` dir: `-I <kernel>/tools/lib`, not `-I <kernel>/tools/lib/bpf`.

## Worked example

The canonical first demo — trace every `execve` and print pid/comm/filename via ringbuf — is documented end-to-end (code + build commands + QEMU boot) in [references/execve-demo.md](references/execve-demo.md).

## Reference files

| File | Content |
|------|---------|
| [references/program-types.md](references/program-types.md) | Hook types, SEC names, required config, context structs |
| [references/build-recipe.md](references/build-recipe.md) | clang BPF compile + libbpf cross-compile + aarch64 static lib extraction (apt source gotchas) |
| [references/pitfalls.md](references/pitfalls.md) | Error → root cause → fix table, with the deep dives |
| [references/execve-demo.md](references/execve-demo.md) | Full worked example: execve tracepoint + ringbuf, end to end |
