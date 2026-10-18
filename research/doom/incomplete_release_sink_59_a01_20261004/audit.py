"""Independent raw-only audit for the incomplete publication probe."""
import hashlib
import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parent
EXPECTED = {
    "main": "a9e109f07dbfdefbf33e87840528c4e24195b2d435782d92f0880049721d0b7d",
    "pr7635": "ee4872770ad4f3009883e6472e59c6584d3f1b3bed145b9bee7cefc8ad13e834",
}
raw = json.loads((ROOT / "raw/RAW.json").read_text())
errors = []
cases = raw.get("cases")
if not isinstance(cases, list) or len(cases) != 4:
    errors.append("expected four frozen source/acceptance cases")
else:
    seen = set()
    for case in cases:
        key = (case.get("source"), case.get("sink_accept_before_raise"))
        if key in seen:
            errors.append(f"duplicate case: {key}")
        seen.add(key)
        source = ROOT / "source_snapshots" / str(case.get("source")) / "doom_owner_thread_release_batch_backend_v1.py"
        actual_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        if actual_hash != EXPECTED.get(case.get("source")) or case.get("source_sha256") != actual_hash:
            errors.append(f"source hash mismatch: {key}")
        if case.get("attempt_positions") != [0, 1]:
            errors.append(f"unexpected retry/attempt positions: {key}")
        delivered = [0, 1] if case.get("sink_accept_before_raise") else [0]
        if case.get("delivered_positions") != delivered:
            errors.append(f"injected sink acceptance mismatch: {key}")
        if case.get("publication_metadata") is not None:
            errors.append(f"unexpected structured metadata: {key}")
        if case.get("context_rows_after") != []:
            errors.append(f"buffer was not cleared: {key}")
        if case.get("original_error_text") != "original step failure":
            errors.append(f"original step error changed: {key}")
        if not case.get("error_notes") or "OSError" not in case["error_notes"][0]:
            errors.append(f"sink boundary not noted: {key}")

result = {
    "schema": "incomplete-release-publication-audit-v1",
    "audited_cases": len(cases) if isinstance(cases, list) else 0,
    "independently_derived_sink_oracle": {
        "confirmed_before_failure": [0],
        "delivery_unknown_at_failure": [1],
        "not_attempted_after_failure": [2],
    },
    "disposition": "FAIL_INCOMPLETE_PUBLICATION_CUSTODY" if not errors else "FAIL_AUDIT",
    "errors": errors,
    "scope": "Raw-only deterministic backend-boundary audit; no runtime sink, executor, game, model, GUI, or OS input.",
}
(ROOT / "raw/AUDIT.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
if errors:
    raise SystemExit(1)
