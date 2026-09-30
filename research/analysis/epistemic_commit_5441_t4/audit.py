#!/usr/bin/env python3
"""Independent replay auditor; intentionally does not import experiment.py."""
import json
from hashlib import sha256
import sys

POLICIES = ("QUORUM_ONLY", "K1_SHARED_EVIDENCE", "K2_RECIPIENT_RECORD", "K3_FINAL_ACK", "ACTION_CLASS_LEVEL")
DELIVERY = {"on_time": (0, 0), "bounded_delay_12": (1, 2), "bounded_delay_21": (2, 1),
            "v1_lost": (None, 1), "v2_lost": (1, None), "all_lost": (None, None)}
LEVEL = {"reversible": 1, "compensable": 2, "one_shot": 3}
DEADLINE = 7


def expected_messages(c):
    versions = ("v1", "v1") if c["verifier_versions"] == "shared_v1" else ("v0", "v1")
    votes = []
    for i, (delay, version) in enumerate(zip(DELIVERY[c["vote_mode"]], versions), 1):
        if delay is not None:
            votes.append({"kind": "vote", "role": f"v{i}", "attempt": 1, "version": version,
                          "digest": f"evidence-{version}", "tick": delay})
    arrived = {m["role"] for m in votes}
    collect = max(m["tick"] for m in votes) if arrived == {"v1", "v2"} else None
    transcript = sha256(json.dumps(
        {"votes": votes, "recipient_set": ["v1", "v2"] if c["recipient_record_complete"] else []},
        sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    acks = []
    if collect is not None and c["recipient_record_complete"]:
        for i, (delay, version) in enumerate(zip(DELIVERY[c["ack_mode"]], versions), 1):
            if delay is None:
                continue
            tick = collect + 1 + delay
            attempts = {"current": ((1, tick),), "stale_only": ((0, tick),),
                        "stale_then_current": ((0, tick), (1, tick + 1))}[c["ack_epoch"]]
            for attempt, at in attempts:
                if at > DEADLINE:
                    continue
                m = {"kind": "final_ack", "role": f"v{i}", "attempt": attempt, "version": version,
                     "digest": f"decision-{version}-attempt-{attempt}",
                     "transcript_hash": (transcript if attempt == 1 else
                                         sha256((transcript + ":superseded").encode()).hexdigest()),
                     "tick": at, "delivery": "primary"}
                acks.append(m)
                if c["duplicate_acks"]:
                    dup = dict(m); dup["delivery"] = "duplicate"; acks.append(dup)
    return votes, acks, collect, transcript


def expected_policies(c, votes, acks, collect, transcript):
    roles = {m["role"] for m in votes}
    both = roles == {"v1", "v2"}
    k1 = both and {m["version"] for m in votes} == {"v1"}
    k2 = k1 and c["recipient_record_complete"]
    ackroles = {m["role"] for m in acks if m["attempt"] == 1 and m["version"] == "v1"
                and m["digest"] == "decision-v1-attempt-1" and m["transcript_hash"] == transcript}
    # Deduplicate message deliveries and use the slowest verifier ACK for a globally completed K3.
    ack_ticks = {role: max(m["tick"] for m in acks if m["role"] == role and m["attempt"] == 1
                            and m["version"] == "v1" and m["digest"] == "decision-v1-attempt-1"
                            and m["transcript_hash"] == transcript)
                 for role in ackroles}
    if {m["version"] for m in votes} != {"v1"}:
        ack_ticks = {}; ackroles = set()
    k3tick = max(ack_ticks.values()) if set(ackroles) == {"v1", "v2"} else None
    physical = lambda t: (t is not None and c["actuator_version"] == "v1" and t < c["expiry_tick"]
                           and (c["revocation_tick"] is None or t < c["revocation_tick"]))
    req = LEVEL[c["action_class"]]
    gates = {
        "QUORUM_ONLY": (both, collect, 1 if k1 else 0),
        "K1_SHARED_EVIDENCE": (k1, collect, 1),
        "K2_RECIPIENT_RECORD": (k2, collect, 2),
        "K3_FINAL_ACK": (k2 and k3tick is not None and physical(k3tick), k3tick, 3),
    }
    g, t, lv = (k1 if req == 1 else k2 if req == 2 else k2 and k3tick is not None,
                collect if req < 3 else k3tick, req)
    gates["ACTION_CLASS_LEVEL"] = (g and physical(t), t, lv)
    result = []
    for p in POLICIES:
        gate, tick, achieved = gates[p]
        committed = bool(gate and tick is not None and tick <= DEADLINE)
        if p == "QUORUM_ONLY" and committed: achieved = 1 if k1 else 0
        unsafe = bool(committed and req == 3 and (achieved < 3 or not physical(tick)))
        if committed:
            reason = "COMMIT"
        elif not both:
            reason = "VOTES_MISSING_OR_LATE"
        elif not k1:
            reason = "EVIDENCE_VERSION_SPLIT"
        elif p in ("K2_RECIPIENT_RECORD", "K3_FINAL_ACK") and not c["recipient_record_complete"]:
            reason = "RECIPIENT_SET_INCOMPLETE"
        elif p == "ACTION_CLASS_LEVEL" and req == 3 and not k3tick:
            if not c["recipient_record_complete"]: reason = "RECIPIENT_SET_INCOMPLETE"
            elif c["actuator_version"] != "v1": reason = "ACTUATOR_VERSION_STALE"
            elif set(ackroles) != {"v1", "v2"}: reason = "CURRENT_FINAL_ACKS_MISSING_OR_STALE"
            elif not physical(k3tick): reason = "CERTIFICATE_EXPIRED" if k3tick >= c["expiry_tick"] else "AUTHORITY_REVOKED"
            else: reason = "KNOWLEDGE_LEVEL_INSUFFICIENT"
        elif p == "K3_FINAL_ACK" and not k3tick:
            if not c["recipient_record_complete"]: reason = "RECIPIENT_SET_INCOMPLETE"
            elif c["actuator_version"] != "v1": reason = "ACTUATOR_VERSION_STALE"
            elif set(ackroles) != {"v1", "v2"}: reason = "CURRENT_FINAL_ACKS_MISSING_OR_STALE"
            elif not physical(k3tick): reason = "CERTIFICATE_EXPIRED" if k3tick >= c["expiry_tick"] else "AUTHORITY_REVOKED"
            else: reason = "KNOWLEDGE_LEVEL_INSUFFICIENT"
        elif tick is not None and not physical(tick):
            if c["actuator_version"] != "v1": reason = "ACTUATOR_VERSION_STALE"
            elif tick >= c["expiry_tick"]: reason = "CERTIFICATE_EXPIRED"
            else: reason = "AUTHORITY_REVOKED"
        elif not gate:
            reason = "KNOWLEDGE_LEVEL_INSUFFICIENT"
        else:
            reason = "UNKNOWN_HOLD"
        result.append({"policy": p, "commit": committed, "commit_tick": tick if committed else None,
                       "achieved_level": achieved if committed else 0, "required_level": req,
                       "unsafe_one_shot": unsafe,
                       "stale_actuator_commit": bool(committed and c["actuator_version"] != "v1"),
                       "expired_commit": bool(committed and tick >= c["expiry_tick"]),
                       "revoked_commit": bool(committed and c["revocation_tick"] is not None and tick >= c["revocation_tick"]),
                       "hold_reason": reason,
                       "unique_current_ack_roles": sorted(ackroles),
                       "duplicate_ack_deliveries": sum(m["delivery"] == "duplicate" for m in acks)})
    return result


def scenario_grid():
    from itertools import product
    dimensions = product(tuple(DELIVERY), tuple(DELIVERY), ("current", "stale_only", "stale_then_current"),
                         (False, True), ("shared_v1", "split_v0_v1"), ("v1", "v0"), (False, True),
                         (2, 7), (None, 2), tuple(LEVEL))
    for i, values in enumerate(dimensions):
        v, a, epoch, dup, versions, actuator, recipient, expiry, revoke, action = values
        yield {"scenario_id": f"case-{i:05d}", "vote_mode": v, "ack_mode": a, "ack_epoch": epoch,
               "duplicate_acks": dup, "verifier_versions": versions, "actuator_version": actuator,
               "recipient_record_complete": recipient, "expiry_tick": expiry, "revocation_tick": revoke,
               "action_class": action}


def audit(path):
    with open(path, encoding="utf-8") as f:
        lines = [json.loads(line) for line in f if line.strip()]
    errors = []
    if len(lines) != 20737 or lines[0].get("kind") != "manifest":
        errors.append(f"line_count_or_manifest:{len(lines)}")
    if len(lines) < 2:
        return {"audit": "FAIL", "errors": errors}
    manifest = lines[0]
    if manifest.get("schema") != "issue-5441-epistemic-t4-v1":
        errors.append("manifest_schema")
    if manifest.get("scenario_count") != 20736 or manifest.get("policy_trace_count") != 103680:
        errors.append("manifest_counts")
    unsafe = {p: 0 for p in POLICIES}
    clean_total = clean_success = 0
    safe_holds = {}
    expected = list(scenario_grid())
    actual_rows = lines[1:]
    if len(actual_rows) != len(expected): errors.append(f"trace_count:{len(actual_rows)}")
    for i, (raw, c) in enumerate(zip(actual_rows, expected)):
        if raw.get("kind") != "trace" or raw.get("case") != c:
            errors.append(f"case_mismatch:{i}"); continue
        votes, acks, collect, transcript = expected_messages(c)
        if raw.get("vote_messages") != votes: errors.append(f"votes:{i}")
        if raw.get("ack_messages") != acks: errors.append(f"acks:{i}")
        policies = expected_policies(c, votes, acks, collect, transcript)
        if raw.get("policies") != policies: errors.append(f"policies:{i}")
        for pr in policies: unsafe[pr["policy"]] += int(pr["unsafe_one_shot"])
        adaptive = next(pr for pr in policies if pr["policy"] == "ACTION_CLASS_LEVEL")
        if not adaptive["commit"]:
            reason = adaptive["hold_reason"]
            safe_holds[reason] = safe_holds.get(reason, 0) + 1
        clean = (c["vote_mode"] in ("on_time", "bounded_delay_12", "bounded_delay_21")
                 and c["ack_mode"] in ("on_time", "bounded_delay_12", "bounded_delay_21")
                 and c["ack_epoch"] in ("current", "stale_then_current")
                 and c["verifier_versions"] == "shared_v1"
                 and c["actuator_version"] == "v1" and c["recipient_record_complete"]
                 and c["expiry_tick"] == 7 and c["revocation_tick"] is None)
        if clean:
            clean_total += 1
            ar = next(p for p in policies if p["policy"] == "ACTION_CLASS_LEVEL")
            clean_success += int(ar["commit"] and ar["commit_tick"] <= DEADLINE)
    quorum = unsafe["QUORUM_ONLY"]; adaptive = unsafe["ACTION_CLASS_LEVEL"]
    reduction = quorum > 0 and adaptive * 10 <= quorum
    model_gate = adaptive == 0 and reduction and clean_total == clean_success
    expected_decision = {"model_gate": "PASS" if model_gate else "FAIL",
        "unqualified_one_shot_commits_by_policy": unsafe,
        "clean_liveness_cases": clean_total, "clean_liveness_passes": clean_success,
        "at_least_90_percent_reduction_vs_quorum": reduction,
        "action_class_safe_holds_by_reason": safe_holds,
        "scope": "deterministic authored protocol/schedule grid; not a consensus or production proof"}
    if manifest.get("decision") != expected_decision: errors.append("manifest_decision_mismatch")
    return {"audit": "PASS" if not errors else "FAIL", "errors": errors[:100],
            "error_count": len(errors), "scenario_count": len(actual_rows),
            "policy_trace_count": sum(len(r.get("policies", [])) for r in actual_rows),
            "reconstructed": {"unsafe": unsafe, "clean_liveness_cases": clean_total,
                              "clean_liveness_passes": clean_success, "model_gate": expected_decision["model_gate"]}}


if __name__ == "__main__":
    print(json.dumps(audit(sys.argv[1]), sort_keys=True))
