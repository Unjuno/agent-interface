"""Independent raw-only audit for #6509; intentionally imports no candidate code."""
import json
import hashlib
import sys
from pathlib import Path


EXPECTED = {
    "complete-positive": "COMPLETE_ALLOW",
    "complete-negative": "COUNTEREXAMPLE",
    "timeout-after-prefix": "PARTIAL_UNKNOWN",
    "false-scalar-positive": "PARTIAL_UNKNOWN",
    "stale-generation": "PARTIAL_UNKNOWN",
    "dropped-mandatory": "PARTIAL_UNKNOWN",
    "crash-receipt-before-commit": "PARTIAL_UNKNOWN",
    "untrusted-receipt": "PARTIAL_UNKNOWN",
    "contradictory-later-evidence": "PARTIAL_UNKNOWN",
    "external-state-change": "PARTIAL_UNKNOWN",
    "optional-only-progress": "PARTIAL_UNKNOWN",
    "mandatory-complete-optional-missing": "COMPLETE_ALLOW",
}
POLICIES = ("ALL_OR_NOTHING_TIMEOUT", "UNSAFE_SCALAR_PROGRESS", "CLAIM_LADDER")
REQUIRED = ("identity", "freshness", "effect")
SOURCE = "fixture-verifier"
TARGET = "task-6509"
FIXTURE_SHA256 = {
    "complete-negative": "47b30abc036a2637f2a03af4505e95814680415479ea2783ad47e53af877cfbe",
    "complete-positive": "7b3cc2f5412dba59560eef6e10d3fc705775c55cd10b1b7e67d1131dc392c6f7",
    "contradictory-later-evidence": "e6a62265099f9fd81205fdd03725ea97ee946f48a6f1cde84c2df7d4c6b5d719",
    "crash-receipt-before-commit": "574cbfcec1acdc38f05999dc2aa8d6da38df00efa7ed3ac713a53f94deaed449",
    "dropped-mandatory": "e1c72b324088e658c263c597ff4fb17f2b9b8c7570a85b1a04d3256e34c43f16",
    "external-state-change": "acc70078a57bdc517d86196e119c21146776fefc2f02e3964b1fa407af290238",
    "false-scalar-positive": "61af324b8e5270add6bcae85d76e37053cf1aa34b2f8774c133f58d91a3be4e2",
    "mandatory-complete-optional-missing": "8d2f5612ba43f240b9437f2ea64b321a0dc7fed08e3e06b095fa742bef08f0ca",
    "optional-only-progress": "aa78b9fef1a475b2ca931deda85422ef33add76dc730c7a0664ab86a1276a860",
    "stale-generation": "6118cb2d816a882bc9b43964f7a856bb1a1c0f07c4811c1570fe6c1796c73b76",
    "timeout-after-prefix": "9b08d6f95dbe38fa669dc4b005dbe28ed8596ff5588d5cfa25122f75b3d4b32b",
    "untrusted-receipt": "fc0dd7d0678d5b02b1feafcaaaa961e66bd4f4250efa7583472722e3fe3d179f",
}


def independently_derive(row, generation):
    trace = row.get("input", {})
    events = trace.get("events", [])
    trusted = []
    for event in events:
        if not isinstance(event, list) or len(event) != 5:
            return None, "malformed event"
        check, value, event_gen, source_bound, committed = event
        if source_bound is True and committed is True and event_gen == generation:
            trusted.append((check, value))
    values = {}
    for check, value in trusted:
        values.setdefault(check, []).append(value)
    contradiction = any(len(set(items)) > 1 for items in values.values())
    final_generation = trace.get("final_generation", generation)
    full = all(c in values and values[c][-1] in ("PASS", "VIOLATION") for c in REQUIRED)
    early_reject = (values.get("effect", [None])[-1] == "VIOLATION"
                    and len(set(values.get("effect", []))) == 1
                    and final_generation == generation and not contradiction)
    all_positive = full and all(values[c][-1] == "PASS" for c in REQUIRED)
    if row.get("policy") == "UNSAFE_SCALAR_PROGRESS":
        expected = "ALLOW" if trace.get("scalar_progress", 0.0) >= 0.5 else "UNKNOWN"
        completed = [event[0] for event in trusted]
        missing = [c for c in REQUIRED if c not in values]
        return expected, None, completed, missing
    if row.get("policy") == "ALL_OR_NOTHING_TIMEOUT":
        if early_reject:
            return "COUNTEREXAMPLE", None, [], list(REQUIRED)
        if all_positive and final_generation == generation and not contradiction:
            return "COMPLETE_ALLOW", None, [], list(REQUIRED)
        return "TIMEOUT_UNKNOWN", None, [], list(REQUIRED)
    if early_reject:
        disposition = "COUNTEREXAMPLE"
    elif all_positive and final_generation == generation and not contradiction:
        disposition = "COMPLETE_ALLOW"
    else:
        disposition = "PARTIAL_UNKNOWN"
    return disposition, None, sorted({check for check, _ in trusted}), [c for c in REQUIRED if c not in values]


