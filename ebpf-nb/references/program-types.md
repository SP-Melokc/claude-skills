# Program Types & Required Kernel Config

## The core distinction

`CONFIG_BPF=y` only enables the eBPF *VM* (verifier + maps + JIT). Each *hook* is gated by its own config. Always grep the target kernel's `.config` first:

```bash
grep -E "CONFIG_BPF|CONFIG_KPROBES|CONFIG_FTRACE|CONFIG_TRACING|CONFIG_TRACEPOINTS|CONFIG_BPF_EVENTS|CONFIG_DEBUG_INFO_BTF|CONFIG_FUNCTION_TRACER|CONFIG_NET|CONFIG_PACKET" .config
```

## Hook types

| Program type | `SEC(...)` | Config needed | Context passed to BPF | Best for |
|---|---|---|---|---|
| **tracepoint** | `tracepoint/syscalls/sys_enter_execve` | `FTRACE` (+`FTRACE_SYSCALLS` for syscalls), `BPF_EVENTS` | `struct trace_event_raw_*` | syscall/static-point tracing |
| **raw tracepoint** | `raw_tracepoint/sched_process_exec` | `FTRACE`, `BPF_EVENTS` | `struct bpf_raw_tracepoint_args { __u64 args[0]; }` | stable, low-overhead tracing |
| **kprobe** | `kprobe/do_sys_open` | `KPROBES`, `BPF_EVENTS` | `struct pt_regs *` | arbitrary function entry |
| **kretprobe** | `kretprobe/do_sys_open` | `KPROBES`, `BPF_EVENTS` | `struct pt_regs *` | function return value |
| **fentry/fexit** | `fentry/<func>` | `BPF_JIT` + `FUNCTION_TRACER` + **BTF** | typed function args | cheapest, typed hooking |
| **socket filter** | (none, `SO_ATTACH_BPF`) | `NET`, `PACKET` | `struct __sk_buff *` | packet filtering (no perf needed) |
| **XDP** | `xdp` | driver XDP support | `struct xdp_md *` | high-speed packet processing |
| **cgroup skb** | `cgroup_skb/ingress` | `CGROUP_BPF` | `struct __sk_buff *` | per-cgroup traffic control |

## Decision rules

- **"Trace every syscall"** → tracepoint `syscalls/sys_enter_*` (or raw `raw_syscalls/sys_enter`).
- **"Hook this specific function"** → kprobe (no BTF needed) or fentry (needs BTF, but typed args + lower overhead).
- **"Watch what the system runs"** → tracepoint `sys_enter_execve` or `sched_process_exec`.
- **"Filter/drop packets"** → socket filter (simplest) or XDP (fastest).

## How to discover what's available

```bash
# 1) kernel config (source of truth for compile-time options)
grep -E "CONFIG_(KPROBES|FTRACE|BPF_EVENTS|DEBUG_INFO_BTF)" .config

# 2) available tracepoints on a running system
ls /sys/kernel/tracing/events/syscalls/          # syscall tracepoints
ls /sys/kernel/tracing/events/sched/             # scheduler tracepoints
cat /sys/kernel/tracing/events/syscalls/sys_enter_execve/id   # tracepoint id
cat /sys/kernel/tracing/events/syscalls/sys_enter_execve/format  # ★ exact field layout

# 3) BTF presence (CO-RE possible?)
ls /sys/kernel/btf/vmlinux   # exists → BTF available
```

## Tracepoint context struct (hand-written, no BTF)

For `tracepoint/syscalls/sys_enter_*`, the context is `trace_event_raw_sys_enter` (from `include/trace/events/syscalls.h`):

```c
struct trace_event_raw_sys_enter {
	unsigned short common_type;      // offset 0
	unsigned char  common_flags;     // offset 2
	unsigned char  common_preempt_count; // offset 3
	int            common_pid;       // offset 4  ← ⚠️ off-limits, see pitfalls
	long           id;               // offset 8
	unsigned long  args[6];          // offset 16  ← syscall args
};
```

> [!warning]
> The first 8 bytes (`struct trace_entry`) are **not readable** from a tracepoint BPF program (verifier rule `off >= sizeof(void *)`). Use helpers (`bpf_get_current_pid_tgid()`) instead of `ctx->common_pid`. `args[0..5]` at offset 16+ are readable.
