"""Subprocess test harness for the PreToolUse Bash guardrail.

Drives `hooks/bash_guardrail.py` exactly the way Claude Code does:
pipe a JSON payload to stdin, parse the JSON response on stdout, assert
the `permissionDecision`. Uses stdlib unittest so `python3 -m unittest`
runs it with zero install.

Run from the repo root:

    python3 -m unittest tests.test_guardrail -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = REPO_ROOT / "hooks" / "bash_guardrail.py"


def invoke(command: str) -> dict[str, Any]:
    payload = {"tool_name": "Bash", "tool_input": {"command": command}}
    with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False) as tmp:
        log_path = tmp.name
    env = {**os.environ, "GUARDRAIL_LOG": log_path}
    proc = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=True,
        timeout=5,
    )
    return json.loads(proc.stdout)


class TestGuardrail(unittest.TestCase):
    def assert_decision(self, command: str, expected: str) -> dict[str, Any]:
        response = invoke(command)
        hook_output = response["hookSpecificOutput"]
        self.assertIsInstance(hook_output, dict)
        decision = hook_output["permissionDecision"]
        self.assertEqual(decision, expected, msg=f"command={command!r} response={response}")
        return hook_output

    def test_safe_command_allowed(self) -> None:
        self.assert_decision("ls -la", "allow")

    def test_rm_rf_root_denied(self) -> None:
        out = self.assert_decision("rm -rf /", "deny")
        self.assertIn("rm-rf-root-or-home", str(out["permissionDecisionReason"]))

    def test_rm_rf_home_denied(self) -> None:
        self.assert_decision("rm -rf ~/.config", "deny")

    def test_rm_rf_scoped_tmp_allowed(self) -> None:
        out = self.assert_decision("rm -rf /tmp/build-xyz-123", "allow")
        self.assertIn("allow", str(out["permissionDecisionReason"]))

    def test_force_push_denied(self) -> None:
        self.assert_decision("git push origin main --force", "deny")

    def test_force_with_lease_allowed(self) -> None:
        self.assert_decision("git push origin feature/foo --force-with-lease", "allow")

    def test_sql_drop_denied(self) -> None:
        out = self.assert_decision("psql -c 'DROP TABLE users'", "deny")
        self.assertIn("sql-drop-or-truncate", str(out["permissionDecisionReason"]))

    def test_sql_drop_with_explicit_override_allowed(self) -> None:
        # Operator must opt-in by appending --guardrail-allow=migration
        self.assert_decision(
            "psql -c 'DROP TABLE tmp_import' --guardrail-allow=migration",
            "allow",
        )

    def test_dd_to_disk_denied(self) -> None:
        self.assert_decision("dd if=/dev/zero of=/dev/sda bs=1M", "deny")

    def test_dd_to_image_file_allowed(self) -> None:
        self.assert_decision("dd if=disk.img of=/tmp/copy.img bs=1M", "allow")


if __name__ == "__main__":
    unittest.main()
