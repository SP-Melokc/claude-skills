---
name: function-trace-diagram
description: 绘制带 ANSI 颜色的 ASCII 函数调用追踪图，用蓝/黄/紫标注函数层级（入口/骨干/叶子）。每次输出简易版+详细版两个版本。触发词：梳理函数调用、追踪调用栈、画调用图、trace call flow、怎么走的。
---

# Function Trace Diagram Skill

当 Master 要求梳理函数调用栈/调用链时，**同时输出两个版本**：

- **简易版** — 2~4 层深度，只展示核心路径和关键分支，标注阶段分类
- **详细版** — 追到关键子函数，列出大部分函数调用

## 触发词

- "梳理一下调用栈" / "追踪调用链" / "画调用图" / "调用关系"
- "这个流程是怎么走的" / "怎么个调用栈"
- "trace the call flow" / "draw the call stack"

## ANSI 配色方案（蓝/黄/紫标注函数层级）

### 颜色编码表（直接复制粘贴使用）

下面的每个颜色标记中，`ESC` 代表一个 **字面 ESC 字符（ASCII 27，0x1B）**，不能用 `\033` 字符串代替。你需要在输出时嵌入真正的 ESC 字节。

颜色标记 + 要着色的文本 + 重置标记：

```
ESC[1;36m  ← 青色粗体开始（顶层框架入口 / VFS / 子系统注册）
ESC[1;34m  ← 蓝色粗体开始（核心入口函数 / 主逻辑承载者）
ESC[1;33m  ← 黄色粗体开始（骨干/核心链路函数，链路上最关键的几个节点）
ESC[1;35m  ← 紫色粗体开始（叶子子函数 / 辅助调用 / 驱动回调）
ESC[1;32m  ← 绿色粗体开始（资源分配动作: kzalloc, init, create 等）
ESC[1;37m  ← 白色亮体开始（关键变量 / 数据结构名 / 重要标志位）
ESC[1;31m  ← 红色粗体开始（关键转折点 / 失败返回，★ 标注用）
ESC[90m    ← 灰色开始（注释、说明文字、行号）
ESC[0m     ← 关闭所有颜色（每条着色文本结束必须加这个）
```

### 三层配色规则（函数调用栈）

画函数调用栈时，用三层颜色区分主次，让核心链路一眼可见：

