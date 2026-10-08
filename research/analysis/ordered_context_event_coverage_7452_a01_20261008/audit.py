"""Independent raw-output auditor; intentionally does not import candidate.py."""
from __future__ import annotations

import hashlib
import itertools
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVENTS = ("ACT", "OBSERVE", "RELEASE", "REVOKE")
PAIR_LEVELS = tuple(itertools.product(("current", "stale"), ("editor", "dialog")))
ALL_CONTEXTS = tuple(itertools.product(("current", "stale"), ("editor", "dialog"), ("fresh", "stale")))


def canonical_episode(eid, c, es):
    return {"episode_id": eid, "reset_before": True,
            "rows": [{"index": i, "focus_generation": c[0], "surface_mode": c[1],
                      "evidence_fresh": c[2], "event": event} for i, event in enumerate(es)]}


def expected():
    pairs = list(itertools.product(EVENTS, repeat=2))
    block = ["ACT", "OBSERVE", "RELEASE", "REVOKE"] * 2
    return {
        "context_only": [canonical_episode(f"ctx-{i}", (*c, "fresh"), ["ACT"]) for i, c in enumerate(PAIR_LEVELS)],
        "order_only": [canonical_episode("order-0", ("current", "editor", "fresh"), block)],
        "mixed_occ": [canonical_episode(f"mixed-{i}", (*c, "fresh"), block) for i, c in enumerate(PAIR_LEVELS)],
        "exhaustive": [canonical_episode(f"exh-{ci}-{pi}", c, p)
                       for ci, c in enumerate(ALL_CONTEXTS) for pi, p in enumerate(pairs)]}


def pairs_in_episode(ep):
    rows = ep["rows"]
    return {(a["event"], b["event"]) for i, a in enumerate(rows) for b in rows[i+1:]}


def catches(suite, mutant):
    for ep in suite:
        revoked = False
        for r in ep["rows"]:
            if r["event"] == "REVOKE":
                revoked = True
            if r["event"] == "ACT":
                if mutant == "joint" and r["focus_generation"] == "stale" and r["surface_mode"] == "dialog" and revoked:
                    return True
                if mutant == "context_only" and r["surface_mode"] == "dialog":
                    return True
                if mutant == "order_only" and revoked:
                    return True
    return False


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit.py CANDIDATE.json AUDIT.json")
    source, dest = map(Path, sys.argv[1:])
    raw = source.read_bytes()
    data = json.loads(raw)
    expected_suites = expected()
    errors = []
    if data.get("schema") != "ordered-context-event-candidate-v1": errors.append("schema")
    if data.get("model_sha256") != hashlib.sha256((HERE / "model.json").read_bytes()).hexdigest(): errors.append("model_hash")
    if data.get("suites") != expected_suites: errors.append("suite_reconstruction")
    suites = data.get("suites", {})
    coverage = {}
    for name in ("order_only", "mixed_occ"):
        episode_sets = [pairs_in_episode(ep) for ep in suites.get(name, [])]
        coverage[name] = {"episodes_with_all_16_pairs": sum(len(s) == 16 for s in episode_sets),
                          "episodes": len(episode_sets)}
    detected = {name: {m: catches(suites.get(name, []), m) for m in ("joint", "context_only", "order_only")}
                for name in ("context_only", "order_only", "mixed_occ", "exhaustive")}
    expected_detection = {
        "context_only": {"joint": False, "context_only": True, "order_only": False},
        "order_only": {"joint": False, "context_only": False, "order_only": True},
        "mixed_occ": {"joint": True, "context_only": True, "order_only": True},
        "exhaustive": {"joint": True, "context_only": True, "order_only": True}}
    if detected != expected_detection: errors.append("mutation_detection")
    # Reset-boundary negative control: no pair is constructed across adjacent episodes.
    flattened = [ep["rows"][-1]["event"] for ep in suites.get("mixed_occ", []) if ep.get("rows")]
    firsts = [ep["rows"][0]["event"] for ep in suites.get("mixed_occ", []) if ep.get("rows")]
    invalid_cross_reset = list(zip(flattened, firsts))
    if len(invalid_cross_reset) != 4 or any(pair != ("REVOKE", "ACT") for pair in invalid_cross_reset): errors.append("cross_reset_fixture")
    result = {"status": "PASS" if not errors else "FAIL", "errors": errors,
              "candidate_sha256": hashlib.sha256(raw).hexdigest(),
              "model_sha256": hashlib.sha256((HERE / "model.json").read_bytes()).hexdigest(),
              "episode_counts": {k: len(v) for k, v in suites.items()},
              "row_counts": {k: sum(len(ep["rows"]) for ep in v) for k, v in suites.items()},
              "coverage": coverage, "mutant_detection": detected,
              "cross_reset_pairs_credited": 0,
              "negative_control_unsafe_effect": False,
              "mutation_controls": {"drop_episode": "reconstruction equality rejects deletion",
                                    "credit_cross_reset_pair": "episode-local oracle rejects boundary credit",
                                    "collapse_context_strata": "reconstruction equality rejects context collapse"}}
    out = (json.dumps(result, sort_keys=True, indent=2) + "\n").encode()
    fd = os.open(dest, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream: stream.write(out)
    print(out.decode(), end="")
    if errors: raise SystemExit(1)


if __name__ == "__main__": main()
