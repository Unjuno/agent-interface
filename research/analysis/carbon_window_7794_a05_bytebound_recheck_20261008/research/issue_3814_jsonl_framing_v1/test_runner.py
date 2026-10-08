import json
import unittest

from research.issue_3814_jsonl_framing_v1 import preflight, runner
import hashlib
import tempfile
from pathlib import Path


class FramingConstructionTests(unittest.TestCase):
    def test_jsonl_without_terminal_lf_is_valid_json_but_not_a_complete_frame(self):
        complete = b'{"status":"returned","result":{"status":"completed"}}\n'
        delivered = complete[:-1]
        self.assertEqual(delivered, complete[:-1])
        self.assertEqual(json.loads(delivered)["result"]["status"], "completed")
        self.assertTrue(complete.endswith(b"\n"))
        self.assertFalse(delivered.endswith(b"\n"))

    def test_hash_binds_terminal_byte(self):
        complete = b'{"status":"returned"}\n'
        self.assertNotEqual(runner.sha(complete), runner.sha(complete[:-1]))

    def test_preflight_accepts_exact_source_and_rejects_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            exp = root / "research/issue_3814_jsonl_framing_v1"
            exp.mkdir(parents=True)
            source = root / "frozen.py"
            source.write_bytes(b"frozen source\n")
            image = "python@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e"
            freeze = {"source_sha256": {"frozen.py": hashlib.sha256(source.read_bytes()).hexdigest()},
                      "C": {"image": image, "image_id": "sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e",
                            "platform": "linux/amd64", "docker_server": "29.8.0"},
                      "formal": {"invocations": 0, "maximum": 1}}
            (exp / "FREEZE.json").write_text(json.dumps(freeze), encoding="utf-8")
            import os
            previous = os.environ.get("ISSUE3814_DOCKER_SERVER")
            os.environ["ISSUE3814_DOCKER_SERVER"] = "29.8.0"
            exact = preflight.verify(root, image, freeze["C"]["image_id"], "linux/amd64")
            self.assertEqual(exact["disposition"], "PASS_SOURCE_FREEZE")
            source.write_bytes(b"mutated source\n")
            changed = preflight.verify(root, image, freeze["C"]["image_id"], "linux/amd64")
            if previous is None:
                os.environ.pop("ISSUE3814_DOCKER_SERVER", None)
            else:
                os.environ["ISSUE3814_DOCKER_SERVER"] = previous
            self.assertEqual(changed["disposition"], "STOP_SOURCE_OR_IMAGE_MISMATCH")
            self.assertIn("SOURCE_SHA256:frozen.py", changed["mismatches"])


if __name__ == "__main__":
    unittest.main()
