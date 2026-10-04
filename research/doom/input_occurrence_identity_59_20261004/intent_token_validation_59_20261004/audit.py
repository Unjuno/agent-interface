"""Audit the intent-token boundary construction record and its source pins."""
import hashlib
import json
import subprocess
from pathlib import Path


PACKET = Path(__file__).resolve().parent
ROOT = PACKET.parents[3]


def main():
    freeze = json.loads((PACKET / "FREEZE.json").read_text(encoding="utf-8"))
    source_ref = f"{freeze['baseline_commit']}:{freeze['baseline_source_path']}"
    blob = subprocess.check_output(["git", "rev-parse", source_ref], cwd=ROOT,
                                   text=True).strip()
    assert blob == freeze["baseline_source_blob"]
    test_ref = (f"{freeze['baseline_commit']}:"
                "research/doom/input_occurrence_identity_59_20261004/test_attribution.py")
    test_blob = subprocess.check_output(["git", "rev-parse", test_ref], cwd=ROOT,
                                        text=True).strip()
    assert test_blob == freeze["baseline_test_blob"]

    out = PACKET / "out"
    red = (out / "red.txt").read_text(encoding="utf-8")
    assert "ValueError not raised" in red and "KeyError: 'intent_token'" in red
    assert (out / "red-exit.txt").read_text().strip() == "1"
    green = (out / "green.txt").read_text(encoding="utf-8")
    assert "Ran 9 tests" in green and "OK" in green
    assert "swap limit" in green.lower()
    assert (out / "green-exit.txt").read_text().strip() == "0"
    oracle = (out / "oracle-audit.txt").read_text(encoding="utf-8")
    assert "260 finite detection-bracket cases match independent oracle" in oracle
    assert (out / "oracle-audit-exit.txt").read_text().strip() == "0"

    manifest = json.loads((PACKET / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        data = (ROOT / entry["path"]).read_bytes()
        assert len(data) == entry["bytes"], entry["path"]
        assert hashlib.sha256(data).hexdigest() == entry["sha256"], entry["path"]
    print(json.dumps({"status": "PASS", "manifest_files": len(manifest["files"]),
                      "baseline_regression": "REPRODUCED",
                      "focused_wslc_tests": "9_PASS",
                      "finite_oracle_cases": 260}, sort_keys=True))


if __name__ == "__main__":
    main()
