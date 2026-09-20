import base64
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from runtime.cli_v1.review import review
from runtime.distribution_v2.build import SOURCE_FILES, build


class PublicReviewTests(unittest.TestCase):
    def test_portable_cli_returns_exact_image_and_preserves_failed_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            for name in SOURCE_FILES:
                target = source / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(Path(name).read_bytes())
            archive = root / "runtime.pyz"
            build(source, archive, root / "manifest.json", root / "sums.txt")
            pixels = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a9xkAAAAASUVORK5CYII=")
            png = root / "frame.png"
            png.write_bytes(pixels)
            report = root / "report.json"
            report.write_text(json.dumps({"status": "failed", "error": "timeout", "records": [
                {"event": "observation", "sequence": 1, "capture_ns": 12, "image": str(png)}]}))
            original = report.read_bytes()
            command = [sys.executable, str(archive), "review", "--report", str(report), "--run-directory", str(root)]
            result = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            row = json.loads(result.stdout)
            self.assertEqual(base64.b64decode(row["image"]["data"]), pixels)
            self.assertEqual(row["receipt"]["report"]["status"], "failed")
            self.assertEqual(row["authority"], "none")
            png.unlink()
            missing = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertEqual(missing.returncode, 2)
            row = json.loads(missing.stdout)
            self.assertEqual(row["image_status"], "needs_review")
            self.assertEqual(row["receipt"]["report"]["error"], "timeout")
            self.assertEqual(report.read_bytes(), original)

    def test_newest_missing_image_never_falls_back_to_older_capture(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            png = root / "old.png"
            png.write_bytes(b"\x89PNG\r\n\x1a\n")
            report = root / "report.json"
            report.write_text(json.dumps({"status": "boundary", "records": [
                {"event": "observation", "sequence": 1, "capture_ns": 12, "image": str(png)},
                {"event": "observation", "sequence": 2, "capture_ns": 13, "image": str(root / "missing.png") }]}))
            row = review(report, root)
            self.assertEqual(row["image_status"], "needs_review")
            self.assertIsNone(row["image"])


if __name__ == "__main__":
    unittest.main()
