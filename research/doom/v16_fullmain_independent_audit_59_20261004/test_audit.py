import json
import shutil
import tempfile
import unittest
from pathlib import Path

from audit import ONE_HOLD, SOURCE, audit
from adapter_replay import run as adapter_replay


REPO = Path(__file__).resolve().parents[3]


def copy_sources(root: Path) -> Path:
    copy = root / "repo"
    shutil.copytree(REPO / SOURCE, copy / SOURCE)
    shutil.copytree(REPO / ONE_HOLD, copy / ONE_HOLD)
    return copy


class V16FullmainAuditTests(unittest.TestCase):
    def test_retained_record_passes_scoped_audit(self):
        result = audit(REPO)
        self.assertEqual(result["audit"], "PASS_SCOPED_V16_LIFECYCLE")
        self.assertEqual(result["construction02"]["scorer_samples"], 2)
        self.assertEqual(result["construction02"]["positive_useful_events"], 0)
        self.assertTrue(result["construction02"]["post_score_precedes_close_release"])
        self.assertTrue(result["one_hold"]["identity_join_verified"])
        self.assertFalse(result["one_hold"]["physical_release_authoritative"])
        self.assertFalse(result["one_hold"]["physical_edge_measurement_present"])

    def test_actual_one_hold_rows_join_pinned_v15_adapter(self):
        result = adapter_replay(REPO)
        self.assertEqual(result["trace_integrity"], "SOURCE_ROWS_JOINED")
        self.assertEqual(result["counts"]["input_admissions"], 1)
        self.assertEqual(result["counts"]["key_release_receipts"], 1)
        self.assertEqual(result["counts"]["scorer_samples"], 17)
        self.assertEqual(result["counts"]["scorer_events"], 0)
        self.assertEqual(result["attributions"], [])
        self.assertFalse(result["release_identity"]["physical_verification_authoritative"])

    def test_nonempty_close_release_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = copy_sources(Path(tmp))
            path = copy / SOURCE / "construction02/out/session/owner-events.json"
            owner = json.loads(path.read_text(encoding="utf-8"))
            owner[0]["keys_down"] = ["left"]
            path.write_text(json.dumps(owner), encoding="utf-8")
            result = audit(copy)
        self.assertIn("construction02_owner_release_not_verified_empty", result["errors"])

    def test_positive_event_claim_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = copy_sources(Path(tmp))
            path = copy / SOURCE / "construction02/out/session/scorer-summary.json"
            summary = json.loads(path.read_text(encoding="utf-8"))
            summary["event_count"] = 1
            path.write_text(json.dumps(summary), encoding="utf-8")
            result = audit(copy)
        self.assertIn("construction02_useful_event_summary_mismatch", result["errors"])

    def test_owner_sync_is_not_promoted_to_physical_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = copy_sources(Path(tmp))
            path = copy / ONE_HOLD / "out/session/owner-events.json"
            owner = json.loads(path.read_text(encoding="utf-8"))
            owner[0]["physical_verification_authoritative"] = True
            path.write_text(json.dumps(owner), encoding="utf-8")
            result = audit(copy)
        self.assertIn("one_hold_keyup_authority_fields_mismatch", result["errors"])

    def test_mismatched_shared_release_identity_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = copy_sources(Path(tmp))
            path = copy / ONE_HOLD / "out/session/events.jsonl"
            events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
            row = next(item for item in events if item.get("event") == "input_release_transition")
            row["intent_token"] = "mismatched-token"
            path.write_text("\n".join(json.dumps(item) for item in events) + "\n", encoding="utf-8")
            result = audit(copy)
        self.assertIn("one_hold_identity_join_mismatch", result["errors"])


if __name__ == "__main__":
    unittest.main()
