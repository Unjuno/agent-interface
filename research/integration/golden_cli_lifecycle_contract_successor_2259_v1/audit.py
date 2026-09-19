import json
import subprocess
from pathlib import Path

EXPECTED = ["SETUP_DOCTOR","MODEL_ATTEMPT","OBSERVATION","GUARDED_DISPATCH","REFUSAL","USEFUL_EFFECT","STALE_INVALIDATION","REPAIR","TERMINAL_RELEASE","CLEANUP_FAILURE"]
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]

def git_blob_sha(path):
    return subprocess.check_output(["git", "hash-object", str(path)], cwd=REPO, text=True).strip()

def main():
    with (ROOT / "RESULT.json").open(encoding="utf-8") as f: result = json.load(f)
    with (ROOT / "SOURCE_MANIFEST.json").open(encoding="utf-8") as f: manifest = json.load(f)
    assert result["status"] == "PASS_DESKTOP_VERTICAL_SLICE_CONTRACT_AUDIT_SCOPED"
    assert len(manifest["sources"]) == 4
    for source in manifest["sources"]:
        path = REPO / source["path"]
        assert path.is_file(), source["path"]
        assert git_blob_sha(path) == source["blob_sha"], source["path"]
    assert [row["state"] for row in result["rows_detail"]] == EXPECTED
    assert len(result["rows_detail"]) == 10
    assert all(row["authority_granted"] is False for row in result["rows_detail"])
    assert all(row["task_success_distinct"] and row["partial_effects_representable"] and row["unknown_fails_closed"] for row in result["rows_detail"])
    assert result["authority_grants"] == result["model_calls"] == result["gui_calls"] == result["input_calls"] == result["network_calls"] == 0
    print("INDEPENDENT_AUDIT_PASS rows=10 authority_grants=0 source_blobs=4")

if __name__ == "__main__":
    main()
