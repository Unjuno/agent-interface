import hashlib
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
freeze_bytes = (root / "FREEZE.json").read_bytes()
freeze = json.loads(freeze_bytes.decode("utf-8-sig"))
raw_bytes = (root / "candidate-output.json").read_bytes()
raw = json.loads(raw_bytes.decode("utf-8-sig"))
prior = freeze["prior_attempt"]["id"]
original_id = raw.get("experiment")
if original_id != prior:
    raise RuntimeError("raw identity mismatch is not the declared A01 carryover; retain as STOP")
if freeze["prior_attempt"]["disposition"] != "STOP_HARNESS_ERROR":
    raise RuntimeError("prior A01 STOP reference changed")
derived = dict(raw)
derived["experiment"] = freeze["experiment"]
derived["posthoc_identity_repair"] = {
    "original_candidate_output_experiment": original_id,
    "source_candidate_output_sha256": hashlib.sha256(raw_bytes).hexdigest(),
    "method": "copy candidate output and replace only the experiment label with the frozen A02 identity",
    "no_candidate_rerun": True
}
(root / "RESULT_POSTHOC.json").write_text(
    json.dumps(derived, indent=2, sort_keys=True) + "\n", encoding="utf-8")

source_bytes = (root / freeze["source_path"]).read_bytes()
probe_bytes = (root / freeze["probe_path"]).read_bytes()
checks = {
    "source_hash_and_size_match_freeze": (
        hashlib.sha256(source_bytes).hexdigest() == freeze["source_sha256"] and
        len(source_bytes) == freeze["source_bytes"]),
    "probe_hash_and_size_match_freeze": (
        hashlib.sha256(probe_bytes).hexdigest() == freeze["probe_sha256"] and
        len(probe_bytes) == freeze["probe_bytes"]),
    "raw_output_has_declared_prior_id": original_id == prior,
    "raw_output_id_matches_a02_freeze": original_id == freeze["experiment"],
    "derived_result_id_matches_a02_freeze": derived["experiment"] == freeze["experiment"],
    "normalization_changes_only_id_and_adds_provenance": (
        {k: v for k, v in derived.items() if k not in ("experiment", "posthoc_identity_repair")} ==
        {k: v for k, v in raw.items() if k != "experiment"}),
}
case_checks = {}
for name, case in raw.get("cases", {}).items():
    events, outs = case.get("events", []), case.get("outcomes", [])
    if len(events) != 2 or len(outs) != 2 or outs[0] is not None:
        case_checks[name] = False
        continue
    first, second = events
    same_epoch = first.get("sequence") == second.get("sequence") and first.get("capture_ns") == second.get("capture_ns")
    transport_changed = first.get("event") != second.get("event")
    same_payload = (first.get("signals") == second.get("signals") and
                    first.get("pointer_binding") == second.get("pointer_binding"))
    same_hash = first.get("frame_rgb_sha256") == second.get("frame_rgb_sha256")
    if same_epoch and transport_changed:
        expected = "PRESERVE" if same_payload and same_hash else "signal_pair_duplicate_epoch_mismatch"
    elif second.get("sequence", 0) > first.get("sequence", 0) and second.get("capture_ns", 0) > first.get("capture_ns", 0):
        expected = "PRESERVE"
    else:
        expected = "UNEXPECTED_CASE_SHAPE"
    actual = outs[1]
    actual_label = "PRESERVE" if actual is None else actual.get("reason", actual.get("event"))
    case_checks[name] = actual_label == expected
checks["three_raw_cases_independently_reconstructed"] = len(case_checks) == 3 and all(case_checks.values())
checks["raw_candidate_reports_expected_case_checks"] = raw.get("status") == "PASS_SYNTHETIC_BOUNDARY" and all(raw.get("checks", {}).values())
checks["live_scope_not_claimed"] = (
    "no game" in raw.get("scope", "").lower() or "no doom" in raw.get("scope", "").lower())

audit = {
    "status": "PASS_OUTCOME_RECONSTRUCTION_WITH_PROVENANCE_DEVIATION"
              if all(v for k, v in checks.items() if k != "raw_output_id_matches_a02_freeze")
              and checks["raw_output_id_matches_a02_freeze"] is False
              else "FAIL_POSTHOC_RECONSTRUCTION",
    "checks": checks,
    "derived_case_checks": case_checks,
    "deviation": "Raw candidate output embeds the prior A01 ID instead of the frozen A02 ID. Raw bytes and the initial unbound audit are preserved; RESULT_POSTHOC.json changes only that identity field and labels the derivation.",
    "scope": "Posthoc saved-data reconstruction only; no candidate rerun, live threat semantics, or gameplay claim."
}
(root / "AUDIT_POSTHOC.json").write_text(
    json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(audit, indent=2, sort_keys=True))
if audit["status"] != "PASS_OUTCOME_RECONSTRUCTION_WITH_PROVENANCE_DEVIATION":
    raise SystemExit(1)
