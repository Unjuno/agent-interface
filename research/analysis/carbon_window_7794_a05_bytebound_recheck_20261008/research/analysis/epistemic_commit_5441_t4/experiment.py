#!/usr/bin/env python3
"""Exact finite message-protocol simulator for Issue #5441 T4."""
from itertools import product
from hashlib import sha256
import json

POLICIES = ("QUORUM_ONLY", "K1_SHARED_EVIDENCE", "K2_RECIPIENT_RECORD", "K3_FINAL_ACK", "ACTION_CLASS_LEVEL")
DELIVERY_MODES = ("on_time", "bounded_delay_12", "bounded_delay_21",
                  "v1_lost", "v2_lost", "all_lost")
ACK_EPOCHS = ("current", "stale_only", "stale_then_current")
ACTION_LEVEL = {"reversible": 1, "compensable": 2, "one_shot": 3}
DEADLINE = 7


def pair_delays(mode):
    return {"on_time": (0, 0), "bounded_delay_12": (1, 2), "bounded_delay_21": (2, 1),
            "v1_lost": (None, 1), "v2_lost": (1, None), "all_lost": (None, None)}[mode]


def verifier_versions(mode):
    return ("v1", "v1") if mode == "shared_v1" else ("v0", "v1")


def make_messages(case):
    versions = verifier_versions(case["verifier_versions"])
    vote_messages = []
    for role, (delay, version) in enumerate(zip(pair_delays(case["vote_mode"]), versions), start=1):
        if delay is not None and delay <= DEADLINE:
            vote_messages.append({"kind": "vote", "role": f"v{role}", "attempt": 1,
                                  "version": version, "digest": f"evidence-{version}", "tick": delay})
    vote_by_role = {message["role"]: message for message in vote_messages}
    collect_tick = (max(message["tick"] for message in vote_messages)
                    if set(vote_by_role) == {"v1", "v2"} else None)
    ack_messages = []
    transcript_hash = sha256(json.dumps(
        {"votes": vote_messages, "recipient_set": ["v1", "v2"] if case["recipient_record_complete"] else []},
        sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if collect_tick is not None and case["recipient_record_complete"]:
        for role, (delay, version) in enumerate(zip(pair_delays(case["ack_mode"]), versions), start=1):
            if delay is None:
                continue
            base_tick = collect_tick + 1 + delay
            if case["ack_epoch"] == "current":
                attempts = ((1, base_tick),)
            elif case["ack_epoch"] == "stale_only":
                attempts = ((0, base_tick),)
            else:
                attempts = ((0, base_tick), (1, base_tick + 1))
            for attempt, tick in attempts:
                if tick <= DEADLINE:
                    message = {"kind": "final_ack", "role": f"v{role}", "attempt": attempt,
                               "version": version, "digest": f"decision-{version}-attempt-{attempt}",
                               "transcript_hash": (transcript_hash if attempt == 1 else
                                                   sha256((transcript_hash + ":superseded").encode()).hexdigest()),
                               "tick": tick}
                    ack_messages.append(message)
                    message["delivery"] = "primary"
                    if case["duplicate_acks"]:
                        duplicate = dict(message)
                        duplicate["delivery"] = "duplicate"
                        ack_messages.append(duplicate)
    current_acks = {}
    for message in ack_messages:
        if (message["attempt"] == 1 and message["version"] == "v1"
                and message["digest"] == "decision-v1-attempt-1"
                and message["transcript_hash"] == transcript_hash):
            current_acks[message["role"]] = min(current_acks.get(message["role"], DEADLINE + 1), message["tick"])
    if versions != ("v1", "v1"):
        current_acks = {}
    return vote_messages, ack_messages, collect_tick, current_acks, transcript_hash


def physical_ok(case, tick):
    return (tick is not None and case["actuator_version"] == "v1"
            and tick < case["expiry_tick"]
            and (case["revocation_tick"] is None or tick < case["revocation_tick"]))


def simulate_case(case):
    votes, acks, collect_tick, current_acks, transcript_hash = make_messages(case)
    roles = {message["role"] for message in votes}
    both_votes = roles == {"v1", "v2"}
    vote_versions = {message["version"] for message in votes}
    k1 = both_votes and vote_versions == {"v1"}
    k2 = k1 and case["recipient_record_complete"]
    k3 = (k2 and set(current_acks) == {"v1", "v2"}
          and physical_ok(case, max(current_acks.values())))
    required = ACTION_LEVEL[case["action_class"]]
    policy_gates = {
        "QUORUM_ONLY": (both_votes, collect_tick, 1 if k1 else 0),
        "K1_SHARED_EVIDENCE": (k1, collect_tick, 1),
        "K2_RECIPIENT_RECORD": (k2, collect_tick, 2),
        "K3_FINAL_ACK": (k3, max(current_acks.values()) if k3 else None, 3),
        "ACTION_CLASS_LEVEL": (
            (k1 if required == 1 else k2 if required == 2 else k3)
            and physical_ok(case, (collect_tick if required < 3 else max(current_acks.values()) if k3 else None)),
            (collect_tick if required < 3 else max(current_acks.values()) if k3 else None), required),
    }
    output = []
    for policy in POLICIES:
        gate, tick, level = policy_gates[policy]
        commit = bool(gate and tick is not None and tick <= DEADLINE)
        if policy == "K3_FINAL_ACK" and commit:
            level = 3
        if policy == "QUORUM_ONLY" and commit:
            level = 1 if k1 else 0
        unsafe = bool(commit and case["action_class"] == "one_shot"
                      and (level < 3 or not physical_ok(case, tick)))
        stale = bool(commit and case["actuator_version"] != "v1")
        expired = bool(commit and tick >= case["expiry_tick"])
        revoked = bool(commit and case["revocation_tick"] is not None and tick >= case["revocation_tick"])
        if commit:
            reason = "COMMIT"
        elif not both_votes:
            reason = "VOTES_MISSING_OR_LATE"
        elif not k1:
            reason = "EVIDENCE_VERSION_SPLIT"
        elif policy in ("K2_RECIPIENT_RECORD", "K3_FINAL_ACK") and not case["recipient_record_complete"]:
            reason = "RECIPIENT_SET_INCOMPLETE"
        elif policy == "K3_FINAL_ACK" and not k3:
            if not case["recipient_record_complete"]:
                reason = "RECIPIENT_SET_INCOMPLETE"
            elif case["actuator_version"] != "v1":
                reason = "ACTUATOR_VERSION_STALE"
            elif k2 and set(current_acks) != {"v1", "v2"}:
                reason = "CURRENT_FINAL_ACKS_MISSING_OR_STALE"
            elif k2 and max(current_acks.values(), default=None) is not None and not physical_ok(case, max(current_acks.values())):
                tick0 = max(current_acks.values())
                reason = "CERTIFICATE_EXPIRED" if tick0 >= case["expiry_tick"] else "AUTHORITY_REVOKED"
            else:
                reason = "KNOWLEDGE_LEVEL_INSUFFICIENT"
        elif policy == "ACTION_CLASS_LEVEL" and required == 3 and not k3:
            if not case["recipient_record_complete"]:
                reason = "RECIPIENT_SET_INCOMPLETE"
            elif case["actuator_version"] != "v1":
                reason = "ACTUATOR_VERSION_STALE"
            elif set(current_acks) != {"v1", "v2"}:
                reason = "CURRENT_FINAL_ACKS_MISSING_OR_STALE"
            elif not physical_ok(case, max(current_acks.values())):
                reason = "CERTIFICATE_EXPIRED" if max(current_acks.values()) >= case["expiry_tick"] else "AUTHORITY_REVOKED"
            else:
                reason = "KNOWLEDGE_LEVEL_INSUFFICIENT"
        elif tick is not None and not physical_ok(case, tick):
            if case["actuator_version"] != "v1":
                reason = "ACTUATOR_VERSION_STALE"
            elif tick >= case["expiry_tick"]:
                reason = "CERTIFICATE_EXPIRED"
            else:
                reason = "AUTHORITY_REVOKED"
        elif not gate:
            reason = "KNOWLEDGE_LEVEL_INSUFFICIENT"
        else:
            reason = "UNKNOWN_HOLD"
        output.append({"policy": policy, "commit": commit, "commit_tick": tick if commit else None,
                       "achieved_level": level if commit else 0, "required_level": required,
                       "unsafe_one_shot": unsafe, "stale_actuator_commit": stale,
                       "expired_commit": expired, "revoked_commit": revoked,
                       "hold_reason": reason,
                       "unique_current_ack_roles": sorted(current_acks),
                       "duplicate_ack_deliveries": sum(m.get("delivery") == "duplicate" for m in acks)})
    return votes, acks, output


def cases():
    dimensions = product(DELIVERY_MODES, DELIVERY_MODES, ACK_EPOCHS, (False, True),
                         ("shared_v1", "split_v0_v1"), ("v1", "v0"), (False, True),
                         (2, 7), (None, 2), ("reversible", "compensable", "one_shot"))
    for index, values in enumerate(dimensions):
        (vote_mode, ack_mode, ack_epoch, duplicate_acks, verifier_mode, actuator_version,
         recipient_complete, expiry_tick, revocation_tick, action_class) = values
        yield {"scenario_id": f"case-{index:05d}", "vote_mode": vote_mode,
               "ack_mode": ack_mode, "ack_epoch": ack_epoch, "duplicate_acks": duplicate_acks,
               "verifier_versions": verifier_mode, "actuator_version": actuator_version,
               "recipient_record_complete": recipient_complete, "expiry_tick": expiry_tick,
               "revocation_tick": revocation_tick, "action_class": action_class}


def is_clean_liveness_case(case):
    return (case["vote_mode"] in ("on_time", "bounded_delay_12", "bounded_delay_21")
            and case["ack_mode"] in ("on_time", "bounded_delay_12", "bounded_delay_21")
            and case["ack_epoch"] in ("current", "stale_then_current")
            and case["verifier_versions"] == "shared_v1"
            and case["actuator_version"] == "v1"
            and case["recipient_record_complete"] and case["expiry_tick"] == 7
            and case["revocation_tick"] is None)


def hand_authored_smokes():
    base = {"scenario_id": "smoke", "vote_mode": "on_time", "ack_mode": "on_time",
            "ack_epoch": "current", "duplicate_acks": False,
            "verifier_versions": "shared_v1", "actuator_version": "v1",
            "recipient_record_complete": True, "expiry_tick": 7,
            "revocation_tick": None, "action_class": "one_shot"}
    safe = simulate_case(base)[2]
    assert next(row for row in safe if row["policy"] == "ACTION_CLASS_LEVEL")["commit"]
    assert next(row for row in safe if row["policy"] == "QUORUM_ONLY")["unsafe_one_shot"]
    stale = simulate_case(dict(base, actuator_version="v0"))[2]
    assert next(row for row in stale if row["policy"] == "QUORUM_ONLY")["commit"]
    assert not next(row for row in stale if row["policy"] == "ACTION_CLASS_LEVEL")["commit"]
    lost = simulate_case(dict(base, ack_mode="all_lost"))[2]
    assert not next(row for row in lost if row["policy"] == "ACTION_CLASS_LEVEL")["commit"]
    assert next(row for row in lost if row["policy"] == "QUORUM_ONLY")["unsafe_one_shot"]
    return 3


def main():
    hand_authored_smokes()
    rows = []
    unsafe_by_policy = {policy: 0 for policy in POLICIES}
    liveness_cases = liveness_passes = 0
    action_class_holds = {}
    for case in cases():
        votes, acks, result = simulate_case(case)
        for row in result:
            unsafe_by_policy[row["policy"]] += int(row["unsafe_one_shot"])
        if is_clean_liveness_case(case):
            liveness_cases += 1
            level = next(row for row in result if row["policy"] == "ACTION_CLASS_LEVEL")
            liveness_passes += int(level["commit"] and level["commit_tick"] <= DEADLINE)
        if not next(row for row in result if row["policy"] == "ACTION_CLASS_LEVEL")["commit"]:
            reason = next(row for row in result if row["policy"] == "ACTION_CLASS_LEVEL")["hold_reason"]
            action_class_holds[reason] = action_class_holds.get(reason, 0) + 1
        rows.append({"case": case, "vote_messages": votes, "ack_messages": acks, "policies": result})
    quorum_bad = unsafe_by_policy["QUORUM_ONLY"]
    class_bad = unsafe_by_policy["ACTION_CLASS_LEVEL"]
    reduction_ok = quorum_bad > 0 and class_bad * 10 <= quorum_bad
    decision = {"model_gate": "PASS" if class_bad == 0 and reduction_ok and liveness_cases == liveness_passes else "FAIL",
                "unqualified_one_shot_commits_by_policy": unsafe_by_policy,
                "clean_liveness_cases": liveness_cases, "clean_liveness_passes": liveness_passes,
                "at_least_90_percent_reduction_vs_quorum": reduction_ok,
                "action_class_safe_holds_by_reason": action_class_holds,
                "scope": "deterministic authored protocol/schedule grid; not a consensus or production proof"}
    print(json.dumps({"kind": "manifest", "schema": "issue-5441-epistemic-t4-v1",
                      "scenario_count": len(rows), "policy_trace_count": len(rows) * len(POLICIES),
                      "deadline_tick": DEADLINE, "policies": list(POLICIES), "decision": decision},
                     sort_keys=True, separators=(",", ":")))
    for row in rows:
        print(json.dumps({"kind": "trace", **row}, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
