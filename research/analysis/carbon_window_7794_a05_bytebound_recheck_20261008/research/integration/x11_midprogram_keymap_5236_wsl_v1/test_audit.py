import sys
import json
import tempfile
import unittest
from pathlib import Path

from research.integration.x11_midprogram_keymap_5236_wsl_v1.audit_raw import audit


class AuditControls(unittest.TestCase):
    def test_missing_output_stops(self):
        self.assertEqual(audit(Path("/definitely/missing/5236"))["decision"],
                         "STOP_PROVENANCE_OR_RUNNER")

    def test_auditor_does_not_import_runner(self):
        self.assertNotIn("runner", sys.modules)

    def test_synthetic_completion_requires_correct_suffix_operation_index(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "summary.json").write_text(json.dumps({}), encoding="utf-8")
            self.assertEqual(audit(root)["decision"], "STOP_PROVENANCE_OR_RUNNER")

    def test_builds_auditor_without_importing_runner(self):
        from research.integration.x11_midprogram_keymap_5236_wsl_v1.audit_raw import BASE, CASES, SOURCES

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            rows = []
            for case_id, initial, target in CASES:
                case_dir = root / case_id
                case_dir.mkdir()
                effect = {"saved": True, "text": "http://a_b"}
                effect_bytes = (json.dumps(effect, sort_keys=True) + "\n").encode()
                (case_dir / "effect.json").write_bytes(effect_bytes)
                actor = {"scheduled": target is not None}
                waits = []
                if target:
                    actor.update({"returncode": 0, "final_layout": {"layout": target},
                                  "symbol_map": {"returncode": 0, "symbol_keycodes": {c: [1] for c in "_/:"}},
                                  "started_ns": 120, "ended_ns": 130})
                    waits = [{"requested_ms": 900, "completed": True,
                              "started_ns": 100, "ended_ns": 900}]
                row = {
                    "case_id": case_id, "initial_layout_requested": initial, "target_layout": target,
                    "initial_layout": {"layout": initial}, "final_layout": {"layout": target or initial},
                    "initial_symbol_map": {"returncode": 0, "symbol_keycodes": {c: [1] for c in "_/:"}},
                    "actor": actor, "waits": waits, "dispatch_started_ns": 90, "dispatch_ended_ns": 910,
                    "expected_text": "http://a_b", "wait_ms": 900, "effect_present": True,
                    "effect_sha256": __import__("hashlib").sha256(effect_bytes).hexdigest(),
                    "effect_bytes_utf8": effect_bytes.decode(), "app_exit": 0, "xvfb_exit": 0,
                    "socket_absent_after_cleanup": True, "program_emissions": 0,
                    "releases": [{"verified": True, "keys_down": [], "buttons_down": []}],
                    "dispatch": {"status": "completed", "execution": {"completed_ops": [6]}},
                }
                if target:
                    row["actor"].update({"scheduled": True, "started_ns": 120, "ended_ns": 130,
                                         "symbol_map": {"returncode": 0, "symbol_keycodes": {c: [1] for c in "_/:"}}})
                (case_dir / "case.json").write_text(json.dumps(row, sort_keys=True, indent=2) + "\n", encoding="utf-8")
                (case_dir / "processes.json").write_text(json.dumps({"app_exit": 0, "xvfb_exit": 0,
                    "socket_absent_after_cleanup": True}, sort_keys=True, indent=2) + "\n", encoding="utf-8")
                rows.append(row)
            (root / "summary.json").write_text(json.dumps({"allocation_id": "ISSUE5236-UBUNTU-WSL-20260928-01",
                "base": BASE, "sources": SOURCES, "cases": rows}, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            self.assertEqual(audit(root)["decision"], "NO_STALE_EFFECT_OBSERVED")


if __name__ == "__main__":
    unittest.main()
