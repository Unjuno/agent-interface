"""Postformal packaging controls; no scientific allocation is invoked."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unpack import unpack


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.source = self.base / "source"
        self.source.mkdir()
        original = Path(__file__).resolve().parent
        for path in (original / "PACK.json", *original.glob("evidence-*.xz.part")):
            shutil.copyfile(path, self.source / path.name)
        self.out = self.base / "out"

    def change(self, key, value):
        path = self.source / "PACK.json"
        pack = json.loads(path.read_bytes())
        pack[key] = value
        path.write_text(json.dumps(pack))

    def test_intact(self):
        self.assertEqual(unpack(self.source, self.out)["files"], 44)

    def test_tampered_part(self):
        path = self.source / "evidence-00.xz.part"
        data = path.read_bytes()
        path.write_bytes(bytes([data[0] ^ 1]) + data[1:])
        with self.assertRaisesRegex(ValueError, "part digest"):
            unpack(self.source, self.out)

    def test_wrong_count(self):
        self.change("files", 43)
        with self.assertRaisesRegex(ValueError, "member denominator"):
            unpack(self.source, self.out)

    def test_oversized_expansion(self):
        self.change("expanded_tar_bytes", 10_000_000)
        with self.assertRaisesRegex(ValueError, "invalid bound"):
            unpack(self.source, self.out)

    def test_existing_destination(self):
        self.out.mkdir()
        with self.assertRaisesRegex(ValueError, "destination must not exist"):
            unpack(self.source, self.out)

    def test_reordered_parts(self):
        path = self.source / "PACK.json"
        pack = json.loads(path.read_bytes())
        pack["parts"][0], pack["parts"][1] = pack["parts"][1], pack["parts"][0]
        path.write_text(json.dumps(pack))
        with self.assertRaisesRegex(ValueError, "part order/name"):
            unpack(self.source, self.out)


if __name__ == "__main__":
    unittest.main()
