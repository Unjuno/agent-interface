#!/usr/bin/env python3
"""Independent raw-only audit; imports neither candidate nor runner."""
import copy
import hashlib
import json
import pathlib
import sys

CASES = ("QUIET", "REPAINT_A", "PERSIST_B", "ABA_1PX", "ABA_2X2", "ABA_8X8")
ALLOC = "xdamage-temporal-boundary-3935-v3-20260927-01"
IMAGE_ID = "sha256:e2a7634d2b9627ec037c488d6aa472c6c00d5ef0dda6e302f7dced8b9b8752d4"
N = 64 * 64 * 3
MATRIX = {
    "QUIET": (False, False, False), "REPAINT_A": (False, False, True),
    "PERSIST_B": (True, True, True), "ABA_1PX": (True, False, True),
    "ABA_2X2": (True, False, True), "ABA_8X8": (True, False, True),
}


def check(rows, summary, raw, source_root=None):
    errors = []
    sessions = 8 if summary.get("mode") == "formal" else summary.get("sessions", 1)
    if summary.get("allocation") != ALLOC:
        errors.append("allocation")
    if summary.get("image_id") != IMAGE_ID:
        errors.append("image")
    if summary.get("mode") == "formal" or summary.get("source_commit") is not None:
        if not isinstance(summary.get("source_commit"), str) or len(summary["source_commit"]) != 40:
            errors.append("source_commit")
        if not summary.get("freeze_sha256") or summary.get("frozen_source_sha256") != summary.get("code_sha256"):
            errors.append("freeze_binding")
    if source_root is not None:
        root=pathlib.Path(source_root)
        code=summary.get("code_sha256",{})
        if set(code)!={"run_formal.py","xdamage_native.c","audit_formal.py","exact_gate.py","temporal_protocol.py","test_temporal_protocol.py","run_container.ps1"}:
            errors.append("source_set")
        else:
            for name,digest in code.items():
                try: actual=hashlib.sha256((root/name).read_bytes()).hexdigest()
                except OSError: actual="missing"
                if actual!=digest: errors.append("source_hash:"+name)
        try:
            freeze=json.loads((root/"FREEZE.json").read_text())
            if summary.get("mode")=="formal":
                gate_bytes=(root/"exact_gate.py").read_bytes()
                git_blob=hashlib.sha1(b"blob "+str(len(gate_bytes)).encode()+b"\0"+gate_bytes).hexdigest()
                if git_blob!=freeze.get("exact_gate_git_blob") or git_blob!="d2629bc94d40cc0a8e1bf9e053585549218629ed": errors.append("exact_gate_blob")
                if summary.get("freeze_sha256")!=hashlib.sha256((root/"FREEZE.json").read_bytes()).hexdigest(): errors.append("freeze_sha")
                if summary.get("frozen_source_sha256")!=freeze.get("source_sha256"): errors.append("freeze_source_set")
        except (OSError,ValueError):
            if summary.get("mode")=="formal": errors.append("freeze_missing")
    expected_rows = {(s, c) for s in range(1, sessions + 1) for c in CASES}
    found_rows = {(r.get("session"), r.get("case")) for r in rows}
    if len(rows) != sessions * 6 or found_rows != expected_rows or len(found_rows) != len(rows):
        errors.append("coverage")
    expected_order = []
    for s in range(1, sessions + 1):
        rotation = (s - 1) % len(CASES)
        expected_order.extend((s, CASES[(rotation + offset) % len(CASES)]) for offset in range(6))
    if [(r.get("session"), r.get("case")) for r in rows] != expected_order:
        errors.append("session_rotated_order")
    for row in rows:
        case = row.get("case")
        if (row.get("session"), case) not in expected_rows or case not in MATRIX:
            errors.append("unexpected_row")
            continue
        frames = []
        for name, sha_field in ((row.get("baseline_file"), "baseline_sha256"),
                                (row.get("middle_file"), "middle_sha256"),
                                (row.get("endpoint_file"), "endpoint_sha256")):
            data = raw.get(name, b"")
            if len(data) != N or hashlib.sha256(data).hexdigest() != row.get(sha_field):
                errors.append("raw_hash_or_length")
                data = b"\0" * N
            frames.append(data)
        baseline, middle, endpoint = frames
        middle_diff, endpoint_diff = baseline != middle, baseline != endpoint
        damage = row.get("observer", {}).get("damage_count", 0) > 0
        if (middle_diff, endpoint_diff, damage) != MATRIX[case]:
            errors.append("frozen_matrix")
        receipt = row.get("observer", {})
        if row.get("native_executable_sha256") != summary.get("native_sha256"):
            errors.append("executable_identity")
        if receipt.get("observer_pid", 0) <= 0 or receipt.get("renderer_middle_pid", 0) == receipt.get("observer_pid"):
            errors.append("observer_renderer_process_separation")
        if row.get("observer_exit") != 0 or receipt.get("renderer_middle_exit") != 0 or receipt.get("renderer_middle_pid", 0) <= 0:
            errors.append("middle_process_exit")
        if case.startswith("ABA_"):
            if receipt.get("renderer_endpoint_exit") != 0 or receipt.get("renderer_endpoint_pid", 0) <= 0:
                errors.append("endpoint_process_exit")
            if receipt.get("renderer_endpoint_pid") in (receipt.get("observer_pid"), receipt.get("renderer_middle_pid")):
                errors.append("endpoint_process_separation")
        elif receipt.get("renderer_endpoint_pid") != 0:
            errors.append("unexpected_endpoint_process")
        if receipt.get("damage_count", 0) and (receipt.get("event_drawable") != receipt.get("window") or not receipt.get("event_drawable")):
            errors.append("event_drawable_identity")
        if receipt.get("damage_count", 0) and (receipt.get("event_damage") != receipt.get("damage_id") or not receipt.get("event_damage")):
            errors.append("event_damage_identity")
        if receipt.get("damage_event_type", -1) < 0 or (receipt.get("damage_count", 0) and receipt.get("event_serial", 0) <= 0):
            errors.append("event_fields")
        if receipt.get("damage_count") != (0 if case == "QUIET" else 1):
            errors.append("damage_count")
        gate = row.get("gate", {})
        if gate.get("endpoint_changed") != endpoint_diff or gate.get("endpoint_forwarded") != endpoint_diff:
            errors.append("gate_endpoint")
        if gate.get("middle_used_by_candidate") is not False or gate.get("action_authority") is not False:
            errors.append("gate_boundary")
        if row.get("damage_disposition") not in ("DAMAGE_OBSERVED", "NO_DAMAGE_OBSERVED_SCOPED", "UNKNOWN"):
            errors.append("typed_disposition")
    xvfb = summary.get("xvfb_exits", [])
    if len(xvfb) != sessions or any(x.get("exit") not in (-15, 0) for x in xvfb):
        errors.append("xvfb_exit")
    return sorted(set(errors))


