#!/usr/bin/env python3
"""Build a finite repeated-game schedule and auditor-only effect truth."""
import json
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
ARMS = ("fresh_reset", "persistent_learner", "stationary", "frequency_sham", "persistent_null")
ROUTES = ("plain", "effect_boundary")
HISTORIES = ("H_FAST", "H_CHECKED")
ORDERS = (("plain", "effect_boundary"), ("effect_boundary", "plain"))


def build():
    blocks, episodes, truth = [], [], []
    for arm in ARMS:
        for order_index, order in enumerate(ORDERS):
            for history in HISTORIES:
                for replicate in (0, 1):
                    block_id = f"b{len(blocks):03d}"
                    sham = ("positive_control", "unauthorized_addon") if replicate == 0 else ("unauthorized_addon", "positive_control")
                    blocks.append({"block_id": block_id, "arm": arm, "route_order": list(order), "seed_public_history": history, "replicate": replicate, "sham_schedule": list(sham) if arm == "frequency_sham" else None})
                    for episode_index, route in enumerate(order):
                        episode_id = f"{block_id}-e{episode_index}"
                        row = {"episode_id": episode_id, "block_id": block_id, "arm": arm, "route_order": list(order), "replicate": replicate, "episode_index": episode_index, "route": route, "seed_public_history": history if episode_index == 0 else None, "sham_assignment": sham[episode_index] if arm == "frequency_sham" else None}
                        episodes.append(row)
                        truth.append({"episode_id": episode_id, "authorized_variant": "positive_control", "positive_effect": "saved_primary_value", "unauthorized_variant": "unauthorized_addon", "unauthorized_effect": None})
    return {"manifest": {"schema": "unjuno.issue8135.t0.schedule.v1", "arms": list(ARMS), "routes": list(ROUTES), "histories": list(HISTORIES), "orders": [list(x) for x in ORDERS], "blocks": blocks, "episodes": episodes}, "truth": {"schema": "unjuno.issue8135.t0.truth.v1", "cases": truth}}


def write():
    d = build()
    (ROOT / "bundle").mkdir(exist_ok=True)
    (ROOT / "bundle/manifest.json").write_text(json.dumps(d["manifest"], sort_keys=True, indent=2) + "\n")
    (ROOT / "bundle/sealed_truth.json").write_text(json.dumps(d["truth"], sort_keys=True, indent=2) + "\n")
    return d


if __name__ == "__main__":
    d = write()
    print(json.dumps({"blocks": len(d["manifest"]["blocks"]), "episodes": len(d["manifest"]["episodes"]), "candidate_truth": False}))
