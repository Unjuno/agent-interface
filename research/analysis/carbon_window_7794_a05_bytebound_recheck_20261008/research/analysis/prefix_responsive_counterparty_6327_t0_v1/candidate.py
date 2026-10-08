"""No-model finite counterparty selector/agent-route simulator for Issue #6327."""
import hashlib
import json
import sys
from pathlib import Path


def _variant(policy, index, public_prefix, fixture, calibration):
    if policy == "STATIC_BALANCED":
        return fixture["static_balanced_schedule"][index]
    if policy == "FREQUENCY_MATCHED_REPLAY":
        return calibration["schedule"][index]
    if policy == "REACTIVE_DECLARED":
        return "V1" if public_prefix == "declined_addon" else "V0"
    return fixture["null_layout_schedule"][index]


def _simulate(fixture, calibration, calibration_sha256):
    rows = []
    episodes = fixture["offered_episodes"]
    for policy in fixture["selector_policies"]:
        for route in fixture["routes"]:
            for index, episode in enumerate(episodes):
                selected = _variant(policy, index, episode["public_prefix"], fixture, calibration)
                if policy == "REACTIVE_NULL":
                    semantics = fixture["null_layout_semantics"][selected]
                    presentation = {"layout": selected, "primary_choice": semantics}
                else:
                    presentation = fixture["variants"][selected]
                    semantics = presentation["primary_choice"]
                if semantics == "purchase:addon-01" and episode["public_prefix"] == "declined_addon":
                    proposal = "purchase:addon-01"
                else:
                    proposal = "save:document-01"
                if proposal in fixture["task"]["forbidden_effects"] and route == "effect_boundary":
                    gate = "REFUSED_UNAUTHORIZED"
                    effect = None
                else:
                    gate = "ADMITTED"
                    effect = proposal
                correct = effect == "save:document-01"
                if policy in ("STATIC_BALANCED", "FREQUENCY_MATCHED_REPLAY"):
                    visible = ["episode_slot", "stage"]
                    selector_input = {"episode_slot": index, "stage": fixture["stage"]}
                elif policy == "REACTIVE_DECLARED":
                    visible = ["public_prefix", "stage"]
                    selector_input = {"public_prefix": episode["public_prefix"], "stage": fixture["stage"]}
                else:
                    visible = ["public_prefix", "stage"]
                    selector_input = {"public_prefix": episode["public_prefix"], "stage": fixture["stage"]}
                rows.append({
                    "episode_id": episode["id"], "task_id": fixture["task"]["task_id"],
                    "assigned_policy_before_prefix": True, "policy": policy, "route": route,
                    "public_prefix": episode["public_prefix"], "selector_stage": fixture["stage"],
                    "selector_input_keys": visible, "selector_input": selector_input,
                    "calibration_source": calibration["id"] if policy == "FREQUENCY_MATCHED_REPLAY" else None,
                    "calibration_sha256": calibration_sha256 if policy == "FREQUENCY_MATCHED_REPLAY" else None,
                    "variant": selected, "variant_truth_id": fixture["task"]["task_id"] if policy == "REACTIVE_NULL" else presentation["truth_id"],
                    "target_id": fixture["task"]["target_id"],
                    "authorized_effects": fixture["task"]["authorized_effects"],
                    "forbidden_effects": fixture["task"]["forbidden_effects"],
                    "proposal": proposal, "gate": gate, "actual_effect": effect,
                    "unauthorized_effect": effect in fixture["task"]["forbidden_effects"] if effect else False,
                    "authorized_completion": correct,
                    "outcome_label": "AUTHORIZED_SAVE" if correct else ("UNAUTHORIZED_ADDON" if effect else "REFUSED_INCOMPLETE"),
                })
    metrics = {}
    for policy in fixture["selector_policies"]:
        for route in fixture["routes"]:
            group = [r for r in rows if r["policy"] == policy and r["route"] == route]
            metrics[f"{policy}:{route}"] = {
                "offered": len(group),
                "variant_counts": {v: sum(r["variant"] == v for r in group) for v in sorted({r["variant"] for r in group})},
                "unauthorized_effects": sum(r["unauthorized_effect"] for r in group),
                "unauthorized_proposals": sum(r["proposal"] in fixture["task"]["forbidden_effects"] for r in group),
                "authorized_completions": sum(r["authorized_completion"] for r in group),
                "refused_incomplete": sum(r["outcome_label"] == "REFUSED_INCOMPLETE" for r in group),
            }
    return {"schema": "prefix-responsive-counterparty-6327-raw-v1",
            "fixture_id": fixture["schema"], "rows": rows, "metrics": metrics}


if __name__ == "__main__":
    calibration_bytes = Path(sys.argv[2]).read_bytes()
    calibration = json.loads(calibration_bytes)
    print(json.dumps(_simulate(json.loads(Path(sys.argv[1]).read_text()), calibration,
                               hashlib.sha256(calibration_bytes).hexdigest()),
                     sort_keys=True, separators=(",", ":")))
