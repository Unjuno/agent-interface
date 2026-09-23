import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).parent


def row(control, pid, display, profile, window_pid, dispatch=False, effect=False):
    return {
        "control": control, "allocation": "a", "display": display,
        "profile": profile, "launch_epoch_ns": 1,
        "cdp_browser": {"pid": pid},
        "cdp_target": {"display": display, "profile": profile},
        "chromium_pid": pid, "xvfb_pid": 20,
        "x11_windows": [{"pid": window_pid, "display": display}], "dispatch": dispatch,
        "dom_effect": effect, "decision": "fixture",
    }


class AuditTest(unittest.TestCase):
    def run_audit(self, rows):
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl") as handle:
            handle.write("\n".join(json.dumps(item) for item in rows))
            handle.flush()
            return subprocess.run(
                [sys.executable, str(HERE / "audit.py"), handle.name],
                text=True, capture_output=True,
            )

    def test_three_controls_pass_only_with_correlated_positive(self):
        result = self.run_audit([
            row("stale_xid", 10, ":99", "p1", 11),
            row("old_process", 12, ":99", "p2", 11),
            row("positive_p2_effect", 12, ":100", "p2", 12, True, True),
        ])
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_positive_without_x11_correlation_is_rejected(self):
        result = self.run_audit([
            row("stale_xid", 10, ":99", "p1", 11),
            row("old_process", 12, ":99", "p2", 11),
            row("positive_p2_effect", 12, ":100", "p2", 11, True, True),
        ])
        self.assertNotEqual(result.returncode, 0)

    def test_same_numeric_xid_on_wrong_display_is_rejected(self):
        positive = row("positive_p2_effect", 12, ":100", "p2", 12, True, True)
        positive["x11_windows"] = [{"xid": "0x200003", "pid": 12, "display": ":99"}]
        result = self.run_audit([
            row("stale_xid", 10, ":99", "p1", 11),
            row("old_process", 12, ":99", "p2", 11), positive,
        ])
        self.assertNotEqual(result.returncode, 0)

    def test_missing_control_is_rejected(self):
        result = self.run_audit([
            row("stale_xid", 10, ":99", "p1", 11),
            row("old_process", 12, ":99", "p2", 11),
        ])
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
