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
- Interleave `<callout>` to expand details without bloating the main text

### Callout usage here:
- Expand on a numbered item's details
- Hardware behavior descriptions ("CPU硬件自动做了这些事情")
- Emoji preference: 😇 (gentle explanation), 🥵 (complex details), 👺 (important warning), 👽 (personal insight)

### Example pattern:
```markdown
1. Core conclusion in one sentence, **key point in bold**

<callout emoji="😇">
Expanded description, possibly step-by-step hardware/software behavior...

(1) First step does X
(2) Second step does Y
</callout>

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
1. **Definition first**: One-line callout explaining the struct's role (emoji: ☠️)
2. **Relationship diagram**: Image/diagram showing inter-struct relationships
3. **Full struct code**: With kernel comments, trim non-critical fields for long structs
4. **Key field annotations**: Inline Chinese comments on important fields
5. **Sub-structs**: As H3, following the same pattern

### Example pattern:
```markdown
## struct irq_desc

<callout emoji="☠️">
irq_desc, 即中断描述符, 与中断号/中断线一一对应.
</callout>

![](relationship diagram)

` ``C++
/**
 * struct irq_desc - interrupt descriptor
 * ...kernel comments preserved...
 */
struct irq_desc {
    ...
};
` ``

### Istate  (H3, enum values follow their struct)
` ``C++
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

` ``C++
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
| C kernel code | ```C++ |
| Assembly / call stacks | ```Plain Text or ```XML |
| Register ops / inline asm | ```JavaScript |
| Macro / preprocessor | ```C++ |

**Always use ```C++ for C code, never ```c.**

---

## Callout Emoji Semantics

| Emoji | When to use |
|-------|------------|
| ☠️ | Definitive explanation ("xxx即xxx"), struct/concept definitions |
| 😇 | Gentle expansion, step-by-step, hardware behavior description |
| 🥵 | Complex details, flag lists, easily confused content |
| 👺 | Important warnings / cautions |
| 👽 | Personal insights / observations ("目前来看...") |
| 😉 | Code structure comments |
| 💎 | Mark core functions (H2 title) |
| 🌠 | Mark key sub-functions (H3 title) |
| ❤ | Mark important flows (H2 title) |
| 💡 | Mark questionable points that need verification |

### Callout content types:
- **Definition** (☠️): One-sentence definition + expanded explanation
- **Step-by-step** (😇): Numbered list, hardware + software separated
- **Flag collection** (🥵): List related flags and meanings
- **Warning** (👺): Key conclusions, often bold

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
4. [ ] Code uses ```C++ label
5. [ ] Callouts use correct emoji
6. [ ] Key conclusions bolded
7. [ ] Complete call chains shown
8. [ ] Relationship/flow diagrams where needed
9. [ ] Optional H1: 案例/番外
10. [ ] Reference links at top (if any)
