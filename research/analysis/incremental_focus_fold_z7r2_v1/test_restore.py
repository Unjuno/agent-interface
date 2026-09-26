import json, shutil, tempfile, unittest
from pathlib import Path
from restore import restore

ROOT = Path(__file__).resolve().parent

class RestoreTests(unittest.TestCase):
    def test_intact_and_existing_destination(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out"
            self.assertEqual(restore(ROOT, out), 331)
            with self.assertRaises(ValueError):
                restore(ROOT, out)

    def test_archive_corruption_rejected_after_intact_control(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            for n in ("ARCHIVE.json", "evidence.tar.xz"):
                shutil.copyfile(ROOT / n, p / n)
            self.assertEqual(restore(p, p / "control"), 331)
            a = p / "evidence.tar.xz"
            b = a.read_bytes()
            a.write_bytes(bytes([b[0] ^ 1]) + b[1:])
            with self.assertRaises(ValueError):
                restore(p, p / "bad")

if __name__ == "__main__":
    unittest.main()