"""Raw-only independent reference; never loads a runtime contract or runner."""
from collections import Counter
import gzip
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQ = ["capture.frame", "display.geometry", "input.pointer", "input.release_all"]
ARMS = {"main", "enum", "scalar", "combined"}
NAMES = ["linux", "windows", "macos", "os_list", "os_object", "os_integer", "os_boolean",
         "os_unknown", "state_list", "state_object", "state_integer", "state_boolean", "state_unknown",
         "frame_list", "frame_object", "frame_integer", "frame_boolean", "frame_unknown", "frame_duplicate",
         "permission", "unknown", "unsupported", "frame_mismatch", "permission_and_release_unsupported"]

def encoded(obj):
    return json.dumps(obj, separators=(",", ":"), sort_keys=True, allow_nan=False).encode()

def sha(obj):
    return hashlib.sha256(encoded(obj)).hexdigest()

def reconstructed_case(indices):
    m, p, n, o, b = indices
    name = NAMES[m]
    manifest = {"schema": "agent-interface/backend-v1", "backend_id": "fixture",
                "platform": {"os": name if m < 3 else "linux", "backend": "inert"},
                "capabilities": {key: {"detail": "", "state": "supported"} for key in REQ},
                "coordinate_frames": ["window_client"], "clock": {"monotonic": True, "unit": "ns"},
                "permissions": []}
    bad_values = [[], {}, 0, False, "invalid"]
    if 3 <= m <= 7:
        manifest["platform"]["os"] = bad_values[m - 3]
    if 8 <= m <= 12:
        manifest["capabilities"]["input.pointer"]["state"] = bad_values[m - 8]
    if 13 <= m <= 17:
        manifest["coordinate_frames"] = [bad_values[m - 13]]
    if m == 18:
        manifest["coordinate_frames"] *= 2
    if m in (19, 20, 21, 23):
        manifest["capabilities"]["input.pointer"]["state"] = {
            19: "permission_required", 20: "unknown", 21: "unsupported", 23: "permission_required"}[m]
    if m == 22:
        manifest["coordinate_frames"] = ["screen_physical_px"]
    if m == 23:
        manifest["capabilities"]["input.release_all"]["state"] = "unsupported"
    program = {"schema": "agent-interface/program-v1", "program_id": "composition",
               "source": {"observation_seq": True if p == 2 else 1, "binding_revision": 1},
               "authority": {"lease_id": "fixture", "expires_at_ns": 10},
               "terminal": {"release_all_required": True},
               "ops": [{"op": "pointer_move", "frame": "window_client", "x": 0, "y": 0},
                       {"op": "observe", "frame": "window_client", "x": 0, "y": 0, "w": 1, "h": 1}]}
    if p != 1:
        program["ops"].append({"op": "release_all"})
    evidence = dict(zip(["now_ns", "current_observation_seq", "current_binding_revision"],
                        [[9, 10, 11, True, 10.0][n], [1, 2, True, 1.0, None][o], [1, 2, True, 1.0, {}][b]]))
    return {"id": f"m{m:02d}-p{p}-n{n}-o{o}-b{b}", "manifest_name": name,
            "manifest": manifest, "program": program, "evidence": evidence}

def reference(case):
    program, manifest, evidence = case["program"], case["manifest"], case["evidence"]
    malformed = (program["source"]["observation_seq"] is True or
                 program["ops"][-1]["op"] != "release_all")
    os_name = manifest["platform"]["os"]
    state = manifest["capabilities"]["input.pointer"]["state"]
    frames = manifest["coordinate_frames"]
    malformed |= type(os_name) is not str or os_name not in ["linux", "windows", "macos"]
    malformed |= type(state) is not str or state not in ["supported", "permission_required", "unknown", "unsupported"]
    malformed |= any(type(f) is not str or f not in ["window_client", "screen_physical_px", "screen_logical"] for f in frames)
    malformed |= len({encoded(f) for f in frames}) != len(frames)
    malformed |= any(type(v) is not int or not 0 <= v < 2**63 for v in evidence.values())
    if malformed:
        return {"accepted": False, "error": "INVALID_PROGRAM", "required_capabilities": []}
    error = None
    if evidence["now_ns"] > 10:
        error = "LEASE_EXPIRED"
    elif evidence["current_observation_seq"] != 1:
        error = "STALE_OBSERVATION"
    elif evidence["current_binding_revision"] != 1:
        error = "STALE_BINDING"
    elif state == "permission_required":
        error = "PERMISSION_DENIED"
    elif state != "supported":
        error = "UNSUPPORTED_CAPABILITY"
    elif "window_client" not in frames:
        error = "COORDINATE_UNSUPPORTED"
    return {"accepted": error is None, "error": error, "required_capabilities": REQ}

