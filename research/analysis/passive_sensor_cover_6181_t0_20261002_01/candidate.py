#!/usr/bin/env python3
"""Finite exhaustive passive-sensor cover candidate; stdlib only."""
import argparse
import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path

MAIN_SHA = "69a1bf509eb432e5e3c0c294d05ad7671d86adb6"
NO_COVER = "NO_SUFFICIENT_PASSIVE_COVER"


def pair_key(a, b):
    return [a, b]


def required_pairs(fixture):
    states = sorted(fixture["states"], key=lambda x: x["id"])
    return [pair_key(a["id"], b["id"]) for a, b in itertools.combinations(states, 2)
            if a["required_response"] != b["required_response"]]


def valid_value(channel, state):
    obs = channel.get("observations", {}).get(state["id"])
    if not isinstance(obs, dict):
        return None
    if obs.get("status") != "CURRENT":
        return None
    if obs.get("generation") != state.get("expected_generation"):
        return None
    if "value" not in obs or obs["value"] is None:
        return None
    return obs["value"]


def assess(fixture, selected, dropped=()):
    selected = tuple(sorted(selected))
    channels = {c["id"]: c for c in fixture["channels"]}
    mandatory = sorted(c["id"] for c in fixture["channels"] if c.get("mandatory"))
    missing_mandatory = [x for x in mandatory if x not in selected]
    dropped = set(dropped)
    by_state = {s["id"]: s for s in fixture["states"]}
    unresolved = []
    for a_id, b_id in required_pairs(fixture):
        separated = False
        for name in selected:
            ch = channels[name]
            if ch["producer"] in dropped:
                continue
            a = valid_value(ch, by_state[a_id])
            b = valid_value(ch, by_state[b_id])
            if a is not None and b is not None and a != b:
                separated = True
                break
        if not separated:
            unresolved.append([a_id, b_id])
    ok = not missing_mandatory and not unresolved
    return {
        "status": "COVER" if ok else NO_COVER,
        "cost": sum(channels[x]["cost"] for x in selected),
        "channels": list(selected),
        "missing_mandatory": missing_mandatory,
        "unresolved_pairs": unresolved,
    }


def all_subsets(fixture):
    names = sorted(c["id"] for c in fixture["channels"])
    return [assess(fixture, combo) for n in range(len(names) + 1)
            for combo in itertools.combinations(names, n)]


def greedy(fixture):
    channels = {c["id"]: c for c in fixture["channels"]}
    selected = sorted(c["id"] for c in fixture["channels"] if c.get("mandatory"))
    while True:
        current = assess(fixture, selected)
        if current["status"] == "COVER":
            return {"status": "COVER", "channels": selected, "cost": current["cost"]}
        unresolved_now = {tuple(x) for x in current["unresolved_pairs"]}
        choices = []
        for name, ch in channels.items():
            if name in selected:
                continue
            nxt = assess(fixture, selected + [name])
            gain = len(unresolved_now - {tuple(x) for x in nxt["unresolved_pairs"]})
            if gain:
                choices.append((Fraction(gain, ch["cost"]), name))
        if not choices:
            return {"status": NO_COVER, "channels": selected, "cost": assess(fixture, selected)["cost"]}
        best_score = max(x[0] for x in choices)
        pick = min(name for score, name in choices if score == best_score)
        selected.append(pick)
        selected.sort()


def minimum_cover(fixture):
    covers = [x for x in all_subsets(fixture) if x["status"] == "COVER"]
    if not covers:
        return {"status": NO_COVER, "channels": [], "cost": None, "minimum_tie_count": 0, "cover_count": 0}
    winner = min(covers, key=lambda x: (x["cost"], len(x["channels"]), x["channels"]))
    tied = [x for x in covers if (x["cost"], len(x["channels"])) ==
            (winner["cost"], len(winner["channels"]))]
    return {
        "status": "COVER",
        "channels": winner["channels"],
        "cost": winner["cost"],
        "minimum_tie_count": len(tied),
        "cover_count": len(covers),
    }


def solve(fixture):
    rows = all_subsets(fixture)
    names = sorted(c["id"] for c in fixture["channels"])
    minimum = minimum_cover(fixture)
    selected = minimum["channels"] if minimum["status"] == "COVER" else []
    selected_producers = sorted({next(c["producer"] for c in fixture["channels"] if c["id"] == n)
                                 for n in selected})
    drop = {p: assess(fixture, selected, dropped=[p]) for p in selected_producers}
    full = assess(fixture, names)
    screenshot = assess(fixture, ["screenshot"],)
    impossible = json.loads(json.dumps(fixture))
    by_channel = {c["id"]: c for c in impossible["channels"]}
    by_channel["app_status"]["observations"]["S2"]["value"] = "effect_uncertain"
    by_channel["app_status"]["observations"]["S3"]["value"] = "effect_uncertain"
    return {
        "all_subsets": rows,
        "minimum": minimum,
        "greedy": greedy(fixture),
        "full_bundle": full,
        "screenshot_only": screenshot,
        "producer_dropout_from_minimum": drop,
        "impossible_effect_alias": minimum_cover(impossible),
        "impossible_control_subset_count": len(all_subsets(impossible)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    raw = args.fixture.read_bytes()
    fixture = json.loads(raw)
    result = {
        "schema": "passive-sensor-cover-candidate-v1",
        "main_sha": MAIN_SHA,
        "fixture_sha256": hashlib.sha256(raw).hexdigest(),
        "producer_by_channel": {c["id"]: c["producer"] for c in fixture["channels"]},
        "analysis": solve(fixture),
    }
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
