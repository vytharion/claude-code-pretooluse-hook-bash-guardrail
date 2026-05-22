"""PreToolUse Bash guardrail — lesson 1.

Reads the PreToolUse payload from stdin, logs the candidate command,
and exits with an `allow` decision. Future lessons add pattern matching
and a real deny path; this lesson just proves the hook is wired.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any


LOG_PATH = os.environ.get("GUARDRAIL_LOG", "/tmp/bash_guardrail.log")


def log(line: str) -> None:
    with open(LOG_PATH, "a", encoding="utf-8") as handle:
        handle.write(line.rstrip() + "\n")


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        sys.stdout.write(json.dumps({"continue": True}))
        return 0

    payload: dict[str, Any] = json.loads(raw)
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    command = tool_input.get("command", "")

    log(f"tool={tool_name} command={command!r}")

    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "guardrail: no rules registered yet",
        }
    }
    sys.stdout.write(json.dumps(response))
    return 0


if __name__ == "__main__":
    sys.exit(main())
