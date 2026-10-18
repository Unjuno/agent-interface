"""No-model schedule harness for companion Issue #8406 T0."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

ARMS = ("episodic_only", "per_episode", "batch_2", "terminal")
QUERY_IDS = ("q_common_save", "q_rare_exception", "q_conflict", "q_history_delta", "q_heldout_conjunction")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def ledger_digest(episodes):
    return hashlib.sha256(canonical(episodes)).hexdigest()


def consolidate(episodes):
    ids = {episode["id"] for episode in episodes}
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


def build(model):
    episodes = copy.deepcopy(model["episodes"])
    full_digest = ledger_digest(episodes)
    histories = {arm: [] for arm in ARMS}
    applied_updates = {arm: 0 for arm in ARMS}
    for prefix in model["checkpoints"]:
        prefix_episodes = episodes[:prefix]
        prefix_ids = [episode["id"] for episode in prefix_episodes]
        for arm in ARMS:
            if arm == "episodic_only":
                update = False
                last_prefix = 0
                claims = []
                pending = prefix_ids
            elif arm == "per_episode":
                update = True
                last_prefix = prefix
                claims = consolidate(prefix_episodes)
                pending = []
            elif arm == "batch_2":
                update = prefix % model["batch_size"] == 0
                last_prefix = prefix if update else prefix - 1
                committed = (prefix_episodes if update else episodes[:last_prefix])
                claims = consolidate(committed)
                pending = [e["id"] for e in episodes[last_prefix:prefix]]
            else:
                update = prefix == len(episodes)
                last_prefix = prefix if update else 0
                claims = consolidate(prefix_episodes) if update else []
                pending = prefix_ids if not update else []
            if update:
                applied_updates[arm] += 1
            histories[arm].append({
                "checkpoint": prefix,
                "processed_episode_ids": prefix_ids,
                "prefix_sha256": ledger_digest(prefix_episodes),
                "ledger_sha256": full_digest,
                "query_ids": list(model["query_ids"]),
                "query_budget": model["query_budget"],
                "update_applied": update,
                "updates_applied_total": applied_updates[arm],
                "last_consolidated_prefix": last_prefix,
                "pending_episode_ids": pending,
                "derived_memory": claims,
            })
    return {
        "allocation": model["allocation"],
        "model_sha256": hashlib.sha256(canonical(model)).hexdigest(),
        "episodes": episodes,
        "arm_order": list(ARMS),
        "checkpoint_histories": histories,
        "update_totals": applied_updates,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    model_bytes = Path(args.model).read_bytes()
    model = json.loads(model_bytes)
    result = build(model)
    result["model_file_sha256"] = hashlib.sha256(model_bytes).hexdigest()
    output = Path(args.output)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        stream.write("\n")
    print("candidate emitted 24 checkpoint snapshots across four schedules")


if __name__ == "__main__":
    main()
