"""Independent raw-only audit for companion Issue #8406; no candidate imports."""
import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_ALLOCATION = "GUI-MEMORY-CONSOLIDATION-SCHEDULE-8406-T0-A01-20261008"
EXPECTED_MODEL_FILE_SHA256 = "b0038e69f5febf785e461d0ddff0d26277c1de7f9b967632e789b9491aa387fa"
EXPECTED_QUERIES = ["q_common_save", "q_rare_exception", "q_conflict", "q_history_delta", "q_heldout_conjunction"]
EXPECTED_BUDGET = {"queries_per_checkpoint": 5, "model_calls": 0, "model_visible_token_budget": 0}
ARM_ORDER = ["episodic_only", "per_episode", "batch_2", "terminal"]

# This truth set is intentionally authored in the auditor rather than imported
# from candidate.py or loaded from the candidate's model path.
EPISODES = [
    {"id":"ep01","source_ids":["src-01"],"kind":"common_success","context":{"app":"editor","mode":"draft","surface":"standard"},"action":"save","exact_effect":"draft_saved","verification":"verified"},
    {"id":"ep02","source_ids":["src-02"],"kind":"common_success","context":{"app":"editor","mode":"draft","surface":"standard"},"action":"save","exact_effect":"draft_saved","verification":"verified"},
    {"id":"ep03","source_ids":["src-03"],"kind":"rare_exception","context":{"app":"editor","mode":"publish","surface":"standard"},"action":"withhold_publish","exact_effect":"no_external_effect","forbidden_effect":"publish","verification":"verified"},
    {"id":"ep04","source_ids":["src-04"],"kind":"fact_observation","fact_key":"revision-r7-mode","value":"draft","verification":"verified"},
    {"id":"ep05","source_ids":["src-05"],"kind":"fact_observation","fact_key":"revision-r7-mode","value":"published","verification":"verified"},
    {"id":"ep06","source_ids":["src-06-baseline","src-06-current"],"kind":"history_pair","baseline":{"mode":"draft","source_id":"src-06-baseline"},"current":{"mode":"published","source_id":"src-06-current"},"version":"revision-r8","verification":"verified"},
]


def digest(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def expected_claims(processed_ids):
    ids = set(processed_ids)
    claims = []
    if {"ep01", "ep02"} <= ids:
        claims.append({"id":"common_save_pattern","kind":"verified_pattern","context":{"app":"editor","mode":"draft","surface":"standard"},"action":"save","effect":"draft_saved","source_episode_ids":["ep01","ep02"],"source_ids":["src-01","src-02"]})
    if "ep03" in ids:
        claims.append({"id":"rare_publish_exception","kind":"forbidden_effect_exception","context":{"app":"editor","mode":"publish","surface":"standard"},"forbidden_effect":"publish","disposition":"retain_exception","source_episode_ids":["ep03"],"source_ids":["src-03"]})
    if {"ep04", "ep05"} <= ids:
        claims.append({"id":"revision_r7_mode","kind":"conflict","value":"UNKNOWN","source_episode_ids":["ep04","ep05"],"source_ids":["src-04","src-05"]})
    if "ep06" in ids:
        claims.append({"id":"revision_r8_mode_delta","kind":"history_delta","before":"draft","after":"published","source_episode_ids":["ep06"],"source_ids":["src-06-baseline","src-06-current"]})
    return claims


def expected_snapshot(arm, prefix):
    prefix_ids = [episode["id"] for episode in EPISODES[:prefix]]
    if arm == "episodic_only":
        update, last, claims, pending = False, 0, [], prefix_ids
    elif arm == "per_episode":
        update, last, claims, pending = True, prefix, expected_claims(prefix_ids), []
    elif arm == "batch_2":
        update = prefix % 2 == 0
        last = prefix if update else prefix - 1
        committed_ids = [episode["id"] for episode in EPISODES[:last]]
        claims = expected_claims(committed_ids)
        pending = [episode["id"] for episode in EPISODES[last:prefix]]
    else:
        update = prefix == len(EPISODES)
        last = prefix if update else 0
        claims = expected_claims(prefix_ids) if update else []
        pending = [] if update else prefix_ids
    update_count = {
        "episodic_only": 0,
        "per_episode": prefix,
        "batch_2": prefix // 2,
        "terminal": 1 if prefix == len(EPISODES) else 0,
    }[arm]
    return {
        "checkpoint": prefix,
        "processed_episode_ids": prefix_ids,
        "prefix_sha256": digest(EPISODES[:prefix]),
        "ledger_sha256": digest(EPISODES),
        "query_ids": EXPECTED_QUERIES,
        "query_budget": EXPECTED_BUDGET,
        "update_applied": update,
        "updates_applied_total": update_count,
        "last_consolidated_prefix": last,
        "pending_episode_ids": pending,
        "derived_memory": claims,
    }


def audit(raw):
    errors = []
    if raw.get("allocation") != EXPECTED_ALLOCATION:
        errors.append("allocation mismatch")
    if raw.get("model_file_sha256") != EXPECTED_MODEL_FILE_SHA256:
        errors.append("input model bytes mismatch")
    if raw.get("episodes") != EPISODES:
        errors.append("immutable episode corpus mismatch or mutation")
    if raw.get("arm_order") != ARM_ORDER:
        errors.append("arm order mismatch")
    if raw.get("model_sha256") != digest({
        "allocation": EXPECTED_ALLOCATION,
        "query_ids": EXPECTED_QUERIES,
        "query_budget": EXPECTED_BUDGET,
        "batch_size": 2,
        "checkpoints": [1, 2, 3, 4, 5, 6],
        "episodes": EPISODES,
    }):
        errors.append("canonical model identity mismatch")
    histories = raw.get("checkpoint_histories")
    if not isinstance(histories, dict) or set(histories) != set(ARM_ORDER):
        return errors + ["arm history universe mismatch"]
    if raw.get("update_totals") != {"episodic_only": 0, "per_episode": 6, "batch_2": 3, "terminal": 1}:
        errors.append("schedule update totals mismatch")
    for arm in ARM_ORDER:
        states = histories.get(arm)
        if not isinstance(states, list) or len(states) != 6:
            errors.append(f"{arm}: checkpoint count mismatch")
            continue
        for prefix, state in enumerate(states, start=1):
            if state != expected_snapshot(arm, prefix):
                errors.append(f"{arm} checkpoint {prefix}: state/claim/provenance/schedule mismatch")
    # Guard semantic controls explicitly, even when a future fixture changes its row shape.
    for arm in ARM_ORDER:
        for state in histories.get(arm, []):
            claims = state.get("derived_memory", [])
            if any(claim.get("id") == "heldout_conjunction" for claim in claims):
                errors.append(f"{arm}: unsupported conjunction was inferred")
            conflict = next((c for c in claims if c.get("id") == "revision_r7_mode"), None)
            if conflict and conflict.get("value") != "UNKNOWN":
                errors.append(f"{arm}: contradiction silently resolved")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    raw = json.loads(Path(args.raw).read_text(encoding="utf-8"))
    errors = audit(raw)
    report = {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL", "arms": len(raw.get("checkpoint_histories", {})), "snapshots": sum(len(v) for v in raw.get("checkpoint_histories", {}).values() if isinstance(v, list)), "errors": errors}
    with Path(args.output).open("x", encoding="utf-8") as stream:
        json.dump(report, stream, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        stream.write("\n")
    print(json.dumps(report, sort_keys=True, ensure_ascii=False))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
