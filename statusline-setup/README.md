# Statusline Setup for Claude Code

A compact, information-dense statusline for Claude Code that shows AI runtime state and workspace context at a glance.

## Preview

**Wide terminal (>= 100 cols):**
```
[DSv4-Pro] | ctx:72% | tok:12.3k->1.2k | cache:4.5k-2.1k | think:H  |  /home/user/project  |  user/repo main
```

**Narrow terminal (< 100 cols):**
```
[DSv4-Pro] | ctx:72% | tok:12.3k->1.2k | think:H
/home/user/project | user/repo main
```

## Information Layout

### Row 1 — AI Runtime State

| Block  | Content               | Notes                              |
|--------|-----------------------|-------------------------------------|
| Model  | `[DSv4-Pro]`          | Auto-abbreviated from model name   |
| Context| `ctx:72%`             | 4-tier color: green -> yellow -> orange -> red |
| Tokens | `tok:12.3k->1.2k`     | Input -> output                    |
| Cache  | `cache:4.5k-2.1k`     | Read / write cache hits (shown when non-zero) |
| Think  | `think:H`             | Thinking mode + effort level (L/M/H/XH/MAX) |
| Agent  | `@agent-name`         | Active sub-agent (shown when active) |

### Row 2 — Workspace Context

| Block | Content              | Notes                    |
|-------|----------------------|--------------------------|
| CWD   | Full working dir path| Low-saturation blue      |
| Git   | `owner/repo branch`  | Low-saturation purple    |
| PR    | `PR#42-ok`           | Includes review status   |

### Color System

All colors use ANSI 256 low-saturation range (73-179). Labels are dark gray (243), separators are faint gray (239). The only dynamic color is the context percentage, using a 4-tier gradient.

## Installation

### 1. Install Dependencies

The statusline command requires `jq` for JSON parsing.

**Windows (winget):**
```bash
winget install --id=jqlang.jq
```

**Windows (chocolatey):**
```bash
choco install jq
```

**macOS (Homebrew):**
```bash
brew install jq
```

**Linux (apt):**
```bash
sudo apt install jq
```

After installation, verify:
```bash
jq --version  # should print jq-1.8.x or similar
```

### 2. Configure settings.json

