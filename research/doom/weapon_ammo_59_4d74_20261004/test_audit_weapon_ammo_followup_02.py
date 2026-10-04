import json
import tempfile
import unittest
from pathlib import Path

from audit_weapon_ammo_followup_02 import audit


PACKAGE = Path(__file__).resolve().parent
CELL = PACKAGE / "00-coast"


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def write_jsonl(path: Path, values: list[object]) -> None:
    path.write_text("".join(json.dumps(value) + "\n" for value in values), encoding="utf-8")


def compact_fixture(destination: Path) -> Path:
    cell = destination / "00-coast"
    cell.mkdir(parents=True)
    for name in ("RESULT.json", "FINAL.json"):
        write_json(cell / name, json.loads((CELL / name).read_text(encoding="utf-8")))
    for name in ("events.jsonl", "scorer-last-action.jsonl"):
        rows = [json.loads(line) for line in (CELL / name).read_text(encoding="utf-8").splitlines()]
        write_jsonl(cell / name, rows)
    return destination


class WeaponAmmoAuditFollowupTests(unittest.TestCase):
    def test_committed_layout_audits_without_saved_audit(self) -> None:
        report = audit(PACKAGE)
        self.assertEqual(report["disposition"], "PASS_HUD_WEAPON_AMMO_BINDING_SCOPED")
        self.assertEqual(report["sample_count"], 90)
        self.assertTrue(all(report["checks"].values()))

    def test_unobserved_hud_signal_cannot_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = compact_fixture(Path(temporary))
            path = root / "00-coast" / "events.jsonl"
            events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            initial = next(event for event in events if event.get("id") == "initial")
            initial["signals"]["ammo"].update(
                status="unobserved",
                format="invalid",
                sequence=999,
                binding={"focus": -1, "surface": -1, "geometry": [1, 1, 1, 1]},
            )
            write_jsonl(path, events)
            report = audit(root)
            self.assertEqual(report["disposition"], "HOLD_AUDIT_CHECK_FAILED")
            self.assertFalse(report["checks"]["HUD_signals_validly_bound_to_initial_capture"])

    def test_wrong_signal_capture_time_cannot_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = compact_fixture(Path(temporary))
            path = root / "00-coast" / "events.jsonl"
            events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            initial = next(event for event in events if event.get("id") == "initial")
            initial["signals"]["health"]["capture_ns"] += 1
            write_jsonl(path, events)
            report = audit(root)
            self.assertEqual(report["disposition"], "HOLD_AUDIT_CHECK_FAILED")
            self.assertFalse(report["checks"]["HUD_signals_validly_bound_to_initial_capture"])

    def test_typed_capture_must_match_published_observation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = compact_fixture(Path(temporary))
            path = root / "00-coast" / "events.jsonl"
            events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            initial = next(event for event in events if event.get("event") == "typed_observation")
            initial["capture_ns"] += 1_000_000_000_000
            for signal in initial["signals"].values():
                signal["capture_ns"] = initial["capture_ns"]
            initial["frame_rgb_sha256"] = "0" * 64
            write_jsonl(path, events)
            report = audit(root)
            self.assertEqual(report["disposition"], "HOLD_AUDIT_CHECK_FAILED")
            self.assertFalse(report["checks"]["typed_capture_matches_observation_event"])

    def test_nearest_api_row_must_be_neutral(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = compact_fixture(Path(temporary))
            path = root / "00-coast" / "scorer-last-action.jsonl"
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            events = [json.loads(line) for line in (root / "00-coast" / "events.jsonl").read_text(encoding="utf-8").splitlines()]
            initial = next(event for event in events if event.get("event") == "typed_observation")
            nearest = min(
                (row for row in rows if row["coherent_tic"]),
                key=lambda row: abs(row["sample_returned_ns"] - initial["capture_ns"]),
            )
            nearest["action"][0] = 1.0
            write_jsonl(path, rows)
            report = audit(root)
            self.assertEqual(report["disposition"], "HOLD_AUDIT_CHECK_FAILED")
            self.assertFalse(report["checks"]["nearest_api_sample_neutral"])

    def test_api_timeline_detached_from_hud_capture_cannot_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = compact_fixture(Path(temporary))
            cell = root / "00-coast"
            result_path = cell / "RESULT.json"
            result = json.loads(result_path.read_text(encoding="utf-8"))
            rows_path = cell / "scorer-last-action.jsonl"
            rows = [json.loads(line) for line in rows_path.read_text(encoding="utf-8").splitlines()]
            offset = 1_000_000_000_000
            result["window_start_ns"] += offset
            result["window_end_ns"] += offset
            for row in rows:
                if row["coherent_tic"]:
                    row["sample_started_ns"] += offset
                    row["sample_returned_ns"] += offset
            initial = next(
                event
                for event in (
                    json.loads(line)
                    for line in (cell / "events.jsonl").read_text(encoding="utf-8").splitlines()
                )
                if event.get("event") == "typed_observation"
            )
            nearest = min(
                (row for row in rows if row["coherent_tic"]),
                key=lambda row: abs(row["sample_returned_ns"] - initial["capture_ns"]),
            )
            nearest["variables"].update(
                HEALTH=97.0,
                SELECTED_WEAPON=2.0,
                SELECTED_WEAPON_AMMO=48.0,
                AMMO2=48.0,
            )
            write_json(result_path, result)
            write_jsonl(rows_path, rows)
            report = audit(root)
            self.assertEqual(report["disposition"], "HOLD_AUDIT_CHECK_FAILED")
            self.assertFalse(report["checks"]["api_timeline_brackets_hud_capture"])

    def test_malformed_action_vector_cannot_be_treated_as_neutral(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = compact_fixture(Path(temporary))
            path = root / "00-coast" / "scorer-last-action.jsonl"
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            result = json.loads((root / "00-coast" / "RESULT.json").read_text(encoding="utf-8"))
            selected = next(
                row
                for row in rows
                if row["coherent_tic"]
                and result["window_start_ns"] <= row["sample_started_ns"]
                and row["sample_returned_ns"] <= result["window_end_ns"]
            )
            selected["action"] = [None] * len(selected["buttons"])
            write_jsonl(path, rows)
            report = audit(root)
            self.assertEqual(report["disposition"], "HOLD_AUDIT_CHECK_FAILED")
            self.assertFalse(report["checks"]["window_samples_neutral"])

    def test_non_neutral_window_cannot_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = compact_fixture(Path(temporary))
            path = root / "00-coast" / "scorer-last-action.jsonl"
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            selected = next(
                row
                for row in rows
                if row["coherent_tic"]
                and row["sample_started_ns"] >= json.loads((root / "00-coast" / "RESULT.json").read_text())["window_start_ns"]
                and row["sample_returned_ns"] <= json.loads((root / "00-coast" / "RESULT.json").read_text())["window_end_ns"]
            )
            selected["action"] = [1]
            write_jsonl(path, rows)
            report = audit(root)
            self.assertEqual(report["disposition"], "HOLD_AUDIT_CHECK_FAILED")
            self.assertFalse(report["checks"]["window_samples_neutral"])


if __name__ == "__main__":
    unittest.main()
