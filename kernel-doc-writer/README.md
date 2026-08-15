# kernel-doc-writer

A Claude Code skill for writing Linux kernel technical documentation in a consistent, thorough style. Designed by and for BSP/kernel engineers.

## What it does

Takes a kernel subsystem topic (e.g., "pinctrl", "regulator", "DMA") and produces a comprehensive Markdown document with:

- **Architecture-first analysis** — layer hierarchy, registration order, coupling direction
- **Key data structures** — full source code with per-field Chinese annotations
- **Core function walkthroughs** — nested call chains with complete source
- **Mandatory source verification** — every identifier checked against actual kernel source
- **Subsystem relationship maps** — how it connects to cpufreq, power domain, OPP, etc.

## Document structure

Every generated document follows a three-section skeleton:

| Section | Purpose |
|---------|---------|
| 核心总结 | 3-10 numbered architecture insights with callout expansions |
| 关键结构体 | Each key struct as H2 with full source + field annotations |
| 核心函数 | Nested H2→H3→H4 call chain walkthrough with complete source |

## Style conventions

- Code blocks: ` ```c ` (never ` ```C++ `)
- Callouts: `<callout emoji="☠️">` with specific emoji semantics
- Platform: ARM64 first
- Language: Chinese, with colloquial engineer tone

## Installation

```bash
# Clone to your Claude Code skills directory
git clone <your-repo-url> /c/Users/<you>/.claude/skills/kernel-doc-writer/
```

Or manually copy the `kernel-doc-writer/` directory to `~/.claude/skills/`.

## Dependencies

- **Linux kernel source tree** — the skill reads from a kernel source directory to verify identifiers
- **Claude Code agents** — uses sub-agents for source exploration and verification
- No external tools or packages required

## Usage

Just ask Claude in natural language:

```
帮我写一篇关于 DMA framework 的文档
write a doc about the SCMI power protocol
分析一下 Linux 的 reset 子系统
```

The skill triggers automatically and follows the full workflow: explore source → explain architecture → write document → verify against source.

## Files

```
kernel-doc-writer/
├── SKILL.md                        # Main skill definition and workflow
└── references/
    ├── style-guide.md              # Complete writing style reference
    ├── doc-template.md             # Document skeleton templates
    ├── source-verifier.md          # Source verification agent prompt
    └── beginner-doc-review.md      # Beginner-friendly review agent prompt
```

## License

MIT — feel free to adapt for your own kernel subsystems and style.
