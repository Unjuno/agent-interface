import json
import tempfile
import unittest
from pathlib import Path

from audit_weapon_ammo_followup_03 import audit


PACKAGE = Path(__file__).resolve().parent


def copy_fixture(destination: Path) -> Path:
    cell = destination / "00-coast"
    cell.mkdir(parents=True)
    for name in ("RESULT.json", "FINAL.json", "events.jsonl", "scorer-last-action.jsonl"):
        (cell / name).write_bytes((PACKAGE / "00-coast" / name).read_bytes())
    return destination


class WeaponAmmoAuditFollowup03Tests(unittest.TestCase):
    def mutate_nearest(self, root: Path, mutation) -> dict:
        path = root / "00-coast" / "scorer-last-action.jsonl"
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        events = [json.loads(line) for line in
                  (root / "00-coast" / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        initial = next(row for row in events if row.get("event") == "typed_observation")
        nearest = min(
            (row for row in rows if row.get("coherent_tic")),
            key=lambda row: abs(row["sample_returned_ns"] - initial["capture_ns"]),
        )
        mutation(nearest)
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        return audit(root)

    def test_nearest_api_sample_must_be_independently_coherent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = copy_fixture(Path(temporary))
            path = root / "00-coast" / "scorer-last-action.jsonl"
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            events = [json.loads(line) for line in
                      (root / "00-coast" / "events.jsonl").read_text(encoding="utf-8").splitlines()]
            initial = next(row for row in events if row.get("event") == "typed_observation")
            nearest = min(
                (row for row in rows if row.get("coherent_tic")),
                key=lambda row: abs(row["sample_returned_ns"] - initial["capture_ns"]),
            )
            nearest["tic_after"] = nearest["tic_before"] + 1
            path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

            report = audit(root)

            self.assertEqual(report["disposition"], "HOLD_AUDIT_CHECK_FAILED")
            self.assertFalse(report["checks"]["nearest_api_sample_coherent"])

    def test_nearest_api_sample_requires_ordered_sample_bounds(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = copy_fixture(Path(temporary))
            report = self.mutate_nearest(
                root,
                lambda row: row.update(sample_started_ns=row["sample_returned_ns"] + 1),
            )

            self.assertEqual(report["disposition"], "HOLD_AUDIT_CHECK_FAILED")
            self.assertFalse(report["checks"]["nearest_api_sample_coherent"])

    def test_nearest_api_sample_requires_finite_variables(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = copy_fixture(Path(temporary))
            report = self.mutate_nearest(
                root,
                lambda row: row["variables"].update(UNUSED_DIAGNOSTIC=float("nan")),
            )

            self.assertEqual(report["disposition"], "HOLD_AUDIT_CHECK_FAILED")
            self.assertFalse(report["checks"]["nearest_api_sample_coherent"])

    def test_retained_nearest_api_sample_remains_scoped_pass(self) -> None:
        report = audit(PACKAGE)

        self.assertEqual(report["disposition"], "PASS_HUD_WEAPON_AMMO_BINDING_SCOPED")
        self.assertTrue(report["checks"]["nearest_api_sample_coherent"])


if __name__ == "__main__":
    unittest.main()
