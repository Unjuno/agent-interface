"""Deterministic finite candidate for #5531 T6-E1; emits only JSONL."""
import argparse
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def episode(deadline, world, policy):
    trial_id = f"d{deadline}-{world}-{policy}"
    observations = [
        {"tick": tick, "event": "NO_HEARTBEAT", "heartbeat_sequence": None}
        for tick in range(1, deadline + 1)
    ]
    prefix_hash = digest(observations)
    state = "AVAILABLE"
    route_enabled = True
    authority_revoked = False
    authority_generation = 1
    rows = []

    def emit(tick, event, observation=None, response_generation=None,
             authenticated=False, witness_domain=None):
        rows.append({
            "schema": "failure-detector-async-transition-v1",
            "trial_id": trial_id,
            "deadline": deadline,
            "world": world,
            "policy": policy,
            "tick": tick,
            "event": event,
            "observation": observation,
            "prefix_sha256": prefix_hash,
            "response_generation": response_generation,
            "authenticated": authenticated,
            "witness_domain": witness_domain,
            "state": state,
            "route_enabled": route_enabled,
            "authority_revoked": authority_revoked,
            "authority_generation": authority_generation,
            "effectful_action": False,
        })

    emit(0, "START")
    for obs in observations:
        emit(obs["tick"], obs["event"], obs)

    if policy == "timeout_as_failure":
        state, route_enabled, authority_revoked, authority_generation = "FAILED", False, True, 2
    else:
        state, route_enabled = "SUSPECTED_UNAVAILABLE", False
    emit(deadline, "TIMEOUT_DECISION", {"tick": deadline, "prefix_sha256": prefix_hash})

    reveal_tick = deadline + 1
    if world == "healthy_slow":
        if policy == "typed_suspicion":
            state, route_enabled = "AVAILABLE", True
        emit(reveal_tick, "FRESH_AUTHENTICATED_HEARTBEAT",
             {"tick": reveal_tick, "heartbeat_sequence": 1}, 1, True, "subject-channel")
    elif world == "crashed":
        state, route_enabled, authority_revoked, authority_generation = "FAILED", False, True, 2
        emit(reveal_tick, "INDEPENDENT_CRASH_WITNESS",
             {"tick": reveal_tick, "witness_sequence": 1}, None, True, "kernel-domain")
        emit(reveal_tick + 1, "LATE_OLD_GENERATION_RESPONSE",
             {"tick": reveal_tick + 1, "heartbeat_sequence": 1}, 1, True, "subject-channel")
    else:
        emit(reveal_tick, "INVALID_UNAUTHENTICATED_RESPONSE",
             {"tick": reveal_tick, "heartbeat_sequence": 1}, 1, False, "untrusted-channel")
    return rows


def build_records(config):
    return [row for deadline in config["deadlines"]
            for world in config["worlds"]
            for policy in config["policies"]
            for row in episode(deadline, world, policy)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True)
    args = parser.parse_args()
    config = json.loads((HERE / "freeze.json").read_text(encoding="utf-8"))
    records = build_records(config)
    Path(args.raw).write_text("".join(canonical(row) + "\n" for row in records), encoding="utf-8")
    print(json.dumps({"rows": len(records), "trials": len({r['trial_id'] for r in records}),
                      "raw_sha256": hashlib.sha256(Path(args.raw).read_bytes()).hexdigest()},
                     sort_keys=True))


if __name__ == "__main__":
    main()
