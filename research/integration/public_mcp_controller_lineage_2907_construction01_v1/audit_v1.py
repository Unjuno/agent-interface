"""Independent raw-only offline audit for construction04."""
import hashlib
import json
from pathlib import Path
import sys

EXPECTED = {
    "cli_v1/api.py": "6318f0d2fe0b0533d694175e2521eb86946dbed1",
    "cli_v1/observe.py": "08460ae506afcd0f9ad89b91064d121c55c5b419",
    "backends/x11_v1/backend.py": "965443ae5b0f92eab62adfb4aaa00b8963f34679",
    "backends/x11_v1/session.py": "e973b2f3f827951634344a320cd833a80a899d9e",
    "core_v1/contract.py": "87154518107e4231a6f8ec06e976d2856b375d1d",
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def git_blob(data):
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

def main():
    root, source = Path(sys.argv[1]), Path(sys.argv[2])
    raw = (root / "lineage.json").read_bytes()
    data = json.loads(raw)
    errors, observed_blobs = [], {}
    obs = data.get("observations", [])
    if [x.get("target") for x in obs] != ["inkscape", "calc", "chromium"]:
        errors.append("target_order")
    if [x.get("sequence") for x in obs] != [1, 2, 3]:
        errors.append("observation_sequence")
    if any(x.get("status") != "returned" or x.get("side_effect_authority") is not False or x.get("input_dispatched") is not False for x in obs):
        errors.append("observation_no_authority")
    if len({x.get("window_id") for x in obs}) != 3:
        errors.append("distinct_windows")
    for i, row in enumerate(obs):
        artifact = row.get("observation", {}).get("artifact", {})
        path = root / "images" / Path(artifact.get("path", "")).name
        if not path.is_file() or sha(path.read_bytes()) != artifact.get("sha256"):
            errors.append(f"image_{i}_digest")
    dispatches = data.get("dispatches", [])
    if len(dispatches) != 2:
        errors.append("dispatch_count")
    if dispatches:
        stale = dispatches[0].get("receipt", {}).get("result", {})
        if stale.get("status") != "refused" or stale.get("error") != "STALE_OBSERVATION":
            errors.append("stale_gate")
        if stale.get("backend_emissions") != 0:
            errors.append("stale_emissions")
        fresh = dispatches[1].get("receipt", {}).get("result", {})
        if fresh.get("status") != "completed" or fresh.get("admission") != "accepted":
            errors.append("fresh_neutral_dispatch")
        releases = fresh.get("execution", {}).get("releases", [])
        if not releases or any(r.get("verified") is not True or r.get("keys_down") != [] or r.get("buttons_down") != [] for r in releases):
            errors.append("dispatch_release")
    release = data.get("release", {})
    if release.get("verified") is not True or release.get("keys_down") != [] or release.get("buttons_down") != []:
        errors.append("final_release")
    if data.get("authority_granted") is not False or not data.get("session_object_identity") or not data.get("backend_object_identity"):
        errors.append("lineage_or_authority")
    for relative, expected in EXPECTED.items():
        path = source / relative
        actual = git_blob(path.read_bytes()) if path.is_file() else None
        observed_blobs[relative] = {"expected": expected, "actual": actual, "match": actual == expected}
        if actual != expected:
            errors.append("source_blob:" + relative)
    result = {
        "schema": "agent-interface/2907-controller-lineage-construction-audit-v1",
        "decision": "PASS_RAW_AUDIT" if not errors else "HOLD_RAW_AUDIT",
        "errors": errors, "formal_allocation": False,
        "raw_sha256": sha(raw), "source_git_blobs": observed_blobs,
        "scope": "one local Docker Linux/amd64 X11 session; three observations; stale sequence refusal; neutral ESC dispatch and verified release; not public MCP session fusion or full #2907 schedule"}
    out = Path(sys.argv[3]) if len(sys.argv) > 3 else root.parent / "audit04"
    out.mkdir(exist_ok=False)
    encoded = json.dumps(result, sort_keys=True, indent=2).encode() + b"\n"
    (out / "audit.json").write_bytes(encoded)
    (out / "sha256.txt").write_text(sha(encoded) + "  audit.json\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())

