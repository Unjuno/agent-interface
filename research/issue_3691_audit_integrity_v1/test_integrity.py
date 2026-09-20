import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import audit

ROOT = Path(__file__).parent
EVIDENCE = ROOT / "evidence"
RAW = EVIDENCE / "raw.json"
PREDECESSOR_FREEZE = EVIDENCE / "predecessor_FREEZE.json"
EXPECTED_RAW = "ccb9a75eefb7df73cb13dbc9191d33334fb672c2fd58fcc5fa32be998e182807"
EXPECTED_FREEZE = "f40494b1be99fb1e68d7b09c498297df35a72c043740b5f09d3faec7e059acfe"


def study_manifest():
    return {
        "predecessor_raw_sha256": EXPECTED_RAW,
        "predecessor_freeze_sha256": EXPECTED_FREEZE,
        "source_sha256": {
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in ("audit.py", "test_integrity.py")
        },
    }


class AuditIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads(RAW.read_text(encoding="utf-8"))

    def test_pristine_fixture_schema_is_accepted(self):
        self.assertEqual(hashlib.sha256(RAW.read_bytes()).hexdigest(), EXPECTED_RAW)
        self.assertEqual(hashlib.sha256(PREDECESSOR_FREEZE.read_bytes()).hexdigest(), EXPECTED_FREEZE)
        self.assertEqual(audit.errors_for(self.raw), [])

    def test_original_and_successor_event_mutations_are_rejected(self):
        mutations = (
            lambda r: r["events"][1]["identity"].__setitem__("xid", -1),
            lambda r: r["events"][3].__setitem__("admitted", True),
            lambda r: r["events"][4]["click"].__setitem__("emissions", 0),
            lambda r: r["events"].append({"event": "unexpected"}),
            lambda r: r["events"].append(copy.deepcopy(r["events"][3])),
            lambda r: r["events"][3].__setitem__("would_call_bridge", True),
            lambda r: r["events"].__setitem__(slice(2, 5), [r["events"][3], r["events"][2], r["events"][4]]),
            lambda r: r["events"].pop(3),
            lambda r: r["events"][0].__setitem__("unsupported", True),
        )
        for mutate in mutations:
            changed = copy.deepcopy(self.raw)
            mutate(changed)
            self.assertTrue(audit.errors_for(changed), changed)

    def test_json_boolean_never_satisfies_integer_count(self):
        for mutate in (
            lambda r: r.__setitem__("final_emissions", True),
            lambda r: r["events"][4]["click"].__setitem__("emissions", True),
            lambda r: r["events"][4]["effect"].__setitem__("count", True),
            lambda r: r["events"][4]["effect"].__setitem__("pid", True),
            lambda r: r["events"][0]["identity"].__setitem__("pid", True),
        ):
            changed = copy.deepcopy(self.raw)
            mutate(changed)
            self.assertTrue(audit.errors_for(changed), changed)

    def test_duplicate_json_keys_are_rejected(self):
        with self.assertRaises(ValueError):
            audit._load(b'{"final_emissions":1,"final_emissions":true}')

    def test_replacement_raw_and_freeze_are_rejected_by_manifest_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = copy.deepcopy(self.raw)
            freeze = root / "freeze.json"
            freeze.write_bytes(b'{"replacement":true}\n')
            raw["freeze_sha256"] = hashlib.sha256(freeze.read_bytes()).hexdigest()
            raw["events"][0]["identity"]["pixel_sha256"] = "0" * 64
            raw["events"][1]["identity"]["pixel_sha256"] = "0" * 64
            raw_path = root / "raw.json"
            raw_path.write_text(json.dumps(raw), encoding="utf-8")
            manifest = root / "study.json"
            manifest.write_text(json.dumps(study_manifest()), encoding="utf-8")
            result = audit.audit(raw_path, freeze, manifest)
            self.assertEqual(result["status"], "FAIL_AUDIT")
            self.assertIn("raw bytes do not match frozen predecessor hash", result["errors"])
            self.assertIn("freeze bytes do not match frozen predecessor hash", result["errors"])

    def test_exact_raw_freeze_and_direct_cli_routes_agree(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "study.json"
            manifest.write_text(json.dumps(study_manifest()), encoding="utf-8")
            output = root / "audit.json"
            direct = audit.audit(RAW, PREDECESSOR_FREEZE, manifest)
            self.assertEqual(direct["status"], "PASS_OFFLINE_STRUCTURAL_AUDIT", direct)
            completed = subprocess.run(
                [sys.executable, str(ROOT / "audit.py"), str(RAW), "--freeze",
                 str(PREDECESSOR_FREEZE), "--study-freeze", str(manifest), "--output", str(output)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(completed.stdout), direct)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), direct)


if __name__ == "__main__":
    unittest.main()
