import json
import subprocess
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]

def blob(path):
    return subprocess.check_output(["git", "hash-object", str(path)], cwd=REPO, text=True).strip()

def main():
    manifest = json.loads((ROOT / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    for source in manifest["sources"]:
        path = REPO / source["path"]
        assert path.is_file(), source["path"]
        assert blob(path) == source["blob_sha"], source["path"]
    output = subprocess.check_output([sys.executable, str(ROOT / "test_adapter.py")], cwd=REPO, text=True)
    result = json.loads(output)
    assert result["status"] == "PASS_GOLDEN_V3_ADAPTER_P1_FIX_SCOPED"
    assert result["cases"] == 5
    assert result["nested_refusal_preserved"]
    assert result["completion_separated"]
    assert result["cleanup_completion_preserved"]
    assert all(result[key] == 0 for key in ["authority_grants", "model_calls", "gui_calls", "input_calls", "network_calls"])
    print("P1_FIX_AUDIT_PASS cases=5 source_blobs=2 authority_grants=0")

if __name__ == "__main__":
    main()
