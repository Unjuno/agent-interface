import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent


class ReconstructFormalTests(unittest.TestCase):
    def test_reconstruct_accepts_crlf_checkout_of_text_evidence(self):
        source_formal = PACKAGE / "formal"
        manifest = json.loads(
            (source_formal / "FORMAL_MANIFEST.json").read_text(encoding="utf-8")
        )
        text_paths = ["terminal.json", *manifest["streams"].keys()]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            temp_formal = temp_root / "formal"
            temp_formal.mkdir()
            shutil.copyfile(
                PACKAGE / "reconstruct_formal.py",
                temp_root / "reconstruct_formal.py",
            )
            shutil.copyfile(
                source_formal / "FORMAL_MANIFEST.json",
                temp_formal / "FORMAL_MANIFEST.json",
            )

            for part in manifest["raw"]["parts"]:
                source = source_formal / part["path"]
                destination = temp_formal / part["path"]
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)

            candidate = manifest["candidate_result"]
            shutil.copyfile(
                source_formal / candidate.get("transport", "candidate_result.json.gz"),
                temp_formal / candidate.get("transport", "candidate_result.json.gz"),
            )

            for relative_path in text_paths:
                source = source_formal / relative_path
                original = source.read_bytes().replace(b"\r\n", b"\n")
                (temp_formal / relative_path).write_bytes(
                    original.replace(b"\n", b"\r\n")
                )

            result = subprocess.run(
                [sys.executable, str(temp_root / "reconstruct_formal.py")],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("PASS raw=360448 rows=4096 candidate=44255", result.stdout)


if __name__ == "__main__":
    unittest.main()
