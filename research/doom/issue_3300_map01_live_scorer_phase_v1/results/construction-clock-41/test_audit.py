from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("entry_audit", Path(__file__).with_name("audit.py"))
entry_audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(entry_audit)


class EntryAuditTest(unittest.TestCase):
    def test_selects_immediately_preceding_entry(self):
        rows = [{
            "repetition": 0, "setup": "initialized", "mode": "Mode.ASYNC_SPECTATOR",
            "ticrate": 35, "wad_sha256": "a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b",
            "scorer_status": "returned", "closed": True, "advancing_api_calls": 0,
            "initial_api_tic": 1, "final_api_tic": 1,
            "tic_entries": [
                {"pid": 2, "monotonic_ns": 100 * n, "gametic": n, "viz_time": n}
                for n in range(1, 11)
            ],
            "scorer_api_trace": [{"name": "get_episode_time", "start_ns": 250, "end_ns": 260}] * 8,
        }]
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "raw.json"
            raw.write_text(json.dumps(rows))
            result = entry_audit.audit(raw)
        self.assertEqual(result["decision"], "PASS_CONSTRUCTION_ONLY_ENTRY_CLOCK_CORRELATION")
        self.assertEqual(result["rows"][0]["scorer_getters"][0]["preceding_viz_time"], 2)
        self.assertEqual(result["rows"][0]["scorer_getters"][0]["following_viz_time"], 3)

    def test_unbracketed_getter_is_rejected(self):
        rows = [{
            "repetition": 0, "setup": "initialized", "mode": "Mode.ASYNC_SPECTATOR",
            "ticrate": 35, "wad_sha256": "a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b",
            "scorer_status": "returned", "closed": True, "advancing_api_calls": 0,
            "initial_api_tic": 1, "final_api_tic": 1,
            "tic_entries": [{"pid": 2, "monotonic_ns": 100, "gametic": 1, "viz_time": 1}],
            "scorer_api_trace": [{"name": "get_episode_time", "start_ns": 250, "end_ns": 260}] * 8,
        }]
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "raw.json"
            raw.write_text(json.dumps(rows))
            result = entry_audit.audit(raw)
        self.assertEqual(result["decision"], "FAIL_AUDIT")
        self.assertEqual(len(result["errors"]), 9)


if __name__ == "__main__":
    unittest.main()
