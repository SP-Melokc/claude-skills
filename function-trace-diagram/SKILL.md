---
name: function-trace-diagram
description: 绘制带 ANSI 颜色的 ASCII 函数调用追踪图，用紫色/蓝色/青色标注不同层级。每次输出简易版+详细版两个版本。触发词：梳理函数调用、追踪调用栈、画调用图、trace call flow、怎么走的。
---

# Function Trace Diagram Skill

当 Master 要求梳理函数调用栈/调用链时，**同时输出两个版本**：

- **简易版** — 2~4 层深度，只展示核心路径和关键分支，标注阶段分类
- **详细版** — 追到关键子函数，列出大部分函数调用

## 触发词

- "梳理一下调用栈" / "追踪调用链" / "画调用图" / "调用关系"
- "这个流程是怎么走的" / "怎么个调用栈"
- "trace the call flow" / "draw the call stack"

## 配色方案（紫色/蓝色/青色为主色调）

```
[1;36m 青 色[0m — 顶层入口 / VFS / 通用框架层 (syscall、configfs、driver_register 等)
[1;34m 蓝 色[0m — 中间层 / 核心子系统 / 关键操作
[1;35m 紫 色[0m — 底层回调 / 驱动层 / 硬件操作
[1;33m 黄 色[0m — 目录路径 / 文件路径 / 节点名称
[1;32m 绿 色[0m — 资源分配动作 (malloc, kzalloc, init, create 等)
[1;37m 白色亮体[0m — 关键变量 / 数据结构名 / 重要标志位
[90m   灰 色[0m — 注释、说明文字、行号
[1;31m 红 色[0m — 保底备用：特别关键的单点（★ 标注）
```

## 输出格式

### 简易版（Simple Version）

- 深度控制在 2~4 层
- 用 `[阶段标签]` 将步骤分组，标签如：`[结构初始化]` `[状态初始化]` `[PM ops绑定]` `[全局注册]` `[debugfs]`
- 每一步只列核心操作，不展开子调用
- 用 `①②③④⑤` 编号关键阶段
- 结尾一行总结文件路径

示例格式：

``` text
  [1;36mentry_func()[0m
    │
    ├── [1;34m[阶段一]  做什么事 / 什么数据结构[0m
    ├── [1;34m[阶段二]  xxx初始化[0m
    ├── [1;34m[阶段三]  绑定 / 注册[0m
    │     ├── [1;35msub_callback_A()[0m
    │     ├── [1;35msub_callback_B()[0m
    │     └── [90m← 这 N 个回调构成了完整能力[0m
    ├── [1;34m[阶段四]  全局注册[0m    [1;33mlist_add → global_list[0m
    └── [1;34m[阶段五]  收尾[0m     [1;35mxxx_debug_add()[0m
```

### 详细版（Detailed Version）

- 深度追到子函数的子函数，不设上限
- 标注关键变量的赋值和状态变化
- 标注锁的获取/释放
- 标注 sysfs 节点创建、通知链调用
- 每个重要步骤标行号

示例格式：