def audit(raw):
    errors = []
    if raw.get("schema") != "claim-ladder-raw-v1":
        errors.append("raw schema mismatch")
    if raw.get("generation") != 7 or raw.get("source") != SOURCE or raw.get("target") != TARGET:
        errors.append("raw contract identity mismatch")
    if raw.get("mandatory") != list(REQUIRED) or raw.get("policies") != list(POLICIES):
        errors.append("raw policy metadata mismatch")
    rows = raw.get("rows", [])
    expected_pairs = {(case, policy) for case in EXPECTED for policy in POLICIES}
    seen = set()
    unsafe_baseline_exposed = False
    for i, row in enumerate(rows):
        pair = (row.get("trace_id"), row.get("policy"))
        if pair in seen:
            errors.append(f"row {i}: duplicate pair {pair}")
        seen.add(pair)
        input_trace = row.get("input", {})
        trace_id = row.get("trace_id")
        if trace_id not in FIXTURE_SHA256 or input_trace.get("id") != trace_id:
            errors.append(f"row {i}: unknown or mismatched frozen trace identity")
        else:
            digest = hashlib.sha256(json.dumps(input_trace, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            if digest != FIXTURE_SHA256[trace_id]:
                errors.append(f"row {i}: trace differs from frozen fixture")
        derived, err, completed, missing = independently_derive(row, 7)
        if err:
            errors.append(f"row {i}: {err}")
            continue
        actual = row.get("result", {}).get("disposition")
        if actual != derived:
            errors.append(f"row {i}: disposition {actual!r} != independently derived {derived!r}")
        result = row.get("result", {})
        if result.get("completed") != completed:
            errors.append(f"row {i}: completed-check list mismatch")
        if result.get("missing") != missing:
            errors.append(f"row {i}: missing-check list mismatch")
        if result.get("authority") is not (actual in ("ALLOW", "COUNTEREXAMPLE", "COMPLETE_ALLOW")):
            errors.append(f"row {i}: authority bit inconsistent with disposition")
        if row.get("policy") == "CLAIM_LADDER":
            expected = EXPECTED.get(row.get("trace_id"))
            if actual != expected:
                errors.append(f"row {i}: claim-ladder disposition violates case oracle")
            if actual == "PARTIAL_UNKNOWN" and row.get("result", {}).get("authority") is not False:
                errors.append(f"row {i}: partial result carries authority")
        if row.get("policy") == "UNSAFE_SCALAR_PROGRESS" and actual == "ALLOW" and row.get("trace_id") in (
                "false-scalar-positive", "dropped-mandatory", "optional-only-progress"):
            unsafe_baseline_exposed = True
    if seen != expected_pairs:
        errors.append(f"denominator mismatch missing={sorted(expected_pairs-seen)} extra={sorted(seen-expected_pairs)}")
    if not unsafe_baseline_exposed:
        errors.append("unsafe scalar negative control did not expose a partial-positive ALLOW")
    return {"status": "METHOD_PASS_SCOPED" if not errors else "FAIL_METHOD",
            "rows": len(rows), "errors": errors,
            "unsafe_scalar_baseline_exposed": unsafe_baseline_exposed,
            "scope": "finite synthetic protocol only; no GUI timing or authorization claim"}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: auditor.py RAW_JSON REPORT_JSON")
    raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    report = audit(raw)
    Path(sys.argv[2]).write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                                 encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if report["status"] == "METHOD_PASS_SCOPED" else 1)