def corruption_controls(rows, summary, raw):
    rejected = []

    def trial(name, mutate):
        rr, ss, bb = copy.deepcopy(rows), copy.deepcopy(summary), dict(raw)
        mutate(rr, ss, bb)
        if check(rr, ss, bb):
            rejected.append(name)

    trial("missing_row", lambda r, s, b: r.pop())
    trial("duplicate_row", lambda r, s, b: r.append(copy.deepcopy(r[0])))
    trial("altered_pixel", lambda r, s, b: b.__setitem__(r[0]["middle_file"], b[r[0]["middle_file"]][:-1] + bytes([b[r[0]["middle_file"]][-1] ^ 1])))
    trial("wrong_gate", lambda r, s, b: r[0]["gate"].__setitem__("endpoint_forwarded", not r[0]["gate"]["endpoint_forwarded"]))
    trial("wrong_event_drawable", lambda r, s, b: next(x for x in r if x["observer"].get("damage_count", 0))["observer"].__setitem__("event_drawable", 999999))
    trial("missing_renderer_exit", lambda r, s, b: r[0]["observer"].__setitem__("renderer_middle_exit", 9))
    trial("authority_escalation", lambda r, s, b: r[0]["gate"].__setitem__("action_authority", True))
    trial("wrong_image", lambda r, s, b: s.__setitem__("image_id", "sha256:wrong"))
    trial("source_identity", lambda r, s, b: s.__setitem__("source_commit", "invalid"))
    return rejected


def independent_disposition(case, damage_count, endpoint_equal, *, identity_valid, coverage_complete, source_fresh):
    """Auditor's independent implementation of the observation-only status boundary."""
    if not identity_valid or not coverage_complete or not source_fresh:
        return "UNKNOWN", False
    if damage_count > 0:
        return "DAMAGE_OBSERVED", False
    if case == "QUIET" and endpoint_equal:
        return "NO_DAMAGE_OBSERVED_SCOPED", False
    return "UNKNOWN", False


def typed_negative_controls():
    specs = {
        "aba_without_damage": ("ABA_1PX", 0, True, True, True, True),
        "stale_event_identity": ("REPAINT_A", 1, True, False, True, True),
        "incomplete_coverage": ("QUIET", 0, True, True, False, True),
        "stale_source": ("PERSIST_B", 1, False, True, True, False),
        "missing_process_receipt": ("REPAINT_A", 1, True, False, True, True),
    }
    results = {}
    for name, (case, count, equal, identity, coverage, fresh) in specs.items():
        status, authority = independent_disposition(case, count, equal,
            identity_valid=identity, coverage_complete=coverage, source_fresh=fresh)
        results[name] = {"status": status, "action_authority": authority}
    return results


def main(path, source_root=None):
    root = pathlib.Path(path)
    rows = [json.loads(line) for line in (root / "rows.jsonl").read_text().splitlines() if line]
    summary = json.loads((root / "candidate_summary.json").read_text())
    raw = {p.name: p.read_bytes() for p in root.glob("*.rgb")}
    errors = check(rows, summary, raw, source_root)
    rejected = corruption_controls(rows, summary, raw)
    typed = typed_negative_controls()
    if any(v != {"status": "UNKNOWN", "action_authority": False} for v in typed.values()):
        errors.append("typed_negative_controls")
    construction = summary.get("mode") == "construction"
    success = not errors and len(rejected) >= 8
    disposition = ("PASS_CONSTRUCTION_PIPELINE" if construction else "PASS_XDAMAGE_TEMPORAL_BOUNDARY_V3_SCOPED") if success else "HOLD_AUDIT"
    result = {"audit_errors": errors, "control_rejections": rejected, "controls_rejected": len(rejected),
              "controls_required": 8, "typed_negative_controls": typed, "rows": len(rows), "disposition": disposition}
    (root / "audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if success else 1


if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument("results");parser.add_argument("--source-root");args=parser.parse_args()
    raise SystemExit(main(args.results,args.source_root))
