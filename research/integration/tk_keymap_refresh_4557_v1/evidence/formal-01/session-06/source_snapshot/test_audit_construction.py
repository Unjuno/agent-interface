#!/usr/bin/env python3
"""Synthetic mutation checks; never experimental rows."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from audit_construction import audit


class ConstructionAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.evidence = self.root / "construction"
        self.evidence.mkdir()
        snapshot = self.evidence / "source_snapshot"
        snapshot.mkdir()
        self.source = snapshot / "probe.py"
        self.source.write_text("immutable source fixture\n", encoding="utf-8")
        (self.evidence / "xvfb.stderr.txt").write_text("", encoding="utf-8")
        for name in ("old.events.jsonl", "fresh.events.jsonl", "old.stdout.txt", "old.stderr.txt",
                     "fresh.stdout.txt", "fresh.stderr.txt"):
            (self.evidence / name).write_text("", encoding="utf-8")
        self.summary = {
            "formal": False,
            "disposition": "CONSTRUCTION_MECHANICS_ONLY",
            "source_sha256": {"probe.py": __import__("hashlib").sha256(self.source.read_bytes()).hexdigest()},
            "child_exit_codes": {"101": -15, "102": -15},
            "xvfb_exit_code": 0,
            "steps": [],
        }
        for phase, symbol, server_symbols in (
            ("us_baseline", "y", ["y", "Y"]),
            ("existing_after_de", "y", ["z", "Z"]),
            ("fresh_after_de", "z", ["z", "Z"]),
        ):
            window = len(self.summary["steps"]) + 100
            self.summary["steps"].append({
                "phase": phase,
                "server_map": {"keycode": 29, "keysyms": server_symbols},
                "window_id": window,
                "send": {"phase": phase, "target_window_id": window,
                         "request_sequence": [{"type": "KeyPress", "detail": 29},
                                              {"type": "KeyRelease", "detail": 29}],
                         "observer_states": {"after_press": True, "after_release": False},
                         "terminal_key_down": False},
                "events": [
                    {"phase": phase, "kind": "press", "keycode": 29, "keysym": symbol},
                    {"phase": phase, "kind": "release", "keycode": 29, "keysym": symbol},
                ],
            })
            filename = "fresh.events.jsonl" if phase == "fresh_after_de" else "old.events.jsonl"
            with (self.evidence / filename).open("a", encoding="utf-8") as stream:
                for event in self.summary["steps"][-1]["events"]:
                    stream.write(json.dumps(event) + "\n")
        self.path = self.evidence / "summary.json"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def check(self) -> list[str]:
        self.path.write_text(json.dumps(self.summary), encoding="utf-8")
        return audit(self.path)

    def test_accepts_complete_synthetic_shape(self) -> None:
        self.assertEqual([], self.check())

    def test_rejects_formal_relabel(self) -> None:
        self.summary["formal"] = True
        self.assertTrue(self.check())

    def test_rejects_duplicate_or_missing_phase(self) -> None:
        self.summary["steps"].pop()
        self.assertTrue(self.check())

    def test_rejects_wrong_keycode(self) -> None:
        self.summary["steps"][0]["events"][0]["keycode"] = 30
        self.assertTrue(self.check())

    def test_rejects_unbalanced_pair(self) -> None:
        self.summary["steps"][1]["events"].pop()
        self.assertTrue(self.check())

    def test_rejects_wrong_de_server_map(self) -> None:
        self.summary["steps"][2]["server_map"]["keysyms"] = ["y"]
        self.assertTrue(self.check())

    def test_rejects_wrong_fresh_tk_keysym(self) -> None:
        self.summary["steps"][2]["events"][0]["keysym"] = "y"
        self.assertTrue(self.check())

    def test_rejects_event_from_wrong_phase(self) -> None:
        self.summary["steps"][0]["events"][1]["phase"] = "fresh_after_de"
        self.assertTrue(self.check())

    def test_rejects_unverified_terminal_state(self) -> None:
        self.summary["steps"][0]["send"]["terminal_key_down"] = True
        self.assertTrue(self.check())

    def test_rejects_tampered_source(self) -> None:
        self.source.write_text("tampered\n", encoding="utf-8")
        self.assertTrue(self.check())

    def test_rejects_wrong_input_target(self) -> None:
        self.summary["steps"][0]["send"]["target_window_id"] += 1
        self.assertTrue(self.check())

    def test_rejects_unverified_child_exit(self) -> None:
        self.summary["child_exit_codes"]["101"] = None
        self.assertTrue(self.check())


if __name__ == "__main__":
    unittest.main(verbosity=2)
