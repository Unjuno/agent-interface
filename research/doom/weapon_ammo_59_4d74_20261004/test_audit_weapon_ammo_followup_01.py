import json
import tempfile
import unittest
from pathlib import Path

from audit_weapon_ammo_followup_01 import audit


PACKAGE = Path(__file__).resolve().parent
CELL = PACKAGE / "00-coast"


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def write_jsonl(path: Path, values: list[object]) -> None:
    path.write_text("".join(json.dumps(value) + "\n" for value in values), encoding="utf-8")


def compact_fixture(destination: Path) -> Path:
    cell = destination / "00-coast"
    cell.mkdir(parents=True)
    (destination / "FILES.json").write_bytes((PACKAGE / "FILES.json").read_bytes())
    (cell / "runtime").mkdir()
    (cell / "runtime" / "001.png").write_bytes((CELL / "runtime" / "001.png").read_bytes())
    for name in ("RESULT.json", "FINAL.json"):
        write_json(cell / name, json.loads((CELL / name).read_text(encoding="utf-8")))
    for name in ("events.jsonl", "scorer-last-action.jsonl"):
        rows = [json.loads(line) for line in (CELL / name).read_text(encoding="utf-8").splitlines()]
        write_jsonl(cell / name, rows)
    return destination


def read_events(root: Path) -> tuple[Path, list[dict]]:
    path = root / "00-coast" / "events.jsonl"
    return path, [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def read_rows(root: Path) -> tuple[Path, list[dict]]:
    path = root / "00-coast" / "scorer-last-action.jsonl"
    return path, [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def prewindow_comparison_row(root: Path, rows: list[dict]) -> dict:
    cell = root / "00-coast"
    result = json.loads((cell / "RESULT.json").read_text(encoding="utf-8"))
    events = [json.loads(line) for line in (cell / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    initial = next(event for event in events if event.get("event") == "typed_observation")
    candidates = [
        row for row in rows
        if row.get("coherent_tic")
        and initial["capture_ns"] <= row["sample_started_ns"]
        and row["sample_started_ns"] <= row["sample_returned_ns"]
        and row["sample_returned_ns"] <= result["window_start_ns"]
    ]
    return min(candidates, key=lambda row: abs(row["sample_returned_ns"] - initial["capture_ns"]))


class WeaponAmmoAuditFollowupTests(unittest.TestCase):
    def test_committed_layout_audits_without_saved_audit(self) -> None:
        report = audit(PACKAGE)
        self.assertEqual(report["disposition"], "PASS_HUD_WEAPON_AMMO_BINDING_SCOPED")
        self.assertEqual(report["sample_count"], 90)
        self.assertTrue(all(report["checks"].values()))

    def test_modified_raw_input_fails_pinned_manifest_check(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = compact_fixture(Path(temporary))
            path = root / "00-coast" / "RESULT.json"
            path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            report = audit(root)
            self.assertEqual(report["disposition"], "HOLD_RAW_INPUT_INTEGRITY_MISMATCH")
            self.assertFalse(report["checks"]["raw_inputs_match_pinned_manifest"])

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
            report = audit(root, verify_raw_integrity=False)
            self.assertEqual(report["disposition"], "HOLD_AUDIT_CHECK_FAILED")
            self.assertFalse(report["checks"]["HUD_signals_validly_bound_to_initial_capture"])

    def test_wrong_signal_capture_time_cannot_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = compact_fixture(Path(temporary))
            path, events = read_events(root)
            initial = next(event for event in events if event.get("id") == "initial")
            initial["signals"]["health"]["capture_ns"] += 1
            write_jsonl(path, events)
            report = audit(root, verify_raw_integrity=False)
            self.assertEqual(report["disposition"], "HOLD_AUDIT_CHECK_FAILED")
            self.assertFalse(report["checks"]["HUD_signals_validly_bound_to_initial_capture"])

    def test_typed_capture_cannot_diverge_from_screen_observation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = compact_fixture(Path(temporary))
            path, events = read_events(root)
            initial = next(event for event in events if event.get("event") == "typed_observation")
            initial["sequence"] += 100
            initial["pointer_binding"] = {"focus": 1, "surface": 1, "geometry": [1, 1, 1, 1]}
            initial["frame_rgb_sha256"] = "0" * 64
            for signal in initial["signals"].values():
                signal["sequence"] = initial["sequence"]
                signal["capture_ns"] = initial["capture_ns"]
                signal["binding"] = initial["pointer_binding"]
            write_jsonl(path, events)
            report = audit(root, verify_raw_integrity=False)
            self.assertEqual(report["disposition"], "HOLD_AUDIT_CHECK_FAILED")
            self.assertFalse(report["checks"]["typed_capture_matches_screen_observation"])

    def test_comparison_sample_must_be_neutral(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = compact_fixture(Path(temporary))
            path, rows = read_rows(root)
            prewindow_comparison_row(root, rows)["action"] = [1]
            write_jsonl(path, rows)
            report = audit(root, verify_raw_integrity=False)
            self.assertEqual(report["disposition"], "HOLD_AUDIT_CHECK_FAILED")
            self.assertFalse(report["checks"]["comparison_sample_neutral"])

    def test_malformed_window_action_vector_cannot_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = compact_fixture(Path(temporary))
            path, rows = read_rows(root)
            result = json.loads((root / "00-coast" / "RESULT.json").read_text(encoding="utf-8"))
            selected = next(
                row for row in rows
                if row["coherent_tic"]
                and result["window_start_ns"] <= row["sample_started_ns"]
                and row["sample_returned_ns"] <= result["window_end_ns"]
            )
            selected["action"] = [None] + [0.0] * 8
            write_jsonl(path, rows)
            report = audit(root, verify_raw_integrity=False)
            self.assertEqual(report["disposition"], "HOLD_AUDIT_CHECK_FAILED")
            self.assertFalse(report["checks"]["window_samples_neutral"])

    def test_wrong_width_window_action_vector_cannot_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = compact_fixture(Path(temporary))
            path, rows = read_rows(root)
            result = json.loads((root / "00-coast" / "RESULT.json").read_text(encoding="utf-8"))
            selected = next(
                row for row in rows
                if row["coherent_tic"]
                and result["window_start_ns"] <= row["sample_started_ns"]
                and row["sample_returned_ns"] <= result["window_end_ns"]
            )
            selected["action"] = [0.0] * 8
            write_jsonl(path, rows)
            report = audit(root, verify_raw_integrity=False)
            self.assertEqual(report["disposition"], "HOLD_AUDIT_CHECK_FAILED")
            self.assertFalse(report["checks"]["window_samples_neutral"])

    def test_shifted_hud_time_cannot_select_a_distant_sample(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = compact_fixture(Path(temporary))
            path, events = read_events(root)
            initial = next(event for event in events if event.get("event") == "typed_observation")
            initial["capture_ns"] += 1_000_000_000_000
            for signal in initial["signals"].values():
                signal["capture_ns"] = initial["capture_ns"]
            write_jsonl(path, events)
            report = audit(root, verify_raw_integrity=False)
            self.assertEqual(report["disposition"], "HOLD_NO_PREWINDOW_COMPARISON_SAMPLE")
            self.assertFalse(report["checks"]["prewindow_comparison_sample_exists"])


if __name__ == "__main__":
    unittest.main()
