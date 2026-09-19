import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
EXPECTED = [
    "SETUP_DOCTOR", "MODEL_ATTEMPT", "OBSERVATION", "GUARDED_DISPATCH",
    "REFUSAL", "USEFUL_EFFECT", "STALE_INVALIDATION", "REPAIR",
    "TERMINAL_RELEASE", "CLEANUP_FAILURE",
]
EXPECTED_ROLES = {
    "runtime/golden_desktop_demo_v3.py": {"doctor", "run_live", "schema"},
    "runtime/cli_v1/api.py": {"setup", "observe", "dispatch", "release"},
    "runtime/core_v1/__init__.py": {"effect", "stale", "repair"},
    "runtime/GOLDEN_DESKTOP_DEMO_V3.md": {"acceptance", "limits"},
}

def main():
    r = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
    m = json.loads((ROOT / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    assert r["status"] == "PASS_DESKTOP_VERTICAL_SLICE_CONTRACT_AUDIT_SCOPED"
    assert len(m["sources"]) == 4
    assert {s["path"] for s in m["sources"]} == set(EXPECTED_ROLES)
    for source in m["sources"]:
        path = REPO / source["path"]
        assert path.is_file(), source["path"]
        assert set(source["roles"]) == EXPECTED_ROLES[source["path"]]
        actual = subprocess.check_output(
            ["git", "hash-object", str(path)], text=True
        ).strip()
        assert actual == source["blob_sha"], (source["path"], actual, source["blob_sha"])
    rows = r["rows_detail"]
    assert [x["state"] for x in rows] == EXPECTED
    assert len(rows) == 10 and all(x["authority_granted"] is False for x in rows)
    assert all(
        x["task_success_distinct"]
        and x["partial_effects_representable"]
        and x["unknown_fails_closed"]
        for x in rows
    )
    assert r["authority_grants"] == r["model_calls"] == r["gui_calls"] == 0
    assert r["input_calls"] == r["network_calls"] == 0
    print("INDEPENDENT_AUDIT_PASS rows=10 source_blobs=4 authority_grants=0")

if __name__ == "__main__":
    main()
