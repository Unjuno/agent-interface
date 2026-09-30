#!/usr/bin/env python3
"""Synthetic fail-closed mutations for the independent formal auditor."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from audit_formal import IMAGE_ID, SCHEDULE, audit


class FormalAuditMutationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.snapshot = self.root / "source_snapshot"
        self.snapshot.mkdir()
        self.source = self.snapshot / "probe.py"
        self.source.write_text("frozen source\n", encoding="utf-8")
        source_hash = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.source_hashes = {"probe.py": source_hash}
        self.manifest = {
            "formal": True, "invocation_count": 1, "retry_count": 0, "replacement_count": 0,
            "image_id": IMAGE_ID, "expected_image_id": IMAGE_ID,
            "scheduled_sessions": SCHEDULE, "source_sha256": self.source_hashes,
        }
        self._write_json(self.root / "manifest.json", self.manifest)
        self.expected_manifest_hash = self._sha(self.root / "manifest.json")
        (self.root / "freeze.sha256").write_text(self.expected_manifest_hash + "\n", encoding="ascii")
        self._write_json(self.root / "environment.json", {
            "tk_runtime": {"returncode": 0}, "dpkg_packages": {"returncode": 0},
        })
        outcomes = []
        for index, allocation_id in enumerate(SCHEDULE, start=1):
            outcomes.append({"allocation_id": allocation_id, "returncode": 0})
            self._make_session(index, allocation_id)
        self._write_json(self.root / "orchestration.json", {
            "scheduled_sessions": SCHEDULE, "retry_count": 0, "replacement_count": 0,
            "outcomes": outcomes,
        })
        self.refresh_hashes()

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def _write_json(path: Path, value: object) -> None:
        path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")

    @staticmethod
    def _sha(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _make_session(self, index: int, allocation_id: str) -> None:
        directory = self.root / f"session-{index:02d}"
        snap = directory / "source_snapshot"
        snap.mkdir(parents=True)
        (snap / "probe.py").write_bytes(self.source.read_bytes())
        steps = []
        old_rows = []
        fresh_rows = []
        for phase, symbol, server_symbols in (
            ("us_baseline", "y", ["y", "Y"]),
            ("existing_after_de", "z", ["z", "Z"]),
            ("fresh_after_de", "z", ["z", "Z"]),
        ):
            window = index * 1000 + len(steps) + 1
            events = [
                {"phase": phase, "kind": "press", "keycode": 29, "keysym": symbol, "char": symbol},
                {"phase": phase, "kind": "release", "keycode": 29, "keysym": symbol, "char": ""},
            ]
            step = {
                "phase": phase, "server_map": {"keycode": 29, "keysyms": server_symbols},
                "window_id": window,
                "send": {"phase": phase, "target_window_id": window,
                         "request_sequence": [{"type": "KeyPress", "detail": 29},
                                              {"type": "KeyRelease", "detail": 29}],
                         "observer_states": {"after_press": True, "after_release": False},
                         "terminal_key_down": False},
                "events": events,
            }
            steps.append(step)
            (fresh_rows if phase == "fresh_after_de" else old_rows).extend(events)
        summary = {
            "formal": True, "allocation_id": allocation_id, "disposition": "FORMAL_SESSION_COMPLETE",
            "source_sha256": self.source_hashes, "steps": steps,
            "child_exit_codes": {"1": -15, "2": -15}, "xvfb_exit_code": 0,
        }
        self._write_json(directory / "summary.json", summary)
        (directory / "old.events.jsonl").write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in old_rows), encoding="utf-8")
        (directory / "fresh.events.jsonl").write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in fresh_rows), encoding="utf-8")
        for name in ("old.ready.jsonl", "fresh.ready.jsonl", "old.stdout.txt", "old.stderr.txt",
                     "fresh.stdout.txt", "fresh.stderr.txt", "xvfb.stderr.txt"):
            (directory / name).write_text("", encoding="utf-8")

    def refresh_hashes(self) -> None:
        hashes = {
            path.relative_to(self.root).as_posix(): self._sha(path)
            for path in sorted(self.root.rglob("*"))
            if path.is_file() and path.name != "evidence_sha256.json"
        }
        self._write_json(self.root / "evidence_sha256.json", hashes)

    def disposition(self) -> str:
        return audit(self.root, self.expected_manifest_hash)["disposition"]

    def test_accepts_complete_six_session_record(self) -> None:
        self.assertEqual("PASS_TK_XKB_REFRESH_SCOPED", self.disposition())

    def test_rejects_missing_session(self) -> None:
        (self.root / "session-06" / "summary.json").unlink()
        self.refresh_hashes()
        self.assertNotEqual("PASS_TK_XKB_REFRESH_SCOPED", self.disposition())

    def test_rejects_duplicate_allocation_id(self) -> None:
        path = self.root / "orchestration.json"
        value = json.loads(path.read_text())
        value["outcomes"][-1]["allocation_id"] = SCHEDULE[0]
        self._write_json(path, value)
        self.refresh_hashes()
        self.assertNotEqual("PASS_TK_XKB_REFRESH_SCOPED", self.disposition())

    def test_rejects_reordered_phase(self) -> None:
        path = self.root / "session-01" / "summary.json"
        value = json.loads(path.read_text())
        value["steps"][1], value["steps"][2] = value["steps"][2], value["steps"][1]
        self._write_json(path, value)
        self.refresh_hashes()
        self.assertNotEqual("PASS_TK_XKB_REFRESH_SCOPED", self.disposition())

    def test_rejects_wrong_keycode(self) -> None:
        path = self.root / "session-01" / "summary.json"
        value = json.loads(path.read_text())
        value["steps"][0]["events"][0]["keycode"] = 30
        self._write_json(path, value)
        self.refresh_hashes()
        self.assertNotEqual("PASS_TK_XKB_REFRESH_SCOPED", self.disposition())

    def test_rejects_missing_release(self) -> None:
        path = self.root / "session-01" / "summary.json"
        value = json.loads(path.read_text())
        value["steps"][0]["events"].pop()
        self._write_json(path, value)
        self.refresh_hashes()
        self.assertNotEqual("PASS_TK_XKB_REFRESH_SCOPED", self.disposition())

    def test_rejects_wrong_us_map(self) -> None:
        path = self.root / "session-02" / "summary.json"
        value = json.loads(path.read_text())
        value["steps"][0]["server_map"]["keysyms"] = ["z"]
        self._write_json(path, value)
        self.refresh_hashes()
        self.assertNotEqual("PASS_TK_XKB_REFRESH_SCOPED", self.disposition())

    def test_rejects_wrong_de_map(self) -> None:
        path = self.root / "session-02" / "summary.json"
        value = json.loads(path.read_text())
        value["steps"][1]["server_map"]["keysyms"] = ["y"]
        self._write_json(path, value)
        self.refresh_hashes()
        self.assertNotEqual("PASS_TK_XKB_REFRESH_SCOPED", self.disposition())

    def test_rejects_wrong_fresh_tk_symbol(self) -> None:
        path = self.root / "session-02" / "summary.json"
        value = json.loads(path.read_text())
        value["steps"][2]["events"][0]["keysym"] = "y"
        self._write_json(path, value)
        self.refresh_hashes()
        self.assertNotEqual("PASS_TK_XKB_REFRESH_SCOPED", self.disposition())

    def test_classifies_complete_stale_mapping_as_fail(self) -> None:
        path = self.root / "session-02" / "summary.json"
        value = json.loads(path.read_text())
        value["steps"][1]["events"][0]["keysym"] = "y"
        value["steps"][1]["events"][1]["keysym"] = "y"
        self._write_json(path, value)
        raw_path = self.root / "session-02" / "old.events.jsonl"
        raw_rows = [json.loads(line) for line in raw_path.read_text().splitlines()]
        for raw in raw_rows:
            if raw.get("phase") == "existing_after_de":
                raw["keysym"] = "y"
        raw_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in raw_rows), encoding="utf-8")
        self.refresh_hashes()
        self.assertEqual("FAIL_TK_STALE_MAPPING_EXPOSED", self.disposition())

    def test_rejects_window_target_mismatch(self) -> None:
        path = self.root / "session-03" / "summary.json"
        value = json.loads(path.read_text())
        value["steps"][1]["send"]["target_window_id"] += 1
        self._write_json(path, value)
        self.refresh_hashes()
        self.assertNotEqual("PASS_TK_XKB_REFRESH_SCOPED", self.disposition())

    def test_rejects_non_neutral_terminal_state(self) -> None:
        path = self.root / "session-03" / "summary.json"
        value = json.loads(path.read_text())
        value["steps"][0]["send"]["terminal_key_down"] = True
        self._write_json(path, value)
        self.refresh_hashes()
        self.assertNotEqual("PASS_TK_XKB_REFRESH_SCOPED", self.disposition())

    def test_rejects_raw_log_mismatch(self) -> None:
        path = self.root / "session-04" / "old.events.jsonl"
        path.write_text(path.read_text().replace('"keysym": "y"', '"keysym": "z"', 1), encoding="utf-8")
        self.refresh_hashes()
        self.assertNotEqual("PASS_TK_XKB_REFRESH_SCOPED", self.disposition())

    def test_rejects_unverified_process_exit(self) -> None:
        path = self.root / "session-05" / "summary.json"
        value = json.loads(path.read_text())
        value["child_exit_codes"]["1"] = None
        self._write_json(path, value)
        self.refresh_hashes()
        self.assertNotEqual("PASS_TK_XKB_REFRESH_SCOPED", self.disposition())

    def test_rejects_manifest_change_against_issue_pinned_hash(self) -> None:
        self.manifest["retry_count"] = 1
        self._write_json(self.root / "manifest.json", self.manifest)
        self.refresh_hashes()
        self.assertNotEqual("PASS_TK_XKB_REFRESH_SCOPED", self.disposition())


if __name__ == "__main__":
    unittest.main(verbosity=2)
