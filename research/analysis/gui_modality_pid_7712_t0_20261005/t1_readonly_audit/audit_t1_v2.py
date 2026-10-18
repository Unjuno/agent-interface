#!/usr/bin/env python3
"""Read-only audit of whether a retained channel bundle can support #7712 T1."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_ARTIFACTS = {
    "full_png.png", "left_roi_png.png", "right_roi_png.png",
    "accessibility_snapshot.txt", "mutation_delta.json",
}
SOURCE_PREFIX = "research/analysis/blackwell_observation_dominance_6678_t1_orbstack_a03_20261003/"


def read_json(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def git_blob_sha(data):
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def main():
    readbacks = read_json("SOURCE_READBACK.json")
    manifest = read_json("source_manifest.json")
    schedule = read_json("source_schedule.json")
    states = read_json("source_states.json")
    freeze = read_json("source_freeze.json")
    prior_audit = read_json("source_original_audit.json")
    report = (ROOT / "source_report.md").read_text(encoding="utf-8")

    blob_checks = []
    for item in readbacks["readbacks"]:
        raw = (ROOT / item["file"]).read_bytes()
        blob_checks.append({"path": item["path"], "expected": item["git_blob_sha"],
                            "observed": git_blob_sha(raw), "pass": git_blob_sha(raw) == item["git_blob_sha"]})
    source_pin_pass = (readbacks["source_commit"] == "c837ad535eed085d95744ad0a9680535a5bb7143"
                       and all(x["pass"] for x in blob_checks)
                       and all(x["path"].startswith(SOURCE_PREFIX) for x in readbacks["readbacks"]))

    expected = schedule.get("captures")
    actual = manifest.get("captures")
    identity_match = (isinstance(expected, list) and isinstance(actual, list)
                      and [(x.get("capture_id"), x.get("state")) for x in actual]
                      == [(x.get("capture_id"), x.get("state")) for x in expected])
    all_groups_complete = bool(identity_match)
    counts_by_state = Counter()
    unique_hashes = {name: set() for name in EXPECTED_ARTIFACTS}
    if isinstance(actual, list):
        for row in actual:
            counts_by_state[row.get("state")] += 1
            artifacts = row.get("artifacts")
            if type(artifacts) is not dict or set(artifacts) != EXPECTED_ARTIFACTS:
                all_groups_complete = False
                continue
            for name, digest in artifacts.items():
                if type(digest) is not str or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                    all_groups_complete = False
                else:
                    unique_hashes[name].add(digest)

    declared_states = {row.get("id") for row in states.get("states", [])}
    balanced_state_coverage = (set(counts_by_state) == declared_states
                               and all(counts_by_state[s] == freeze["protocol"]["captures_per_state"]
                                       for s in declared_states))
    old_audit_pass = (prior_audit.get("disposition") == "PASS_CHANNEL_RECONSTRUCTION_SCOPED"
                      and prior_audit.get("captures_audited") == 72
                      and prior_audit.get("errors") == [])
    paired_state_data = (source_pin_pass and len(actual or []) == freeze["protocol"]["total_captures"]
                         and identity_match and all_groups_complete and balanced_state_coverage
                         and old_audit_pass)

    # State labels and loss matrices are distinct from observed or oracle-labeled
    # next-action/effect outcomes. The fixture lists action tokens, but no row
    # binds an action to a measured effect or declares a gold safe action.
    forbidden_label_fields = {"safe_action", "gold_action", "next_action_label", "effect_label",
                              "observed_effect", "action_outcome"}
    row_fields = set()
    for row in actual or []:
        row_fields.update(row.keys())
    has_effect_target = bool(row_fields & forbidden_label_fields)
    has_authored_losses = isinstance(states.get("decision_problems"), dict)
    effect_target_feasible = has_effect_target
    disposition = ("PASS_T1_TARGET_DATA_FEASIBLE" if paired_state_data and effect_target_feasible
                   else "HOLD_NO_SAFE_ACTION_EFFECT_LABELS" if paired_state_data
                   else "HOLD_PAIRED_SOURCE_EVIDENCE_INCOMPLETE")

    result = {
        "schema": "issue7712_t1_retained_data_feasibility_v2",
        "source_commit": readbacks["source_commit"],
        "source_blob_checks": blob_checks,
        "captures": len(actual or []),
        "captures_per_state": dict(sorted(counts_by_state.items())),
        "channels_per_capture": sorted(EXPECTED_ARTIFACTS),
        "unique_artifact_hashes_per_channel": {k: len(v) for k, v in sorted(unique_hashes.items())},
        "paired_same_capture_modalities": paired_state_data,
        "state_oracle_independent_of_model": "yes; authored fixture RGB/state oracle, no model evaluated",
        "independent_safe_action_or_effect_labels": effect_target_feasible,
        "researcher_authored_loss_matrices_present": has_authored_losses,
        "timestamp_or_capture_epoch_field_in_manifest": any(k in row_fields for k in ("timestamp", "epoch", "capture_ns")),
        "old_audit_scope": "prior raw-only audit record reports 72/72 and zero errors; original 360 artifact bytes not re-downloaded",
        "disposition": disposition,
        "limits": [
            "one authored deterministic static browser fixture; repetitions are technical, not independent GUI samples",
            "capture identity groups the five channel artifacts but no capture timestamp is retained in manifest rows",
            "no independently labeled safe next-action or measured action/effect outcome is present in per-capture rows",
            "loss matrices define hypothetical decision costs; they are not observed action effects",
            "no model, real application, Agent Interface runtime, safety, latency, acquisition-cost, or product inference",
        ],
        "prior_report_mentions_no_action_effect": "No Agent Interface runtime, real application, LLM behavior, user data, action/effect, safety" in report,
    }
    (ROOT / "T1_AUDIT_V2.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": disposition, "captures": len(actual or []),
                      "paired_same_capture_modalities": paired_state_data,
                      "independent_safe_action_or_effect_labels": effect_target_feasible,
                      "source_pins_pass": source_pin_pass}, sort_keys=True))
    if not source_pin_pass or not identity_match or not all_groups_complete or not old_audit_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