1. **蓝（ESC[1;34m）** = 核心入口函数——最外层、承载主逻辑的那个函数（如 `collapse_scan_mm_slot`）。
2. **黄（ESC[1;33m）** = 骨干函数——链路上最关键的几个节点（如 `collapse_single_pmd` → `collapse_scan_pmd` → `collapse_huge_page` 这条主线）。
3. **紫（ESC[1;35m）** = 叶子子函数——其余辅助/细节调用（`find_xxx`、`spin_lock`、`collect_xxx` 等）。

即：**蓝 → 黄 → 紫 = 入口 → 骨干 → 细节**。青色留给更上层的框架/VFS 入口（如 `vfs_write`、`configfs_mkdir`）。**所有函数名都要上色，不许有裸露的函数名。**

用法示例：`ESC[1;36mconfigfs_mkdir()ESC[0m` → 输出后 `configfs_mkdir()` 就变成青色。

### 如何生成真正的 ESC 字符

在 Claude Code 中，你要在文本里嵌入真正的 ESC 字节（0x1b），方法：
- 如果终端支持：输入 `Ctrl+V` 然后 `Ctrl+[`（会插入一个字面的 ESC）
- 如果输出编程语言：写 `\x1b` 或 `\033` 在字符串中
- **最可靠的方法**：直接复制下面这行中看不见的 ESC 字符：

``  ← 这行只有一个 ESC 字符。复制它。

### 三条铁律：不能犯的错

**错误1：用 markdown 代码块包裹**
```
│  └─ [1;36mkswapd() ← 代码块会吞ESC，颜色不显示
```
→ 正确做法：直接输出，不在 ``` 代码块内。

**错误2：用行内反引号包裹颜色文本**
```
`kswapd()` ← 反引号也会吞ESC
```
→ 正确做法：函数名直接用颜色包裹，不加 `。

**错误3：用 \033 字符串代替真正的 ESC 字节**
```
\033[1;36m ← 终端看到的是反斜杠+数字，不是颜色
```
→ 正确做法：输出真正的 0x1B 字节。

### 每次输出后必须附配色表

图下方必须附一行配色说明：

```
配色：ESC[1;36mCyanESC[0m=框架入口  ESC[1;34mBlueESC[0m=核心入口  ESC[1;33mYellowESC[0m=骨干函数  ESC[1;35mPurpleESC[0m=叶子子函数  ESC[1;32mGreenESC[0m=分配  ESC[90mGrayESC[0m=注释
```

---

## 输出格式

### 简易版（Simple Version）

- 深度控制在 2~4 层
- 用 ESC[1;34m[阶段标签]ESC[0m 将步骤分组
- 每一步只列核心操作，不展开子调用
- 用 ①②③④⑤ 编号关键阶段
- 结尾一行总结文件路径

示例格式（输出时 ANSI 必须生效）：

---

ESC[1;36mentry_func()ESC[0m
  │
  ├── ESC[1;34m[阶段一]ESC[0m  做什么事 / 什么数据结构
  ├── ESC[1;34m[阶段二]ESC[0m  xxx初始化
  ├── ESC[1;34m[阶段三]ESC[0m  绑定 / 注册
  │     ├── ESC[1;35msub_callback_A()ESC[0m
  │     ├── ESC[1;35msub_callback_B()ESC[0m
  │     └── ESC[90m← 这 N 个回调构成了完整能力ESC[0m
  ├── ESC[1;34m[阶段四]ESC[0m  全局注册    ESC[1;33mlist_add → global_listESC[0m
  └── ESC[1;34m[阶段五]ESC[0m  收尾     ESC[1;35mxxx_debug_add()ESC[0m

配色：ESC[1;36mCyanESC[0m=框架入口  ESC[1;34mBlueESC[0m=核心入口  ESC[1;33mYellowESC[0m=骨干函数  ESC[1;35mPurpleESC[0m=叶子子函数  ESC[90mGrayESC[0m=注释

---

### 详细版（Detailed Version）

- 深度追到子函数的子函数，不设上限
- 标注关键变量的赋值和状态变化
- 标注锁的获取/释放
- 每个重要步骤标行号

示例格式（输出时 ANSI 必须生效）：

---

ESC[1;36mentry_func(cpu)ESC[0m                                                     ESC[90m// file.c:行号ESC[0m
  │
  ├─ ① ESC[1;34mkey_check()ESC[0m
  │     ├─ 有 → ESC[1;35mfast_path()ESC[0m
  │     │        ├─ stop → 更新掩码 → restart
  │     │        └─ （快速路径：跳过重复初始化）
  │     │
  │     └─ 无 → ESC[1;37mnew_policy = trueESC[0m
  │           └─ ESC[1;35mpolicy_alloc(cpu)ESC[0m                      ESC[90m// file.c:1257ESC[0m
  │                ├─ ESC[1;32mkzalloc(policy)ESC[0m
  │                ├─ ESC[1;32mcpumask_var_t initESC[0m               ESC[90m(cpus / related_cpus)ESC[0m
  │                ├─ ESC[1;32mkobject_init_and_add()ESC[0m           ESC[90m→ /sys/.../policyNESC[0m
  │                ├─ ESC[1;35minit_rwsem(&policy->rwsem)ESC[0m       ESC[90m// 保护 policy 字段ESC[0m
  │                ├─ ESC[1;35mfreq_constraints_init()ESC[0m          ESC[90m// QoS 约束树 (min/max)ESC[0m
  │                ├─ ESC[1;32m注册通知链ESC[0m
  │                │   └─ ESC[1;35mfreq_qos_add_notifier(MIN/MAX)ESC[0m
  │                │       └─ 当 thermal / 用户空间改频率限制时触发回调
  │                └─ ESC[1;35mINIT_WORK(&update, handle_update)ESC[0m
  │                     └─ 延迟更新（atomic 上下文触发）
  │
  ├─ ② ESC[1;34m核心初始化ESC[0m    ESC[1;35monline_sub(policy, cpu, new_policy)ESC[0m   ESC[90m// file.c:1389ESC[0m
  │     ├─ guard(policy_write)          ESC[90m← 拿写锁，scope guard 自动释放ESC[0m
  │     ├─ policy->cpu = cpu
  │     ├─ policy->governor = NULL
  │     ├─ [new] ESC[1;35mdriver->init(policy)ESC[0m
  │     │     └─ 填充 cpuinfo / freq_table / transition_latency
  │     ├─ ESC[1;35mcpumask_and(policy->cpus, cpu_online_mask)ESC[0m
  │     ├─ [new] ESC[1;32mper-cpu 映射建立ESC[0m + ESC[1;33msysfs 软链接ESC[0m
  │     ├─ [new] Qos Request init
  │     │     ESC[1;35mblocking_notifier_call_chain(CPUFREQ_CREATE_POLICY)ESC[0m
  │     ├─ ESC[1;35mdriver->get() → policy->curESC[0m  ESC[90m← 读真实频率ESC[0m
  │     └─ ESC[1;34m★ init_policy(policy)ESC[0m   ESC[90m// 决定 governor 并启动ESC[0m
  │          └─ ESC[1;35mcpufreq_set_policy()ESC[0m
  │               ├─ exit 旧 governor → ESC[1;35minit_governor()ESC[0m → ESC[1;35mstart()ESC[0m
  │               └─ sysfs 通知
  │
  ├─ ③ ESC[1;35mkobject_uevent(KOBJ_ADD)ESC[0m           ESC[90m← 通知 udevESC[0m
  └─ ⑤ [new] ESC[1;35mthermal_cooling_register(policy)ESC[0m ESC[90m← 温控可限制频率ESC[0m

配色：ESC[1;36mCyanESC[0m=框架入口  ESC[1;34mBlueESC[0m=核心入口  ESC[1;33mYellowESC[0m=骨干函数  ESC[1;35mPurpleESC[0m=叶子子函数  ESC[1;32mGreenESC[0m=分配/初始化  ESC[1;37mWhiteESC[0m=关键变量  ESC[1;31mRedESC[0m=失败/错误  ESC[90mGrayESC[0m=注释

---

### 颜色使用分布指导

| 层 | 颜色 | 占图比例建议 |
|---|------|-------------|
| 顶层框架入口 | ESC[1;36mCyanESC[0m | ~10% |
| 核心入口函数 | ESC[1;34mBlueESC[0m | ~15% |
| 骨干函数 | ESC[1;33mYellowESC[0m | ~20% |
| 叶子子函数 | ESC[1;35mPurpleESC[0m | ~30% |
| 资源分配操作 | ESC[1;32mGreenESC[0m | ~5% |
| 关键变量 | ESC[1;37mWhiteESC[0m | ~5% |
| 注释/行号 | ESC[90mGrayESC[0m | ~15% |

### 简易版（Simple Version）

- 深度控制在 2~4 层
- 用 `[阶段标签]` 将步骤分组，标签如：`[结构初始化]` `[状态初始化]` `[PM ops绑定]` `[全局注册]` `[debugfs]`
- 每一步只列核心操作，不展开子调用
- 用 `①②③④⑤` 编号关键阶段
- 结尾一行总结文件路径

示例格式（[SYMBOL] 注意：下面是纯文本，不包裹在代码块中）：

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

### 详细版（Detailed Version）

- 深度追到子函数的子函数，不设上限
- 标注关键变量的赋值和状态变化
- 标注锁的获取/释放
- 标注 sysfs 节点创建、通知链调用
- 每个重要步骤标行号

示例格式（[SYMBOL] 注意：纯文本输出，不用代码块）：

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

## 工作流

### Step 1: 确认范围

- 从哪个入口开始？到什么层级为止？
- 只要内核侧还是包含用户态入口？

### Step 2: 查源码验证

**必须先查源码再画图，不准推测函数名/调用关系。** 用 Grep / Read 确认所有函数名真实存在。

### Step 3: 分层归类

| 层级 | ANSI 代码 | 典型函数 |
|------|----------|---------|
| 顶层 (框架入口) | ESC[1;36m (cyan bold) | vfs_write(), configfs_mkdir(), syscall entry |
| 核心入口函数 | ESC[1;34m (blue bold) | collapse_scan_mm_slot(), xxx_init(), balance_pgdat() |
| 骨干函数 | ESC[1;33m (yellow bold) | collapse_single_pmd(), collapse_huge_page(), shrink_node() |
| 叶子子函数 | ESC[1;35m (purple bold) | find_xxx(), spin_lock(), collect_xxx() |
| 分配/创建 | ESC[1;32m (green bold) | kzalloc(), init_rwsem(), kthread_run() |
| 关键变量 | ESC[1;37m (white bright) | kswapd_order, func_list, max_active |
| 注释/行号 | ESC[90m (gray) | // file.c:123, ← 说明文字 |
| 错误/警告 | ESC[1;31m (red bold) | -EINVAL, goto retry, BUG() |

### Step 4: 输出两个版本

- **先执行自检清单**：真正的 ESC 字节？不在代码块中？不在反引号中？三项全部通过再输出。
- 简易版在前，用 `---` 分隔线隔开
- 详细版在后
- 每个版本下方标注配色表（用真正的 ANSI 着色文本展示每个颜色）

### Step 5: 收尾

图后 1-2 句总结核心设计意图或最关键的跳转点。

## 输出前自检清单（强制）

在输出每个带颜色的 ASCII 图之前，先回答以下 3 个问题：

1. **ESC 字符是真的吗？** 我的输出文本中，颜色标记开头是真正的 ESC 字节（0x1b），还是写了 `\033` 四个字符？只有真正的 0x1B 才能让终端变色。
2. **代码块有没有包住图？** 图前有没有 ` ```text ` 或 ` ``` ` ？图后有没有 ` ``` ` ？如果有，全部删掉。
3. **反引号有没有包住着色文本？** 类似 ` [1;35mfsg_alloc() [0m ` 这种上一行和下一行的颜色部分，有没有被反引号 ` ` ` 包裹？如果有，把反引号去掉。

如果以上 3 点全部检查通过，颜色就会正常显示。

## 反例（禁止）

- 没查源码直接画图（脑补函数名）
- 用模糊描述代替函数名（"内核做了一些处理"）
- 忘记输出两个版本（只出了简易版或只出了详细版）
- **用代码块包裹 ANSI 着色图 → 颜色全挂**
- **用反引号包裹着色文本 → 颜色局部挂**
- **用 \033 四字符代替真正的 ESC 字节 → 颜色全挂**
- 没有颜色标注层级
- **函数名裸露未上色（所有函数调用都必须套上颜色标记，不许出现光秃秃的函数名）**
- 图后没有配色说明
- 配色表中写了颜色名但没有附实际的 ANSI 标签
