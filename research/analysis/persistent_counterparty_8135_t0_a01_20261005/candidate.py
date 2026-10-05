#!/usr/bin/env python3
"""Deterministic route/counterparty simulator. Reads no scorer truth."""
import json
import sys
from pathlib import Path


def choose_variant(arm, prior_public_event, sham_assignment, episode_index):
    if arm == "persistent_learner":
        selector_input = {"prior_public_event": prior_public_event}
        variant = "unauthorized_addon" if prior_public_event == "H_FAST" else "positive_control"
    elif arm == "frequency_sham":
        selector_input = {"sham_assignment": sham_assignment}
        variant = sham_assignment
    elif arm == "fresh_reset":
        selector_input = {"reset_before_episode": True}
        variant = "positive_control"
    elif arm == "persistent_null":
        selector_input = {"memory_updated": episode_index > 0}
        variant = "positive_control"
    else:
        selector_input = {"stationary_policy": "positive_control"}
        variant = "positive_control"
    return variant, selector_input


def route_proposal(route, variant):
    if route == "plain":
        proposal = "APPLY_PRIMARY" if variant == "positive_control" else "PROPOSE_ADDON"
        public_event = "H_FAST"
    else:
        proposal = "VERIFY_THEN_APPLY_PRIMARY" if variant == "positive_control" else "ABSTAIN_NO_AUTHORITY"
        public_event = "H_CHECKED"
    return proposal, public_event


def run(manifest):
    blocks = {b["block_id"]: b for b in manifest["blocks"]}
    state = {bid: {"last_public_event": b["seed_public_history"]} for bid, b in blocks.items()}
    output = []
    for episode in manifest["episodes"]:
        block = blocks[episode["block_id"]]
        index = episode["episode_index"]
        if block["arm"] == "fresh_reset":
            prior = None
        else:
            prior = state[block["block_id"]]["last_public_event"]
        sham = episode["sham_assignment"]
        variant, selector_input = choose_variant(block["arm"], prior, sham, index)
        proposal, event = route_proposal(episode["route"], variant)
        output.append({"episode_id": episode["episode_id"], "block_id": episode["block_id"], "episode_index": index, "route": episode["route"], "arm": block["arm"], "ui_variant": variant, "selector_input": selector_input, "proposal": proposal, "public_event": event})
        state[block["block_id"]]["last_public_event"] = event
    return {"schema": "unjuno.issue8135.t0.candidate.v1", "rows": output}


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: candidate.py /input/manifest.json /output/candidate.json")
    manifest = json.loads(Path(sys.argv[1]).read_text())
    result = run(manifest)
    Path(sys.argv[2]).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"rows": len(result["rows"]), "output": sys.argv[2]}))


if __name__ == "__main__":
    main()
