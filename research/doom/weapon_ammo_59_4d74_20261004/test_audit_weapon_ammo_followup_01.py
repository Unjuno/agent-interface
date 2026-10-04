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
