# crash-assistant

A Claude Code skill for traversing and analyzing Linux kernel data structures with the `crash` utility. Designed for BSP/stability engineers who analyze vmcore dumps.

## What it does

- Teaches the **container_of reverse-offset** methodology — how to go from a linked-list node address back to the enclosing struct
- Provides **arm64 struct offset** baselines and the config flags that break them (`CONFIG_LOCKDEP`, `CONFIG_RANDSTRUCT`)
- Documents **crash commands** (`list` in depth, `tree`/`foreach`/`struct` as extension points)
- Ships the **driver core 3-layer traversal** (bus → driver → device) as the worked example, with full offsets and command sequences
- Records the **six pitfalls** that actually bite in practice

## Core idea

Kernel linked lists embed the link node *inside* the struct. To walk them in crash you must reverse-engineer the struct base from each node:

```
struct_base = member_address - member_offset
```

The skill turns this one formula into a repeatable workflow and gives you the ready-made offsets for the driver core.

## Files

```
crash-assistant/
├── SKILL.md                        # methodology + workflow + entry points
├── README.md                       # this file
└── references/
    ├── list-command.md             # full crash list command reference
    ├── driver-core.md              # bus/driver/device offsets + command sequence
    └── pitfalls.md                 # six pitfalls, root cause & fix
```

## Usage

Just ask Claude in natural language:

```
用 crash 遍历所有 driver
crash 看 platform 总线下的 device
how do I walk klist_drivers in crash
```

The skill triggers automatically and applies the container_of + offset + crash-command workflow.

## Installation

```bash
git clone https://github.com/SP-Melokc/claude-skills /c/Users/<you>/.claude/skills/
```

Or copy the `crash-assistant/` directory into `~/.claude/skills/`.

## Dependencies

- `crash` utility + a kernel `vmlinux` with DWARF debug info (`CONFIG_DEBUG_INFO`)
- Linux kernel source tree for verifying struct definitions (optional but recommended)
- No external tools or packages

## License

MIT — adapt freely for your own kernel data structures and crash workflows.
