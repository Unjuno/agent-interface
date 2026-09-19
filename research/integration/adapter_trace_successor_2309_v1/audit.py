import json
import subprocess
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
EXPECTED = [
    "SETUP_DOCTOR", "OBSERVATION", "GUARDED_DISPATCH", "REFUSAL",
    "USEFUL_EFFECT", "STALE_INVALIDATION", "REPAIR",
    "TERMINAL_RELEASE", "CLEANUP_FAILURE",
]

sys.path.insert(0, str(ROOT))
from adapter import exchange

def blob(path):
    return subprocess.check_output(["git", "hash-object", str(path)], cwd=REPO, text=True).strip()

def main():
    result = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
    trace = json.loads((ROOT / "trace.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    assert result["status"] == "PASS_SYNTHETIC_LIFECYCLE_ADAPTER_TRACE_SCOPED"
    assert [event["state"] for event in trace] == EXPECTED
    assert len(manifest["sources"]) == 4
    for source in manifest["sources"]:
        path = REPO / source["path"]
        assert path.is_file(), source["path"]
        assert blob(path) == source["blob_sha"], source["path"]
    out = exchange(trace)
    assert out["attempt_count"] == 9
    assert out["authority_grants"] == 0
    assert out["cleanup_failures"] == 1
    assert out["unknown_rejections"] == 0
    rows = out["attempts"]
    assert rows[7]["status"] == "released"
    assert rows[7]["release_attempted"] and rows[7]["released"]
    assert rows[7]["program_completed"] and rows[7]["task_success"]
    assert rows[8]["status"] == "cleanup_failed"
    assert rows[8]["release_attempted"] and not rows[8]["released"]
    assert not rows[8]["program_completed"]
    unknown = exchange([{"state": "UNMODELED_STATE"}])
    assert unknown["unknown_rejections"] == 1
    assert unknown["authority_grants"] == 0
    print("ADAPTER_TRACE_AUDIT_PASS attempts=9 authority_grants=0 unknown_fail_closed=1 cleanup_failures=1")

if __name__ == "__main__":
    main()
