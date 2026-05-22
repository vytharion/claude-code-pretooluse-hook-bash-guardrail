"""PreToolUse Bash guardrail — lesson 3.

Switches from detect-only to active deny. When a rule matches, return
`permissionDecision: "deny"` with `permissionDecisionReason` set to a
crisp explanation. Claude Code surfaces the reason to the agent so the
next turn can propose a safer command instead of dying opaquely.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Any


LOG_PATH = os.environ.get("GUARDRAIL_LOG", "/tmp/bash_guardrail.log")


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern[str]
    reason: str


BLOCK_RULES: tuple[Rule, ...] = (
    Rule(
        name="rm-rf-root-or-home",
        pattern=re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-rf|-fr)\b.*(/|~|\$HOME)\b"),
        reason="rm -rf against root, home, or absolute paths is irreversible; restrict to a scoped temp dir",
    ),
    Rule(
        name="git-force-push",
        pattern=re.compile(r"\bgit\s+push\b.*(--force|-f\b|\+)"),
        reason="force-push rewrites remote history; use --force-with-lease and target a feature branch",
    ),
    Rule(
        name="sql-drop-or-truncate",
        pattern=re.compile(r"\b(DROP\s+(TABLE|DATABASE|SCHEMA)|TRUNCATE\s+TABLE)\b", re.IGNORECASE),
        reason="DROP/TRUNCATE in a one-shot Bash command bypasses migration review; write a migration file",
    ),
    Rule(
        name="dd-of-device",
        pattern=re.compile(r"\bdd\b.*\bof=/dev/(sd|nvme|disk)"),
        reason="dd to a block device wipes the disk; target a named image file instead",
    ),
    Rule(
        name="chmod-recursive-root",
        pattern=re.compile(r"\bchmod\s+-R\s+[0-7]{3,4}\s+/(?!tmp/|var/tmp/)"),
        reason="recursive chmod outside /tmp wrecks system permissions; scope the path",
    ),
)


def log(line: str) -> None:
    with open(LOG_PATH, "a", encoding="utf-8") as handle:
        handle.write(line.rstrip() + "\n")


def first_match(command: str) -> Rule | None:
    for rule in BLOCK_RULES:
        if rule.pattern.search(command):
            return rule
    return None


def decide(command: str) -> dict[str, str]:
    matched = first_match(command)
    if matched is None:
        return {
            "permissionDecision": "allow",
            "permissionDecisionReason": "guardrail: no rule matched",
            "_rule": "none",
        }
    return {
        "permissionDecision": "deny",
        "permissionDecisionReason": f"[guardrail:{matched.name}] {matched.reason}",
        "_rule": matched.name,
    }


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        sys.stdout.write(json.dumps({"continue": True}))
        return 0

    payload: dict[str, Any] = json.loads(raw)
    tool_name = payload.get("tool_name", "")
    command = payload.get("tool_input", {}).get("command", "")

    verdict = decide(command)
    log(
        f"decision={verdict['permissionDecision']} rule={verdict['_rule']} "
        f"tool={tool_name} command={command!r}"
    )

    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": verdict["permissionDecision"],
            "permissionDecisionReason": verdict["permissionDecisionReason"],
        }
    }
    sys.stdout.write(json.dumps(response))
    return 0


if __name__ == "__main__":
    sys.exit(main())