def verify(cases, rows):
    errors = []
    expected = {c["id"]: c for c in map(reconstructed_case, itertools.product(range(24), range(3), range(5), range(5), range(5)))}
    actual = {}
    for case in cases:
        cid = case.get("id")
        if cid in actual or cid not in expected or encoded(case) != encoded(expected[cid]):
            errors.append("case_identity:" + str(cid))
        actual[cid] = case
    if set(actual) != set(expected) or len(cases) != 9000:
        errors.append("case_coverage")
    coverage = set()
    mismatches, exceptions, mutations = Counter(), Counter(), Counter()
    mismatch_ids = {arm: [] for arm in sorted(ARMS)}
    output_counts = {arm: Counter() for arm in sorted(ARMS)}
    for row in rows:
        arm, cid = row.get("arm"), row.get("id")
        key = (arm, cid)
        if arm not in ARMS or cid not in expected or key in coverage:
            errors.append("row_identity:" + str(key))
            continue
        coverage.add(key)
        if set(row) != {"arm", "id", "input_sha256", "output", "unchanged"} or row["input_sha256"] != sha(expected[cid]):
            errors.append("row_input:" + str(key))
        if row.get("unchanged") is not True:
            mutations[arm] += 1
            errors.append("input_mutation:" + str(key))
        output = row.get("output", {})
        if "exception" in output:
            exceptions[arm] += 1
            label = output["exception"]
        else:
            label = output.get("error") or "ACCEPTED"
        output_counts[arm][label] += 1
        if encoded(output) != encoded(reference(expected[cid])):
            mismatches[arm] += 1
            mismatch_ids[arm].append(cid)
            if arm == "combined":
                errors.append("combined_reference:" + cid)
    if len(rows) != 36000 or coverage != set(itertools.product(ARMS, expected)):
        errors.append("row_coverage")
    return {"decision": "PASS_CORE_ADMISSION_COMPOSITION_SCOPED" if not errors else "FAIL_CORE_ADMISSION_COMPOSITION_SCOPED",
            "cases_per_arm": 9000, "rows": len(rows), "errors": errors,
            "mismatches": {a: mismatches[a] for a in sorted(ARMS)},
            "exceptions": {a: exceptions[a] for a in sorted(ARMS)},
            "mutations": {a: mutations[a] for a in sorted(ARMS)},
            "output_counts": {a: dict(output_counts[a]) for a in sorted(ARMS)},
            "mismatch_ids_sha256": {a: sha(sorted(mismatch_ids[a])) for a in sorted(ARMS)}}

def read_gzip(path):
    with gzip.open(path, "rt", encoding="utf-8") as inp:
        return [json.loads(line) for line in inp]

def main():
    freeze = json.loads((ROOT / "FREEZE.json").read_bytes())
    for name, expected in freeze["source_sha256"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError("freeze source mismatch: " + name)
    receipt = json.loads((ROOT / "raw/RECEIPT.json").read_bytes())
    for name, expected in receipt["raw_sha256"].items():
        if hashlib.sha256((ROOT / "raw" / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError("raw hash mismatch: " + name)
    result = verify(read_gzip(ROOT / "raw/cases.jsonl.gz"), read_gzip(ROOT / "raw/results.jsonl.gz"))
    if receipt["cases"] != 9000 or receipt["rows"] != 36000 or set(receipt["arms"]) != ARMS:
        result["errors"].append("receipt_counts")
        result["decision"] = "FAIL_CORE_ADMISSION_COMPOSITION_SCOPED"
    (ROOT / "AUDIT.json").open("xb").write(json.dumps(result, indent=2).encode() + b"\n")
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(result["errors"]))

if __name__ == "__main__":
    main()
