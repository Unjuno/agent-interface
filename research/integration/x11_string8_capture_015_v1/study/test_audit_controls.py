import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from audit import expected_pixels, expected_schedule, validate
from controls import controls


def synthetic_evidence(directory: Path) -> None:
    source_root = Path(__file__).resolve().parents[1]
    (directory / "SCHEDULE.json").write_bytes((source_root / "SCHEDULE.json").read_bytes())
    cases = expected_schedule(directory)
    rows = []
    string_rows = byte_rows = 0
    for case_id, case in cases.items():
        size = case["width"] * 4 * case["height"]
        kind = "str" if case["index"] % 2 == 0 else "bytes"
        source = b"\x00" * size if kind == "str" else b"\xff" + b"\x00" * (size - 1)
        encoded = base64.b64encode(source).decode("ascii")
        if kind == "str":
            string_rows += 1
            data_text = source.decode("UTF-8")
            data_bytes_b64 = None
            legacy_error = {"type": "TypeError", "message": "synthetic unit fixture"}
            legacy_b64 = None
        else:
            byte_rows += 1
            data_text = None
            data_bytes_b64 = encoded
            legacy_error = None
            legacy_b64 = encoded
        spec = {"case_id": case_id, **case}
        row = {
            "case": spec,
            "status": "COMPLETE",
            "cleanup_complete": True,
            "fixture_exit": 0,
            "xvfb_exit": 0,
            "tcp_listening": False,
            "xauthority_mode": "0o600",
            "python_data_type": kind,
            "python_data_text": data_text,
            "python_data_bytes_b64": data_bytes_b64,
            "representation_b64": encoded,
            "representation_sha256": hashlib.sha256(source).hexdigest(),
            "legacy_error": legacy_error,
            "legacy_bytes_b64": legacy_b64,
            "candidate_bytes_b64": encoded,
            "candidate_sha256": hashlib.sha256(source).hexdigest(),
            "native_bytes_b64": encoded,
            "native_sha256": hashlib.sha256(source).hexdigest(),
            "source_pixels": expected_pixels(case["pattern"], case["width"], case["height"]),
            "native_pixels": expected_pixels(case["pattern"], case["width"], case["height"]),
            "geometry": {"width": case["width"], "height": case["height"], "depth": 24, "bits_per_pixel": 32, "bytes_per_line": case["width"] * 4, "byte_order": 0},
        }
        rows.append(row)
    raw = "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows).encode("utf-8")
    (directory / "raw.jsonl").write_bytes(raw)
    (directory / "summary.json").write_text(json.dumps({
        "scheduled": len(rows), "completed": len(rows), "failed": 0,
        "string_payloads": string_rows, "bytes_payloads": byte_rows,
        "legacy_type_errors": string_rows, "candidate_native_mismatches": 0,
        "pixel_oracle_mismatches": 0, "raw_sha256": hashlib.sha256(raw).hexdigest(),
    }), encoding="utf-8")


class AuditorControlsTests(unittest.TestCase):
    def test_auditor_accepts_synthetic_integrity_fixture_and_rejects_corruptions(self):
        with tempfile.TemporaryDirectory(prefix="x11-string8-audit-test-") as temp:
            evidence = Path(temp) / "formal"
            evidence.mkdir()
            synthetic_evidence(evidence)
            self.assertEqual(validate(evidence)["status"], "PASS_AUDIT")
            result = controls(evidence)
            self.assertEqual(result["status"], "PASS_CONTROLS")
            self.assertEqual(result["total"], 12)
            self.assertEqual(result["rejected"], 12)


if __name__ == "__main__":
    unittest.main()
