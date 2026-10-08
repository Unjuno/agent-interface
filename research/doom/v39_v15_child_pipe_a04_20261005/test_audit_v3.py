import copy, json, unittest
from audit_v3 import HERE, verify

class AuditV3Tests(unittest.TestCase):
    def test_full_frozen_audit(self):
        self.assertTrue(verify())

    def test_retained_streams_and_result_agree(self):
        result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
        candidate = next(row for row in result["arms"] if row["arm"] == "candidate")
        lines = (HERE / "results/candidate/child-stdout.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines, candidate["stdout_lines"])
        self.assertEqual(json.loads(lines[1])["parsed_command"], {"op": "finish"})

if __name__ == "__main__": unittest.main()
