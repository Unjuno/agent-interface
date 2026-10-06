"""Read-only binding audit for the supplemental bundled-runtime test logs."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    frozen = json.loads((ROOT / "SUPPLEMENTAL_FREEZE.json").read_text())
    checks = {f"source:{name}": digest(REPO / name) == expected
              for name, expected in frozen["source_files"].items()}
    for filename in ("bundled-39-normal.txt", "bundled-39-optimized.txt"):
        output = (ROOT / "results" / filename).read_text()
        checks[filename] = "Ran 39 tests" in output and "OK" in output
    result = {"scope": "source_hash_and_captured_test_result_shape_only",
              "checks": checks, "passed": all(checks.values())}
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
