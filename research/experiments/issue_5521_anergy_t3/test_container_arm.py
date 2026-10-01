import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import audit

HERE = Path(__file__).resolve().parent


class ContainerArmTests(unittest.TestCase):
    def test_separate_policy_streams_assemble_and_audit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            arm_paths = []
            for policy in ("clear", "tombstone"):
                proc = subprocess.run(
                    [sys.executable, str(HERE / "container_arm.py"), policy],
                    check=True, capture_output=True, text=True,
                )
                path = root / f"{policy}.jsonl"
                path.write_text(proc.stdout)
                arm_paths.append(path)
            merged = root / "merged.jsonl"
            assembled = subprocess.run(
                [sys.executable, str(HERE / "assemble_container_raw.py"),
                 str(arm_paths[0]), str(arm_paths[1]), str(merged)],
                check=True, capture_output=True, text=True,
            )
            records = [json.loads(line) for line in merged.read_text().splitlines()]
            self.assertEqual(json.loads(assembled.stdout)["records"], 35)
            core_records = [record for record in records if record["type"] != "state_snapshot"]
            self.assertEqual(audit.validate(core_records), {
                "clear": {"verifier_checks": 6, "admitted_effects": 4},
                "tombstone": {"verifier_checks": 5, "admitted_effects": 3},
            })
            checked = subprocess.run(
                [sys.executable, str(HERE / "audit_container.py")],
                input=merged.read_text(), check=True, capture_output=True, text=True,
            )
            audit_result = json.loads(checked.stdout)
            self.assertEqual(audit_result["audit"], "PASS_T3_CONTAINER_RAW_ONLY")
            self.assertEqual(audit_result["state_snapshots"], 6)
            self.assertEqual(audit_result["corruption_controls_rejected"], {
                "expiry_disposition_swap": True,
                "expiry_generation_mutation": True,
            })
            self.assertEqual(
                [r["policy"] for r in records if r["type"] == "freeze"],
                ["clear"],
            )


if __name__ == "__main__":
    unittest.main()
