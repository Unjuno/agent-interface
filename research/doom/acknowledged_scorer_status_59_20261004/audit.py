"""Independent audit of the retained scorer-status construction packet."""
import hashlib
import json
import subprocess
from pathlib import Path


PACKET = Path(__file__).resolve().parent
RESEARCH_DOOM = PACKET.parent
REPO = RESEARCH_DOOM.parent.parent


def sha256(data):
    return hashlib.sha256(data).hexdigest().upper()


def main():
    freeze = json.loads((PACKET / "FREEZE.json").read_text(encoding="utf-8"))
    baseline = subprocess.check_output(
        ["git", "show", f"{freeze['source_base_commit']}:research/doom/acknowledged_scorer_v1.py"],
        cwd=REPO)
    assert sha256(baseline) == freeze["baseline_files"]["research/doom/acknowledged_scorer_v1.py"]

    out = PACKET / "out" / "construction01"
    red = (out / "red.txt").read_text(encoding="utf-8")
    assert "AssertionError: 'UPDATE_UNAVAILABLE' != 'SAMPLE_UNAVAILABLE'" in red
    assert (out / "red-exit.txt").read_text().strip() == "1"
    green = (out / "wslc-green.txt").read_text(encoding="utf-8")
    assert "Ran 11 tests" in green and "OK" in green
    assert (out / "wslc-green-exit.txt").read_text().strip() == "0"
    assert "swap limit" in green.lower()

    manifest = json.loads((PACKET / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        data = (REPO / entry["path"]).read_bytes()
        assert len(data) == entry["bytes"], entry["path"]
        assert sha256(data) == entry["sha256"], entry["path"]
    print(json.dumps({"status": "PASS", "manifest_files": len(manifest["files"]),
                      "baseline_regression": "REPRODUCED",
                      "focused_wslc_tests": "11_PASS",
                      "live_or_input_claim": False}, sort_keys=True))


if __name__ == "__main__":
    main()
