# Document Template Skeleton

This is the base template for a new kernel technical document. Adapt based on whether it's an intro-level doc (stop at 2-3 call levels) or a deep-dive (chase to the bottom).

---

## Intro-Level Doc Template

For overview/newcomer docs (like usb.md, ufs.md, pinctrl.md, pinmux.md, regulator.md).

```markdown
# <Subsystem Name> 子系统：<one-line summary>

> 基于 Linux 7.0 源码，ARM64 平台。本文聚焦 <specific focus>。

## 一、核心总结

1. **第一条核心洞察**

<callout emoji="☠️">
定义性说明，展开细节
</callout>

2. **第二条核心洞察**

<callout emoji="😇">
展开描述...
</callout>

3. **第三条核心洞察**

...

(3~10 entries total)

---

## 二、角色模型（如适用）

如果子系统有明确的 Provider/Consumer 分离，用 ASCII 图展示角色关系：

```
┌─────────────────┐     ┌─────────────────┐
│    Provider     │     │    Consumer     │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
          ┌──────────────────┐
          │     Core Framework│
          └──────────────────┘
```

---

## 三、关键结构体

### struct xxx_desc — <一句话定位>

<callout emoji="☠️">
xxx_desc 是 <一句话定义>
</callout>

` + "``" + "`C++" + `
// <path/to/header.h:line>
struct xxx_desc {
    const char *name;         // 字段注释
    int key_field;            // ★ 核心字段的注释
};
` + "``" + "`" + `

**关键字段解读：**
- **key_field**: 为什么重要，和其他结构体怎么关联

### struct xxx_ops — <一句话定位>
...

---

## 四、核心函数

### 💎xxx_register() — provider 注册入口

<callout emoji="☠️">
<一句话说明这个函数做什么>
</callout>

` + "``" + "`C++" + `
// drivers/xxx/core.c:line
int xxx_register(struct device *dev, const struct xxx_desc *desc)
{
    ...
}
` + "``" + "`" + `

注册流程：

```
xxx_register()
  ├─ 步骤1: ...
  ├─ 步骤2: ...
  └─ 步骤3: ...
```

### 💎xxx_get() — consumer 获取句柄
...

### 🌠xxx_enable() — 核心 enable 逻辑
...

---

## 五、DT 配置（如适用，ARM64 平台）

### Consumer 侧
` + "``" + "`dts" + `
&i2c0 {
    vdd-supply = <&ldo3>;
};
` + "``" + "`" + `

### Provider 侧
` + "``" + "`dts" + `
pmic {
    ldo3: ldo3 {
        regulator-name = "VDD_IO";
        regulator-min-microvolt = <1800000>;
    };
};
` + "``" + "`" + `

---

## 六、与其他子系统的关联（如适用）

<callout emoji="☠️">
<how this subsystem relates to others in the power/IO stack>
</callout>

### 7.1 全景架构
ASCII diagram showing layers

### 7.2 Subsystem A → This → Subsystem B
...

---

## N、必须知道的事实

**1. 事实一**
简短说明

**2. 事实二**
...

(5-8 entries)
```

---

## Deep-Dive Doc Template

For focused analysis of a single mechanism (like OOM Killer). Follow the same skeleton but go deeper — chase call chains to H4/H5 level, include full source for each sub-function.

Key differences from intro docs:
- Each function at H2 gets full `_do_xxx()` → `_really_do_xxx()` nesting
- Include more hardware register details
- Include debugfs interfaces
- Include error paths and rollback logic
```

## ARM64 Notes

- Always mention if the code path differs for ACPI vs Device Tree
- SCMI is increasingly common on ARM64 — check if SCMI plays a role
- GIC (Generic Interrupt Controller) is the standard ARM64 interrupt controller
- Device Tree is the standard ARM64 hardware description; ACPI is server-only
```

## Anti-Patterns

❌ Skipping the architecture explanation and jumping straight to code
❌ Using ````c` instead of ````C++`
❌ Writing multi-paragraph docstrings or multi-line comments
❌ Adding features/abstractions beyond what the task requires
❌ Forgetting the source verification step
❌ Making up function names without grepping the source
