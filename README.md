# claude-code-pretooluse-hook-bash-guardrail

A Claude Code `PreToolUse` hook that blocks destructive Bash commands at
the source — `rm -rf` on system paths, `git push --force` to protected
branches, `DROP TABLE` against production DSNs — and returns a structured
`permissionDecision: deny` so the agent can retry with a safer command
instead of crashing opaquely.

Full walkthrough: <https://claudeplugins.nicedx.com/claude-code-pretooluse-hook-bash-guardrail/>

## Layout

```
.claude/
  settings.json        # registers the hook
hooks/
  bash_guardrail.py    # the hook itself (Python 3.11+, stdlib only)
tests/
  test_guardrail.py    # pytest harness simulating Claude Code's stdin/stdout
```

## Try it

Clone, then point a Claude Code session at this directory:

```bash
git clone https://github.com/vytharion/claude-code-pretooluse-hook-bash-guardrail.git
cd claude-code-pretooluse-hook-bash-guardrail
claude --settings .claude/settings.json
```

Ask the agent to run `rm -rf /`. The hook returns `deny` with a reason;
the agent should propose a scoped alternative.
