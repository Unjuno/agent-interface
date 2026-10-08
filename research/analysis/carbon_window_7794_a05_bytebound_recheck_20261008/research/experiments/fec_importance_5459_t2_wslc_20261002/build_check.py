"""Single frozen-source construction gate for the WSLc container."""
import hashlib
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "PREREGISTRATION.md": "924ed19ba93b81cfbda9b7b3a79706d4c51915135a96fcb2693bd69fd9a76f23",
    "candidate.py": "01a883164ed09109025c82edc14cf91c3de43076bdea94ffa3b3420d124e9dd1",
    "auditor.py": "9ffc0c105cf79173a620dd0cebb1f254d205a981de51e7e67b87b781521137e7",
    "test_t2.py": "bfc57eef7f6391b7b05ef5536b1454467a77113dd102490261a4e5247ea90cf3",
    "build_check.py": "TO_BE_FROZEN",
}


def main():
    actual = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
              for name in EXPECTED if name != "build_check.py"}
    mismatches = {name: {"expected": EXPECTED[name], "actual": digest}
                  for name, digest in actual.items() if digest != EXPECTED[name]}
    if mismatches:
        print({"source_hash_mismatches": mismatches})
        return 2
    suite = unittest.defaultTestLoader.discover(str(ROOT), pattern="test_t2.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
