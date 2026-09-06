# crash `list` command — full reference

## Syntax

```
list [[-o] offset][-e end][-[s|S] struct[.member[,member] [-l offset]] -[x|d]]
     [-r|-B] [-h [-O head_offset]|-H] start
```

## Two list kinds

`list` handles two formats. Kernel `bus_kset->list`, `klist_drivers`, `klist_devices` are all **list_head-linked** (doubly-linked).

1. **Singly-linked** — a `next` pointer to the next struct. Ends at NULL / start / itself.
2. **list_head-linked** — an embedded `struct list_head` (next + prev), usually headed by an external standalone `LIST_HEAD()`.

## Key fact: `list` prints STRUCT addresses, not list_head addresses

The column of addresses `list` dumps are **data-structure addresses** (struct bases). To recover the struct base from a list_head, crash needs the `offset`:

```
struct_base = list_head_address - offset
```

This is container_of, in crash's own terms.

## `start` semantics (decides how crash reads your address)

| form | start is | crash does |
|------|----------|-----------|
| `start` (default) | first **struct** address | treat it as a struct |
| `-H start` | **standalone list_head** address | iterate from `start.next` |
| `-h start` | **struct containing list_head** | read the list_head inside |
| `-l offset` (with `-s`) | **embedded list_head** address | iterate from `start`, offset via `-l` |

> `bus_kset->list`, `klist_drivers.k_list`, `klist_devices.k_list` are standalone list_head addresses → always use **`-H`**.

## `offset` (`-o`)

`offset` = distance from struct start to the **next pointer**. For list_head links, `next` is list_head's first field, so offset == list_head's offset in the struct.

Two spellings:

| spelling | notes | example |
|----------|-------|---------|
| `structure.member` | `-o` optional; 2-level max | `list kobject.entry ...` |
| numeric bytes | explicit `-o` safer | `list -o 0x70 ...` |

> A 3-level `driver_private.knode_bus.n_node` fails (`invalid argument`); use numeric `-o 0x70`.

## `-s` / `-S`

- `-s struct` — print whole struct
- `-s struct.member` — print one member
- `-s struct.member.member` — nested (embedded structs & arrays only, **no pointer auto-deref**)
- `-s struct.member[index]` — array element
- comma-separated: `-s struct.a,b,c`
- `-S struct` — fast path, reads memory directly (1/2/4/8-byte members)

> `-s driver_private.driver.name` fails (`invalid data structure member reference`) because `driver` is a pointer. Read the pointer first (`-s driver_private.driver`), then `struct device_driver <ptr>`.

## Other options

| flag | purpose |
|------|---------|
| `-r` | reverse traversal (prev, not next) |
| `-e end` | explicit end address when the list terminator is unusual |
| `-O offset` | with `-h` only: head's list_head offset differs from node offset |
| `-x` / `-d` | force hex / decimal output |
| `-B` | Brent loop detection (low memory, long lists) |

## Official warnings

1. **`-h` trap**: `-h` assumes every list_head in the list is embedded in the *same* struct type. Passing through an external standalone LIST_HEAD yields a wrong address + bogus `-s` data for that entry.
2. **`-s` + `-l` trap**: same issue when `start` is an embedded list_head address and the walk passes an external list head.

## The pattern used throughout the driver-core case

```
list -o <numeric-offset> -s <struct.member> -H <list_head-address>
```

| target | head | offset | `-s` |
|--------|------|--------|------|
| all buses | `bus_kset` (list at 0) | `kobject.entry` (0x8) | `kobject.name` (embedded, prints directly) |
| a bus's drivers | `subsys_private + 0xd0` | `0x70` | `driver_private.driver` (pointer → grab address) |
| a bus's devices | `subsys_private + 0xa8` | `0x70` | `device_private.device` (pointer → grab address) |

Rule of thumb: **embedded members print directly; pointer members give you an address to `struct` later.**
