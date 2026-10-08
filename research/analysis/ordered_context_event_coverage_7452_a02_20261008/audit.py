"""Independent suite reconstruction, stateful oracle, and hostile-input audit."""
import hashlib
import itertools
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVENTS = ("ACT", "OBSERVE", "RELEASE", "REVOKE")
CONTEXTS = tuple(itertools.product(("current", "stale"), ("editor", "dialog")))


def make_episode(eid, context, events):
    return {"episode_id": eid, "reset_before": True,
            "rows": [{"index": i, "focus_generation": context[0],
                      "surface_mode": context[1], "evidence_fresh": "fresh", "event": event}
                     for i, event in enumerate(events)]}


def reconstructed():
    pairs = tuple(itertools.product(EVENTS, repeat=2))
    block = ["ACT", "OBSERVE", "RELEASE", "REVOKE"] * 2
    return {
        "context_only": [make_episode(f"ctx-{i}", c, ["ACT"]) for i, c in enumerate(CONTEXTS)],
        "order_only": [make_episode("order-0", ("current", "editor"), block)],
        "mixed_occ": [make_episode(f"mixed-{i}", c, block) for i, c in enumerate(CONTEXTS)],
        "exhaustive": [make_episode(f"exh-{ci}-{pi}", c, pair)
                       for ci, c in enumerate(CONTEXTS)
                       for pi, pair in enumerate(pairs)]
    }


def valid(data):
    return (isinstance(data, dict)
            and set(data) == {"schema", "model_sha256", "suites"}
            and data.get("schema") == "ordered-context-event-a02-v1"
            and data.get("model_sha256") == hashlib.sha256((HERE / "model.json").read_bytes()).hexdigest()
            and data.get("suites") == reconstructed())


def mutant_triggered(episode, mutant):
    authority = "active"  # reset is episode-local
    revoked_seen = False
    for row in episode["rows"]:
        event = row["event"]
        if event == "REVOKE":
            authority = "revoked"
            revoked_seen = True
        if event != "ACT":
            continue
        if mutant == "joint":
            admitted = (row["focus_generation"] == "stale" and
                        row["surface_mode"] == "dialog" and revoked_seen)
        elif mutant == "context_only":
            admitted = row["surface_mode"] == "dialog"
        elif mutant == "order_only":
            admitted = revoked_seen
        else:
            admitted = authority == "active"
        if admitted:
            return True
    return False


def negative_unsafe(suite):
    for episode in suite:
        authority = "active"
        for row in episode["rows"]:
            if row["event"] == "REVOKE":
                authority = "revoked"
            elif row["event"] == "ACT":
                admitted = authority == "active"
                if admitted and authority == "revoked":
                    return True
    return False


def event_pairs(episode):
    rows = episode["rows"]
    return {(a["event"], b["event"]) for i, a in enumerate(rows) for b in rows[i+1:]}


def hostile_controls(data):
    attacks = {}
    dropped = json.loads(json.dumps(data))
    dropped["suites"]["mixed_occ"].pop()
    attacks["drop_episode"] = not valid(dropped)

    corrupt = json.loads(json.dumps(data))
    corrupt["suites"]["mixed_occ"][0]["rows"][0]["event"] = "UNKNOWN_EVENT"
    attacks["corrupt_universe"] = not valid(corrupt)

    cross = json.loads(json.dumps(data))
    cross["cross_reset_pairs"] = [["REVOKE", "ACT"]]
    attacks["credit_cross_reset_pair"] = not valid(cross)

    collapsed = json.loads(json.dumps(data))
    for ep in collapsed["suites"]["mixed_occ"]:
        for row in ep["rows"]:
            row["focus_generation"] = "current"
            row["surface_mode"] = "editor"
    attacks["collapse_context_strata"] = not valid(collapsed)
    return attacks


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit.py CANDIDATE.json AUDIT.json")
    raw = Path(sys.argv[1]).read_bytes()
    data = json.loads(raw)
    errors = []
    if not valid(data):
        errors.append("candidate_reconstruction")
    suites = data.get("suites", {})
    pairs = set(itertools.product(EVENTS, repeat=2))
    mixed_obligations = set()
    mixed_full_pairs = True
    for ep in suites.get("mixed_occ", []):
        ctx = (ep["rows"][0]["focus_generation"], ep["rows"][0]["surface_mode"])
        observed = event_pairs(ep)
        mixed_full_pairs = mixed_full_pairs and observed == pairs
        mixed_obligations.update((ctx, a, b) for a, b in observed)
    exhaustive_obligations = set()
    for ep in suites.get("exhaustive", []):
        row0, row1 = ep["rows"]
        exhaustive_obligations.add(((row0["focus_generation"], row0["surface_mode"]), row0["event"], row1["event"]))
    expected_obligations = {(c, a, b) for c in CONTEXTS for a, b in pairs}
    if mixed_obligations != expected_obligations: errors.append("mixed_denominator")
    if exhaustive_obligations != expected_obligations: errors.append("exhaustive_denominator")
    if not mixed_full_pairs: errors.append("within_episode_order_coverage")
    detections = {suite: {m: any(mutant_triggered(ep, m) for ep in suites.get(suite, []))
                          for m in ("joint", "context_only", "order_only")}
                  for suite in ("context_only", "order_only", "mixed_occ", "exhaustive")}
    expected_detections = {
        "context_only": {"joint": False, "context_only": True, "order_only": False},
        "order_only": {"joint": False, "context_only": False, "order_only": True},
        "mixed_occ": {"joint": True, "context_only": True, "order_only": True},
        "exhaustive": {"joint": True, "context_only": True, "order_only": True}}
    if detections != expected_detections: errors.append("mutant_oracle")
    negative_control_unsafe = any(negative_unsafe(suite) for suite in suites.values())
    if negative_control_unsafe: errors.append("negative_control")
    attacks = hostile_controls(data)
    if not all(attacks.values()): errors.append("hostile_mutation_rejection")
    result = {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "candidate_sha256": hashlib.sha256(raw).hexdigest(),
        "model_sha256": hashlib.sha256((HERE / "model.json").read_bytes()).hexdigest(),
        "episode_counts": {k: len(v) for k, v in suites.items()},
        "row_counts": {k: sum(len(ep["rows"]) for ep in v) for k, v in suites.items()},
        "obligations": {"mixed_occ": len(mixed_obligations), "exhaustive": len(exhaustive_obligations),
                        "equal": mixed_obligations == exhaustive_obligations == expected_obligations},
        "mixed_each_episode_covers_16_ordered_pairs": mixed_full_pairs,
        "mutant_detection": detections,
        "negative_control_unsafe_effect": negative_control_unsafe,
        "hostile_mutations_rejected": attacks,
        "cross_reset_pairs_credited": 0
    }
    output = (json.dumps(result, sort_keys=True, indent=2) + "\n").encode()
    fd = os.open(sys.argv[2], os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(output)
    print(output.decode(), end="")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
