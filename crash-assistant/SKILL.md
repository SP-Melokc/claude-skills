---
name: crash-assistant
description: Use crash to traverse and analyze Linux kernel data structures (linked lists, klist, kobject, driver core). Covers the container_of reverse-offset methodology, struct offset calculation for arm64, and crash commands (list/tree/foreach/struct). Use when the user asks to walk a kernel list, find all drivers/devices, inspect a struct in a vmcore, debug with crash, or reverse-engineer a kernel data structure from an address. Trigger on: "用crash遍历", "crash看链表", "crash list", "crash查driver/device", "crash分析结构体", "crash看所有driver", "how to walk a list in crash".
---

# Crash Assistant

Guide for traversing and analyzing Linux kernel data structures with the `crash` utility. The user is "Master" — a BSP/stability engineer on ARM64 who analyzes vmcore dumps and needs to walk kernel-internal linked lists.

## Core Methodology

Three pillars, in order of importance:

### 1. container_of reverse-offset (the foundation)

Kernel linked lists embed the link node *inside* the structure, not a pointer to the next structure. To go from a node address back to the enclosing struct:

```
struct_base = member_address - member_offset
```

`container_of` (include/linux/container_of.h) is exactly this. Every "node - 0x70 = driver_private" is a container_of in disguise.

### 2. Struct offset calculation (arm64 ABI)

Offsets depend on the ABI and kernel config. Baseline for arm64 with `CONFIG_LOCKDEP=n`:

| type | size |
|------|------|
| pointer | 8 |
| `struct list_head` | 16 (next + prev) |
| `spinlock_t` / `raw_spinlock_t` | 4 |
| `struct mutex` | 0x20 |
| `struct kobject` | 0x40 |
| `struct kset` | 0x60 |
| `struct klist` | 0x28 |
| `struct klist_node` | 0x20 |

> [!warning]
> Offsets drift when `CONFIG_LOCKDEP=y` (lock_class_key becomes 16-byte hlist_node, mutex/spinlock grow via `dep_map`) or `CONFIG_RANDSTRUCT=y` (kset has `__randomize_layout`). **Always confirm with `crash> struct -o <struct>` before trusting any hand-calculated offset.**

### 3. crash commands (list is the first, not the only)

- `list` — traverse linked lists (singly- and list_head-linked)
- `tree` — traverse rbtree / radix / xarray
- `foreach` — run a command over a set (batch `struct`, batch `list`)
- `struct` — format one address as a struct
- `p` / `sym` — look up globals and symbols

`list` is the workhorse and is documented in [references/list-command.md](references/list-command.md). `tree`/`foreach` are extension points.

## Workflow

When Master asks to walk a data structure in crash:

1. **Identify the target** — what struct, what list/tree links it together.
2. **Find the entry point** — a global (`p bus_kset`) or a known head (`list_head`/`LIST_HEAD`).
3. **Compute offsets** — `struct -o <struct>`, confirm against the ABI table above.
4. **Traverse** — `list -o <offset> -s <struct.member> -H <head>` (or `tree`/`foreach`).
5. **Dereference pointers** — `-s` does NOT auto-deref pointer members; read the pointer first, then `struct <target>` it.
6. **Verify** — the first node's name/fields should look sane (e.g. `kobj.name = "bus"`, first bus is "faux", not ASCII garbage).

## Worked Example: driver core (bus → driver → device)

The canonical first case. Full offsets and command sequence live in [references/driver-core.md](references/driver-core.md).

```
bus_kset (p bus_kset)                       ← global entry
  └─ list kobject.entry -s kobject.name -H   → all buses
       → subsys_private = kobject - 0x18
            ├─ klist_drivers  (+0xd0)  → list -o 0x70 → driver_private → driver (0x90)
            └─ klist_devices (+0xa8)  → list -o 0x70 → device_private → device (0xc8)
```

## Pitfalls (the ones that actually bite)

See [references/pitfalls.md](references/pitfalls.md) for the full writeup. The top offenders:

1. **`start` is a `list_head` address → must use `-H`** (else crash treats it as a struct address → reversed traversal + garbage).
2. **offset `structure.member` format is 2-level max** — a 3-level `driver_private.knode_bus.n_node` fails; use a numeric `-o 0x70`.
3. **`-s` does not auto-deref pointer members** — `-s x.y.z` fails when `y` is a pointer.
4. **`struct.member` "name" is a DWARF symbol, not the `name` field** — static vars get symbol annotation, dynamic allocations don't.

## Reference Files

| File | Content |
|------|---------|
| [references/list-command.md](references/list-command.md) | Full `crash list` command reference (syntax, start semantics, offset, -s, warnings) |
| [references/driver-core.md](references/driver-core.md) | driver core 3-layer offsets + complete command sequence |
| [references/pitfalls.md](references/pitfalls.md) | The six pitfalls, root cause and fix for each |
