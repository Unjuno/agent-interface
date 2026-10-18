"""Follow-up regression for checksum paths in the retained A03 package."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent


class ManifestIntegrityTests(unittest.TestCase):
    def test_every_checksum_entry_resolves_to_a_file(self):
        missing = []
        for line in (ROOT / "SHA256SUMS").read_text().splitlines():
            digest, relative = line.split(None, 1)
            if not (ROOT / relative.strip()).is_file():
                missing.append(relative.strip())
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