Add the `statusLine` block to `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "input=$(cat);model=$(echo \"$input\"|jq -r '.model.display_name//.model.id//\"?\"');case \"$model\" in *Pro*)model=\"DSv4-Pro\";;*Flash*)model=\"DSv4-Flash\";;*V3*)model=\"DSv3\";;*R1*)model=\"DS-R1\";;*Opus*)model=\"Opus\";;*Sonnet*)model=\"Sonnet\";;*Haiku*)model=\"Haiku\";;esac;pct=$(echo \"$input\"|jq -r '.context_window.used_percentage//empty');ti=$(echo \"$input\"|jq -r '.context_window.total_input_tokens//0');to=$(echo \"$input\"|jq -r '.context_window.total_output_tokens//0');cr=$(echo \"$input\"|jq -r '.context_window.current_usage.cache_read_input_tokens//0');cw=$(echo \"$input\"|jq -r '.context_window.current_usage.cache_creation_input_tokens//0');think=$(echo \"$input\"|jq -r '.thinking.enabled//false');ef=$(echo \"$input\"|jq -r '.effort.level//empty');cwd=$(echo \"$input\"|jq -r '.workspace.current_dir//.cwd//\"\"');repo=$(echo \"$input\"|jq -r '.workspace.repo|if . then .owner+\"/\"+.name else empty end');br=\"\";if [ -n \"$cwd\" ]&&[ -d \"$cwd/.git\" ];then br=$(GIT_OPTIONAL_LOCKS=0 git -C \"$cwd\" branch --show-current 2>/dev/null);fi;pr=$(echo \"$input\"|jq -r '.pr.number//empty');prs=$(echo \"$input\"|jq -r '.pr.review_state//empty');vm=$(echo \"$input\"|jq -r '.vim.mode//empty');ag=$(echo \"$input\"|jq -r '.agent.name//empty');fmt(){ n=${1%.*};if [ $n -ge 1000000 ];then awk 'BEGIN{printf\"%.1fM\",'$n'/1000000}';elif [ $n -ge 1000 ];then awk 'BEGIN{printf\"%.1fk\",'$n'/1000}';else echo $n;fi;};cc(){ echo $1|awk '{if($1>=90)print\"167\";else if($1>=75)print\"173\";else if($1>=50)print\"143\";else print\"108\"}';};R='\\033[0m';S='\\033[38;5;239m';L='\\033[38;5;';o1=\"${L}109m[$model]$R\";if [ -n \"$pct\" ];then gc=$(cc \"$pct\");o1=\"$o1 ${S}|$R ${L}243mctx:$R${L}${gc}m${pct}%$R\";fi;if [ -n \"$ti\" ]&&[ \"$ti\"!=\"0\" ]&&[ \"$ti\"!=\"null\" ];then o1=\"$o1 ${S}|$R ${L}243mtok:$R${L}250m$(fmt \"$ti\")$R${L}243m->$R${L}250m$(fmt \"$to\")$R\";fi;if [ -n \"$cr\" ]&&[ -n \"$cw\" ];then if [ \"$cr\"!=\"0\" ]||[ \"$cw\"!=\"0\" ];then o1=\"$o1 ${S}|$R ${L}243mcache:$R${L}73m$(fmt \"$cr\")-$(fmt \"$cw\")$R\";fi;fi;if [ \"$think\" = \"true\" ];then es=\"\";case \"$ef\" in low)es=\"L\";;medium)es=\"M\";;high)es=\"H\";;xhigh)es=\"XH\";;max)es=\"MAX\";;esac;if [ -n \"$es\" ];then o1=\"$o1 ${S}|$R ${L}179mthink:$es$R\";else o1=\"$o1 ${S}|$R ${L}179mthink$R\";fi;fi;if [ -n \"$ag\" ];then o1=\"$o1 ${S}|$R ${L}110m@${ag}$R\";fi;o2=\"${L}110m${cwd:-?}$R\";if [ -n \"$repo\" ];then o2=\"$o2 ${S}|$R ${L}139m$repo$R\";fi;if [ -n \"$br\" ];then o2=\"$o2 ${L}139m$br$R\";fi;if [ -n \"$pr\" ];then pl=\"PR#$pr\";case \"$prs\" in approved)pl=\"$pl-ok\";;changes_requested)pl=\"$pl-D\";;pending)pl=\"$pl....\";;draft)pl=\"$pl-draft\";;esac;o2=\"$o2 ${S}|$R ${L}108m$pl$R\";fi;if [ -n \"$vm\" ];then o2=\"$o2 ${S}|$R ${L}173mV:$vm$R\";fi;cols=$(tput cols 2>/dev/null||echo 80);if [ \"$cols\" -ge 100 ];then printf \"%b  ${S}||$R  %b\" \"$o1\" \"$o2\";else printf \"%b\\n%b\" \"$o1\" \"$o2\";fi"
  }
}
```

### 3. Restart Claude Code

Close and reopen your Claude Code terminal. The statusline should appear at the bottom of the interface.

## Troubleshooting

### Statusline shows nothing (blank)

**Root cause:** `jq` is not installed or not on `PATH`.

Check with `which jq`. If not found:

1. Install `jq` via your package manager (see above)
2. Ensure the `jq` binary is in a directory on your shell's `PATH`
3. For Windows: winget installs to `%LOCALAPPDATA%/Microsoft/WinGet/Packages/jqlang.jq_.../jq.exe` -- you may need to copy it to `~/bin/` or add the directory to `PATH`

### Statusline shows `[]` for model name

The model name abbreviation logic uses simple substring matching. If you're using a model not covered by the `case` statement, add your model prefix to the pattern:

```bash
case "$model" in
  *Pro*)   model="DSv4-Pro";;
  *Flash*) model="DSv4-Flash";;
  *V3*)    model="DSv3";;
  *R1*)    model="DS-R1";;
  ...
esac
```

### ANSI colors not rendering

Make sure your terminal supports ANSI 256-color escape sequences. Windows Terminal, iTerm2, and most modern terminal emulators support this. The legacy Windows Console (`cmd.exe`) may not.

## License

MIT

---

Author: [SP-Melokc](https://github.com/SP-Melokc)
