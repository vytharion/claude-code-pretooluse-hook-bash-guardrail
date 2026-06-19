# claude-code-pretooluse-hook-bash-guardrail

Companion repository for the article at https://claudeplugins.nicedx.com/claude-code-pretooluse-hook-bash-guardrail/.

A Claude Code `PreToolUse` hook that blocks destructive Bash commands at the source — `rm -rf` on root or home, blanket `git push --force`, `DROP TABLE` against production — and returns a structured `permissionDecision: deny` so the agent retries with a safer command instead of crashing opaquely. Per-rule allowlists make the guardrail usable in real work (scoped `/tmp` deletes pass, `--force-with-lease` passes, opt-in migration overrides pass) so the agent does not learn to dodge the regex.

## What this project demonstrates

1. **Wiring `PreToolUse` via `.claude/settings.json`** — registers a `matcher: "Bash"` entry pointing at a stdlib Python script, so any Bash tool call routes through the guardrail before the shell sees it.
2. **A pattern catalog as data, not branches** — five `Rule` dataclasses (`rm-rf-root-or-home`, `git-force-push`, `sql-drop-or-truncate`, `dd-of-device`, `chmod-recursive-root`) drive a single dispatch loop; adding a sixth rule never touches control flow.
3. **Returning `hookSpecificOutput.permissionDecision: deny` with a reason** — the agent receives a structured reason it can read back and rewrite the command around, instead of seeing a non-zero exit code with no explanation.
4. **Per-rule `safe_if_matches` allowlists** — `rm -rf /tmp/build-xyz` and `git push --force-with-lease` downgrade to `allow` with an audit-trail reason, so the rule stays useful instead of being disabled outright.
5. **A subprocess test harness** — `tests/test_guardrail.py` drives the hook over real stdin/stdout the way Claude Code does, asserts the decision JSON, and catches a regex word-boundary bug introduced mid-refactor.

## Tech stack

- Python 3.11+ (stdlib only — `json`, `re`, `dataclasses`, `subprocess`, `unittest`)
- Claude Code 1.0+ with `PreToolUse` hook support
- No external dependencies; nothing to `pip install`

## Prerequisites

- Python 3.11 or newer (`python3 --version` should print `3.11.x` or higher)
- Claude Code CLI installed and authenticated — install instructions at https://docs.claude.com/en/docs/claude-code/quickstart
- A POSIX shell (the hook itself is OS-agnostic, but the example `rm -rf` commands assume `/tmp` exists)

## Quick start

```bash
git clone https://github.com/vytharion/claude-code-pretooluse-hook-bash-guardrail.git
cd claude-code-pretooluse-hook-bash-guardrail
python3 -m unittest tests.test_guardrail -v
```

Expected output: `Ran 10 tests in ~1s` with `OK`. Then point Claude Code at the directory:

```bash
claude --settings .claude/settings.json
```

Ask the agent to run `rm -rf /`. The hook returns `deny` with a reason; the agent should propose a scoped alternative such as `rm -rf /tmp/build-xyz`.

## Commit walkthrough

Step through the lessons chronologically. Each commit leaves the tree in a runnable state — `python3 -m unittest tests.test_guardrail -v` works at every commit.

| Step | Commit | Description |
|---|---|---|
| 0 | [`2887cac`](https://github.com/vytharion/claude-code-pretooluse-hook-bash-guardrail/commit/2887cac) | init: project scaffold (`.gitignore`, README, empty `hooks/` + `tests/` dirs) |
| 1 | [`0feb005`](https://github.com/vytharion/claude-code-pretooluse-hook-bash-guardrail/commit/0feb005) | wire `PreToolUse` hook scaffold + `.claude/settings.json` registration |
| 2 | [`919b644`](https://github.com/vytharion/claude-code-pretooluse-hook-bash-guardrail/commit/919b644) | add dangerous-command pattern catalog (detect-only, no deny yet) |
| 3 | [`1da231c`](https://github.com/vytharion/claude-code-pretooluse-hook-bash-guardrail/commit/1da231c) | return `permissionDecision: deny` with structured reason |
| 4 | [`623a500`](https://github.com/vytharion/claude-code-pretooluse-hook-bash-guardrail/commit/623a500) | per-rule allowlist for scoped temp dirs + `--force-with-lease` |
| 5 | [`776f25c`](https://github.com/vytharion/claude-code-pretooluse-hook-bash-guardrail/commit/776f25c) | test harness catches and fixes regex word-boundary bug |

To replay a specific step:

```bash
git checkout 623a500
python3 -m unittest tests.test_guardrail -v
```

## Repo layout

```
.claude/
  settings.json        — registers the PreToolUse hook with matcher "Bash"
hooks/
  bash_guardrail.py    — the hook (rules, allowlist, decision dispatch, JSON I/O)
tests/
  test_guardrail.py    — unittest harness driving the hook via subprocess stdin/stdout
```

## License

MIT.