``` text
  [1;36mentry_func(cpu)[0m                                                     [90m// file.c:行号[0m
    │
    ├─ ① [1;34mkey_check()[0m
    │     ├─ 有 → [1;35mfast_path()[0m
    │     │        ├─ stop → 更新掩码 → restart
    │     │        └─ （同 cluster 后续 CPU 的快速路径）
    │     │
    │     ├─ 有但 inactive → new_policy = false（复用旧 policy）
    │     │
    │     └─ 无 → [1;37mnew_policy = true[0m
    │           └─ [1;35mpolicy_alloc(cpu)[0m                      [90m// file.c:1257[0m
    │                ├─ [1;32mkzalloc(policy)[0m
    │                ├─ [1;32mcpumask_var_t init[0m               [90m(cpus / related_cpus)[0m
    │                ├─ [1;32mkobject_init_and_add()[0m           [90m→ /sys/.../policyN[0m
    │                ├─ [1;35minit_rwsem(&policy->rwsem)[0m       [90m// 保护 policy 字段[0m
    │                ├─ [1;35mfreq_constraints_init()[0m          [90m// QoS 约束树 (min/max)[0m
    │                ├─ [1;32m注册通知链[0m
    │                │   └─ [1;35mfreq_qos_add_notifier(MIN/MAX)[0m
    │                │       └─ 当 thermal / 用户空间改频率限制时触发回调
    │                ├─ [1;35mspin_lock_init(&transition_lock)[0m
    │                └─ [1;35mINIT_WORK(&update, handle_update)[0m
    │                     └─ 延迟更新（atomic 上下文触发）
    │
    ├─ ② [1;34m核心初始化[0m    [1;35monline_sub(policy, cpu, new_policy)[0m   [90m// file.c:1389[0m
    │     ├─ guard(policy_write)          [90m← 拿写锁，scope guard 自动释放[0m
    │     ├─ policy->cpu = cpu
    │     ├─ policy->governor = NULL
    │     ├─ [new] [1;35mdriver->init(policy)[0m
    │     │     └─ 填充 cpuinfo / freq_table / transition_latency
    │     ├─ [1;35mcpumask_and(policy->cpus, cpu_online_mask)[0m
    │     ├─ [new] [1;32mper-cpu 映射建立[0m + [1;33msysfs 软链接[0m
    │     ├─ [new] Qos Request init
    │     │     [1;35mblocking_notifier_call_chain(CPUFREQ_CREATE_POLICY)[0m
    │     ├─ [1;35mdriver->get() → policy->cur[0m  [90m← 读真实频率[0m
    │     ├─ [new] [1;35madd_dev_interface(policy)[0m
    │     │     └─ 创建 sysfs: available_freqs / cur_freq / stats / ...
    │     │     [1;33mlist_add → cpufreq_policy_list[0m
    │     │     [1;35mregister_em(policy)[0m      [90m→ Energy Model (EAS)[0m
    │     └─ [1;34m★ init_policy(policy)[0m   [90m// 决定 governor 并启动[0m
    │          └─ [1;35mcpufreq_set_policy()[0m
    │               ├─ exit 旧 governor → [1;35minit_governor()[0m → [1;35mstart()
    │               └─ sysfs 通知
    │
    ├─ ③ [1;35mkobject_uevent(KOBJ_ADD)[0m           [90m← 通知 udev[0m
    ├─ ④ [1;35mdriver->ready(policy)[0m               [90m← 最后一哆嗦[0m
    └─ ⑤ [new] [1;35mthermal_cooling_register(policy)[0m [90m← 温控可限制频率[0m
```

## 工作流

### Step 1: 确认范围

- 从哪个入口开始？到什么层级为止？
- 只要内核侧还是包含用户态入口？

### Step 2: 查源码验证

**必须先查源码再画图，不准推测函数名/调用关系。** 用 Grep / Read 确认所有函数名真实存在。

### Step 3: 分层归类

| 层级 | 颜色 | 典型函数 |
|------|------|---------|
| 顶层 (框架/系统调用/入口) | 青色 | `vfs_write()`, `configfs_mkdir()`, `cpufreq_online()`, `xxx_store()` |
| 中间层 (子系统核心逻辑) | 蓝色 | `xxx_alloc()`, `xxx_bind()`, `xxx_init()`, 核心操作函数 |
| 底层 (驱动/硬件/回调) | 紫色 | `ops->xxx()`, `driver->xxx()`, `xxx_open()`, 具体回调 |

### Step 4: 输出两个版本

- 简易版在前，用分隔线隔开
- 详细版在后
- 每个版本下方标注配色说明

### Step 5: 收尾

图后 1-2 句总结核心设计意图或最关键的跳转点。

## 反例（禁止）

- [SYMBOL] 没查源码直接画图（脑补函数名）
- [SYMBOL] 用模糊描述代替函数名（"内核做了一些处理"）
- [SYMBOL] 忘记输出两个版本（只出了简易版或只出了详细版）
- [SYMBOL] 没有颜色标注层级
- [SYMBOL] 图后没有配色说明
- [SYMBOL] 漏掉关键跳转点
