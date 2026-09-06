# Pitfalls — root cause & fix

Six traps hit while walking the driver core, ordered by how badly they bite.

## 1. `bus_type` has no `p` field since ~6.x/7.0

Old kernels had `struct bus_type { struct subsys_private *p; ... }`, so `bus->p` worked. Newer kernels removed it — `struct bus_type` now ends at `driver_override` / `need_parent_lock`.

**Why**: to make `bus_type` const (read-only segment) and separate public descriptor from private data.

**Fix**: use `bus_to_subsys()` which walks the global `bus_kset->list` and matches `sp->bus == bus`.

**Symptom**: `p platform_bus_type` output stops at `need_parent_lock` — not a crash bug.

## 2. `bus_type - 0x128` is flat wrong

`0x128` is the offset of `subsys_private.bus` (a pointer field). Its *value* is the `bus_type` address, but that does NOT mean `bus_type` sits at `subsys_private + 0x128`.

**Why**: `subsys_private` is heap-allocated (`kzalloc_obj()` in `bus_register()`), `bus_type` is a static global. Two unrelated allocations, linked by a one-way pointer.

**Symptom**: reading `bus_type - 0x128` dumps rodata string garbage (`"class_ed" "v_iter_i" "nit"`).

## 3. `start` is a list_head address → must use `-H`

`list`'s `start` has three meanings (default struct / `-H` list_head / `-h` struct-containing-list_head). Passing a list_head address *without* `-H` makes crash treat it as a struct address.

**Symptom**: reversed traversal (reads `head.prev` instead of `head.next`) + garbage member output. Looks like a crash bug, but it's a `start` semantics mismatch.

## 4. offset `structure.member` format is 2-level max

`list driver_private.knode_bus.n_node ...` (3-level) fails with `invalid argument: driver_private`. The `-s` option supports multi-level nesting, but the `offset` argument only supports 2-level `structure.member`.

**Fix**: numeric offset — `list -o 0x70 ...`.

## 5. `-s` does NOT auto-dereference pointer members

`-s driver_private.driver.name` fails with `invalid data structure member reference: driver.name` because `driver` is a pointer. Nested `-s` only walks embedded structs and arrays.

**Fix**: `-s driver_private.driver` to grab the pointer value, then `struct device_driver <ptr>`.

## 6. DWARF symbol annotation ≠ `name` field

`driver = 0xffffffc082baea18 <tegra194_cbb_driver+40>` — the `<...>` is a **DWARF symbol name** (C variable, underscores), not the `device_driver.name` field (sysfs name, hyphens).

- static vars (most drivers) → have symbols → auto-annotated
- dynamic allocations (most devices) → no symbol → bare address

The `+40` means `driver_private.driver` points at the `device_driver` embedded inside `platform_driver`, offset 40 (5 function pointers probe/remove/shutdown/suspend/resume).

**To get the real sysfs name, always `struct`-dereference and read the `name` field.**
