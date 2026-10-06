# Claude Skills

My [Claude Code](https://claude.ai/code) skills collection.

## Skills

### Kernel

- **annotate-struct** — Analyze and annotate C struct members with comments. Outputs annotated struct to terminal with key members emphasized. Triggered when asked to analyze/organize/explain struct definitions, especially Linux kernel structs.
- **crash-assistant** — Use `crash` to traverse and analyze Linux kernel data structures (linked lists, klist, kobject, driver core). Covers the `container_of` reverse-offset methodology, struct offset calculation for arm64, and crash commands (`list`/`tree`/`foreach`/`struct`).
- **kernel-doc-writer** — Write comprehensive Linux kernel technical documentation in my personal style. Use when asked to explain a kernel subsystem, create a driver analysis, document a framework, or produce a subsystem deep-dive.
- **ebpf-nb** — Develop, debug, and explain eBPF programs. Covers program types (tracepoint/kprobe/socket filter/XDP/fentry) and the kernel config each requires, the write → clang → libbpf → load → attach workflow, cross-compilation (aarch64), and common verifier errors.
- **function-trace-diagram** — Draw ANSI-colored ASCII function call-trace diagrams, using blue/yellow/purple for the entry/backbone/leaf layers. Emits both a simple and a detailed version each time. *Terminal ANSI version.*
- **function-trace-png** — Trace a function's call chain (esp. Linux kernel), annotate every check/decision with *why* it exists, and render the annotated call graph to a **PNG** image. Builds on `function-trace-diagram`'s coloring/method; outputs an overview plus one detailed diagram per branch. *Image version.*

### Embedded

- **rk-build** — Build and package the ATK-DLRK3568 Linux 6.1 SDK (RK3568). Covers board-configuration selection, full/partial builds, long builds detached from the SSH session, host disk-space monitoring, buildroot trimming, and 4 bumps already hit (menuconfig overwritten, leftovers not landing in target, missing gettext, recovery needing a second build pass).

### Tooling

- **statusline-setup** — Compact two-row statusline for Claude Code showing AI runtime state (model, context%, tokens, cache, thinking mode) and workspace context (CWD, git branch, PR status). Includes full install guide and troubleshooting.
