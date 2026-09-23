import hashlib
import json
import subprocess
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    manifest = json.loads((ROOT / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    for item in manifest["sources"]:
        path = REPO / item["path"]
        assert path.is_file(), item["path"]
        assert sha(path) == item["sha256"], item["path"]
    output = subprocess.check_output([sys.executable, str(ROOT / "oracle.py")], cwd=REPO, text=True)
    result = json.loads(output)
    assert result["status"] == "PASS_DWELL_TIMEOUT_ORACLE_SCOPED"
    assert result["cases"] == 4
    assert result["censored_not_completion"]
    assert result["finite_grid_coverage"]
    assert result["live_gui_calls"] == result["model_calls"] == result["network_calls"] == 0
    print("DWELL_TIMEOUT_ORACLE_AUDIT_PASS cases=4 sources=1 external_calls=0")

if __name__ == "__main__":
    main()
