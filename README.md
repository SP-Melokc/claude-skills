# Claude Skills

My [Claude Code](https://claude.ai/code) skills collection.

## Skills

- **annotate-struct** — Analyze and annotate C struct members with comments. Outputs annotated struct to terminal with key members emphasized. Triggered when asked to analyze/organize/explain struct definitions.
- **function-trace-png** — Trace a function's call chain (esp. Linux kernel), annotate every check/decision with *why* it exists, and render the annotated call graph to a **PNG** image. Builds on `function-trace-diagram`'s coloring/method; outputs an overview plus one detailed diagram per branch.
- **statusline-setup** — Compact two-row statusline for Claude Code showing AI runtime state (model, context%, tokens, cache, thinking mode) and workspace context (CWD, git branch, PR status). Includes full install guide and troubleshooting.
