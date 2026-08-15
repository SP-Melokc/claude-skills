# Writing Style Guide

This is the authoritative reference for Master's document writing style. Extracted from analysis of IRQ, CPU IDLE, Device Tree, and OOM Killer documents.

---

## Document Skeleton (H1 Structure)

```
# 核心总结 (or 核心整理)   ← H1, MANDATORY
# 关键结构体               ← H1, MANDATORY
# 核心函数                 ← H1, MANDATORY, largest section
# 案例 / 番外 / Q&A        ← H1, optional
```

---

## Section 1: 核心总结 (Core Summary)

- Numbered list (1. 2. 3.), each entry is an independent core insight
- **Heavy use of bold** to emphasize key conclusions
- Interleave Obsidian callouts (`> [!type]`) to expand details without bloating the main text

### Callout usage here:
- Expand on a numbered item's details
- Hardware behavior descriptions ("CPU硬件自动做了这些事情")
- Callout types: `> [!note]` (gentle), `> [!info]` (details), `> [!warning]` (cautions), `> [!tip]` (insights), `> [!important]` (key conclusions), `> [!question]` (uncertain points)

### Example pattern:
```markdown
1. Core conclusion in one sentence, **key point in bold**

> [!note]
> Expanded description, possibly step-by-step hardware/software behavior...
>
> (1) First step does X
> (2) Second step does Y

2. Next core conclusion...
```

---

## Section 2: 关键结构体 (Key Structures)

### Per-struct format:
Each struct as H2 heading:
```markdown
## struct xxx_desc
```

### Organization order:
1. **Definition first**: One-line callout explaining the struct's role (`> [!info]`)
2. **Relationship diagram**: Image/diagram showing inter-struct relationships
3. **Full struct code**: With kernel comments, trim non-critical fields for long structs
4. **Key field annotations**: Inline Chinese comments on important fields
5. **Sub-structs**: As H3, following the same pattern

### Example pattern:
```markdown
## struct irq_desc

> [!info]
> irq_desc, 即中断描述符, 与中断号/中断线一一对应.

![](relationship diagram)

` ``c
/**
 * struct irq_desc - interrupt descriptor
 * ...kernel comments preserved...
 */
struct irq_desc {
    ...
};
` ``

### Istate  (H3, enum values follow their struct)
` ``c
enum {
    IRQS_AUTODETECT = 0x00000001,
    ...
};
` ``

### struct irq_data  (H3, sub-struct)
...
```

### Enum / flag handling:
- H3 right after their owning struct
- Full source + key value explanations
- Optionally add diagram showing bit layout

---

## Section 3: 核心函数 (Core Functions) — Most Important

### Nested hierarchy rules:

```
H1: 核心函数
  H2: 💎FunctionA (core entry)
    H3: 🌠SubFunctionA1 (key sub-function)
      H4: Grandchild function A1a
        H5: Great-grandchild A1a1
    H3: SubFunctionA2
  H2: ❤FunctionB (important flow)
    H3: SubFunctionB1
```

- H2 uses emoji prefix for importance: 💎 = core entry, 🌠 = key sub-function, ❤ = important flow
- Nesting can go deep (observed up to H5)

### Per-function template:

```markdown
### 🌠 select_bad_process()   ← H3: function name + short Chinese description

This function traverses all processes, calling oom_evaluate_task() to evaluate/select a suitable process to kill.
← One sentence saying what the function does

` ``c
/*
 * Simple selection loop. We choose the process with the highest number of 'points'.
 */
static void select_bad_process(struct oom_control *oc)
{
    ...
}
` ``
← Full source with kernel comments, key lines annotated in Chinese

#### 评估 oom_evaluate_task()   ← H4: next level sub-function
...
```

### Call chain display:
Use call stack trace format:
```
[<ffffffc0801431ec>] __handle_irq_event_percpu+0xbc
[<ffffffc080143488>] handle_irq_event+0x48
[<ffffffc0801492b0>] handle_fasteoi_irq+0x160
...
```

Or in code block showing setup relationships:
```JavaScript
set_handle_irq(gic_handle_irq);
```

---

## Code Block Language Labels

| Content Type | Label |
|-------------|-------|
| C kernel code | ```c |
| Assembly / call stacks | ```Plain Text or ```XML |
| Register ops / inline asm | ```JavaScript |
| Macro / preprocessor | ```c |

**Always use ```c for C code.**

---

## Callout Type Semantics (Obsidian Standard)

Use Obsidian standard `> [!type]` callout syntax. All content lines inside the callout **must** be prefixed with `>`.

| Type | When to use |
|------|------------|
| `> [!note]` | General explanation, background context, step-by-step description |
| `> [!info]` | Struct/concept definitions ("xxx即xxx"), flag lists, framework details |
| `> [!important]` | Key conclusions, critical design points, core call chain entry points |
| `> [!warning]` | Cautions, anti-patterns, things that will break |
| `> [!tip]` | Insights, best practices, coding tricks, architecture observations |
| `> [!question]` | Uncertain points, unanswered questions, items needing verification |
| `> [!abstract]` | Opening summary, document TL;DR |
| `> [!summary]` | Closing recap, key takeaways |

### Callout content types:
- **Definition** (`[!info]`): One-sentence definition + expanded explanation
- **Step-by-step** (`[!note]`): Numbered list, hardware + software separated
- **Flag collection** (`[!info]`): List related flags and meanings
- **Warning** (`[!warning]`): Key conclusions that must not be missed, often bold
- **Core entry** (`[!important]`): Mark critical function call chain starting points

### Callout format example:
```markdown
> [!warning]
> **poll=false：这条频率设置是异步的。** 发送完 SCMI 消息后立即返回，
> 不阻塞等待固件完成 DVFS。仅当订阅了 LEVEL_CHANGED 通知时才能
> 得到确切的完成确认。
```

### H2/H3 function heading emoji:
These are inline emoji in headings (not callouts), kept for visual navigation:
- 💎 = core entry functions (H2)
- 🌠 = key sub-functions (H3)
- ❤ = important flows (H2)

---

## Tone & Expression Habits

### Colloquial markers:
- "目前来看" — personal judgment based on code reading
- "注意细节" — emphasizing easily overlooked points
- "这里写的可能有点问题" — marking uncertain areas
- "等下" — transition warning
- "我们发现" — introducing analysis conclusions

### Technical depth characteristics:
- Never satisfied with API level — chase to hardware registers (DAIF, ICC_IAR1_EL1)
- Function analysis goes to the bottom (entry → deepest helper)
- Struct fields explained one by one for key fields
- Complete call chains
- Cross-references: CSDN blogs, kernel docs, own other docs

### Typography preferences:
- Key conclusions **bold**
- Every code block preceded by a Chinese lead-in sentence
- Images/whiteboards interleaved between structs and functions
- Key point summary after large code blocks

---

## Document Writing Checklist

1. [ ] H1: 核心总结 — 3~10 numbered insights
2. [ ] H1: 关键结构体 — each key struct as H2, full definition + key field annotations
3. [ ] H1: 核心函数 — nested H2→H3→H4..., each level with full source + Chinese explanation
4. [ ] Code uses ```c label
5. [ ] Callouts use correct emoji
6. [ ] Key conclusions bolded
7. [ ] Complete call chains shown
8. [ ] Relationship/flow diagrams where needed
9. [ ] Optional H1: 案例/番外
10. [ ] Reference links at top (if any)
