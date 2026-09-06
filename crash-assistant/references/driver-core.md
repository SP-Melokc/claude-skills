# driver core traversal — offsets & command sequence

The canonical case: walk `bus_kset` down to every driver and device. Based on Linux 6.15/7.0, arm64, `CONFIG_LOCKDEP=n`.

## The 3-layer map

```
bus_kset (global kset)
  └─ list (list_head, offset 0)          ← head
       └─ node = subsys_private.subsys.kobj.entry

subsys_private (one bus)                  SIZE 0x1a0
  ├─ subsys (kset)          0x0
  ├─ klist_devices          0xa0  ──────────┐
  ├─ klist_drivers          0xc8  ──────┐   │
  └─ bus (bus_type *)       0x128       │   │
                                         │   │
   driver chain (head +0xd0)             │   device chain (head +0xa8)
   driver_private (SIZE 0x98)            │   device_private (SIZE 0xd8)
     ├─ kobj          0x0                │     ├─ klist_children 0x0
     ├─ klist_devices 0x40               │     ├─ knode_parent   0x28
     ├─ knode_bus     0x68               │     ├─ knode_driver   0x48
     │   └─ n_node    0x70 ← list_head   │     ├─ knode_bus      0x68
     ├─ mkobj         0x88               │     │   └─ n_node     0x70 ← list_head
     └─ driver        0x90 → device_driver│    ├─ knode_class    0x88
                                          │    ├─ deferred_probe 0xa8
                                          │    ├─ async_driver   0xb8
                                          │    ├─ deferred_probe_reason 0xc0
                                          │    └─ device        0xc8 → struct device
```

## Conversion chains

```
bus_kset->list → kobject = node - 0x8 → subsys_private = kobject - 0x18

driver chain: head = subsys_private + 0xd0
  → driver_private = node - 0x70 → device_driver = driver_private + 0x90

device chain: head = subsys_private + 0xa8
  → device_private = node - 0x70 → struct device = device_private + 0xc8
```

## Full command sequence

```crash
# 1. global entry
crash> p bus_kset
bus_kset = $3 = (struct kset *) 0xffffff80035d6c00

# 2. verify (kobj.name MUST be "bus")
crash> struct kset 0xffffff80035d6c00

# 3. list all buses (embedded name prints directly)
crash> list kobject.entry -s kobject.name -H 0xffffff80035d6c00
ffffff8003529818
  name = 0xffffffc081c003b8 "faux",
ffffff8003529a18
  name = 0xffffffc081c19138 "platform",

# 4. locate target bus → subsys_private
#    platform kobject = 0xffffff8003529a18
#    subsys_private   = 0xffffff8003529a18 - 0x18 = 0xffffff8003529a00

# 5. list drivers (pointer member → grab address)
crash> list -o 0x70 -s driver_private.driver -H 0xffffff8003529ad0
ffffff800365a300
  driver = 0xffffffc082baea18 <tegra194_cbb_driver+40>

# 6. list devices (pointer member → grab address)
crash> list -o 0x70 -s device_private.device -H 0xffffff8003529aa8
ffffff80034aeb00
  device = 0xffffff8004518410,

# 7. dereference to get real names
crash> struct device_driver 0xffffffc082baea18   # name field
crash> struct device 0xffffff8004518410          # kobj.name
```

## Key struct definitions (private, in drivers/base/base.h)

```c
struct subsys_private {                 // base.h:42, SIZE 0x1a0
	struct kset subsys;                  // 0x0
	struct kset *devices_kset;           // 0x60
	struct list_head interfaces;         // 0x68
	struct mutex mutex;                  // 0x78
	struct kset *drivers_kset;           // 0x98
	struct klist klist_devices;          // 0xa0
	struct klist klist_drivers;          // 0xc8
	struct blocking_notifier_head bus_notifier;  // 0xf0
	unsigned int drivers_autoprobe:1;    // 0x120
	const struct bus_type *bus;          // 0x128
	struct device *dev_root;             // 0x130
	struct kset glue_dirs;               // 0x138
	const struct class *class;           // 0x198
	struct lock_class_key lock_key;      // 0x1a0
};

struct driver_private {                 // base.h:79, SIZE 0x98
	struct kobject kobj;                 // 0x0
	struct klist klist_devices;          // 0x40
	struct klist_node knode_bus;         // 0x68
	struct module_kobject *mkobj;        // 0x88
	struct device_driver *driver;        // 0x90
};

struct device_private {                 // base.h:122, SIZE 0xd8
	struct klist klist_children;         // 0x0
	struct klist_node knode_parent;      // 0x28
	struct klist_node knode_driver;      // 0x48
	struct klist_node knode_bus;         // 0x68
	struct klist_node knode_class;       // 0x88
	struct list_head deferred_probe;     // 0xa8
	const struct device_driver *async_driver;  // 0xb8
	char *deferred_probe_reason;         // 0xc0
	struct device *device;               // 0xc8
};
```

## Offset quick-reference

| struct | field | offset |
|--------|-------|--------|
| `kobject` | `name` | 0x0 |
| `kobject` | `entry` | 0x8 |
| `kset` | `kobj` | 0x18 |
| `klist` | `k_list` | 0x8 |
| `klist_node` | `n_node` | 0x8 |
| `subsys_private` | `klist_devices` | 0xa0 |
| `subsys_private` | `klist_drivers` | 0xc8 |
| `subsys_private` | `bus` | 0x128 |
| `driver_private` | `knode_bus` | 0x68 |
| `driver_private` | `driver` | 0x90 |
| `device_private` | `knode_bus` | 0x68 |
| `device_private` | `device` | 0xc8 |
| `device_driver` | `name` | 0x0 |
| `struct device` | `kobj` (name) | 0x0 |
| `struct device` | `init_name` | 0x50 |
