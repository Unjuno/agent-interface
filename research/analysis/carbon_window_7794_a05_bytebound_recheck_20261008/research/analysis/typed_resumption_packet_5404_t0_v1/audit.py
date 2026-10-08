#!/usr/bin/env python3
"""Independent raw-only resumption audit; does not import experiment.py."""

from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

POINTS = ("before_action", "during_observation", "after_timeout", "after_authority_change", "after_handoff")
FAULTS = ("none", "stale_evidence", "authority_revoked", "geometry_changed", "duplicate_receipt")
IDEM = (False, True)
POLICIES = ("OPAQUE_SUMMARY", "FULL_REPLAY", "TYPED_PACKET")


def reference_context(point, fault, idem):
    action_status = "UNKNOWN" if point == "after_timeout" else "NOT_EMITTED"
    committed = point == "after_timeout" or fault == "duplicate_receipt"
    return {
        "interruption": point,
        "fault": fault,
        "idempotent": idem,
        "packet_execution_generation": 4,
        "current_execution_generation": 5 if point == "after_handoff" else 4,
        "packet_authority_generation": 7,
        "current_authority_generation": 8 if point == "after_authority_change" else 7,
        "authority_active": point != "after_authority_change" and fault != "authority_revoked",
        "handoff_accepted": point != "after_handoff",
        "packet_evidence_generation": 12,
        "current_evidence_generation": 13 if fault == "stale_evidence" else 12,
        "observation_complete": point != "during_observation",
        "packet_geometry_generation": 2,
        "current_geometry_generation": 3 if fault == "geometry_changed" else 2,
        "action_status": "COMMITTED" if committed and action_status != "UNKNOWN" else action_status,
        "effect_committed": committed,
        "action_id": "effect-17",
    }


def calculate(context):
    auth = context["authority_active"] and context["current_authority_generation"] == context["packet_authority_generation"]
    handoff = context["handoff_accepted"] and context["current_execution_generation"] == context["packet_execution_generation"]
    evidence = context["observation_complete"] and context["current_evidence_generation"] == context["packet_evidence_generation"]
    geometry = context["current_geometry_generation"] == context["packet_geometry_generation"]
    detected = not (auth and handoff and evidence and geometry) or context["effect_committed"]
    if not auth or not handoff:
        packet = {"decision": "ABSTAIN", "attempts": 0, "new_effects": 0, "unsafe": False, "steps": 1, "detected": detected}
    elif context["effect_committed"]:
        packet = {"decision": "RECONCILE_RECEIPT", "attempts": 0, "new_effects": 0, "unsafe": False, "steps": 2 if context["action_status"] == "UNKNOWN" else 1, "detected": detected}
    else:
        steps, decision = 1, "RESUME"
        if not evidence:
            steps, decision = steps + 1, "REOBSERVE_THEN_RESUME"
        if not geometry:
            steps, decision = steps + 1, "REGROUND_THEN_RESUME"
        packet = {"decision": decision, "attempts": 1, "new_effects": 1, "unsafe": False, "steps": steps + 1, "detected": detected}
    if not auth or not handoff:
        replay = {"decision": "ABSTAIN_AFTER_REPLAY", "attempts": 0, "new_effects": 0, "unsafe": False, "steps": 7, "detected": True}
    elif context["effect_committed"]:
        replay = {"decision": "RECONCILE_RECEIPT_AFTER_REPLAY", "attempts": 0, "new_effects": 0, "unsafe": False, "steps": 7, "detected": True}
    else:
        steps = 6 + int(not evidence) + 2 * int(not geometry)
        replay = {"decision": "RESUME_AFTER_REPLAY", "attempts": 1, "new_effects": 1, "unsafe": False, "steps": steps + 1, "detected": True}
    attempts = 1
    opaque = {
        "decision": "RESUME_FROM_SUMMARY",
        "attempts": attempts,
        "new_effects": 0 if context["effect_committed"] and context["idempotent"] else attempts,
        "unsafe": not (auth and handoff and evidence and geometry) or (context["effect_committed"] and not context["idempotent"]),
        "steps": 1,
        "detected": False,
    }
    return {"OPAQUE_SUMMARY": opaque, "FULL_REPLAY": replay, "TYPED_PACKET": packet}


def expected_scenarios():
    for point, fault, idem in itertools.product(POINTS, FAULTS, IDEM):
        yield reference_context(point, fault, idem)


def validate(records):
    errors = []
    headers = [r for r in records if r.get("kind") == "header"]
    rows = [r for r in records if r.get("kind") == "scenario"]
    if len(headers) != 1:
        return ["header_count"], rows, {}
    header = headers[0]
    expected = list(expected_scenarios())
    if [r.get("context") for r in rows] != expected:
        errors.append("scenario_coverage_or_context")
    if len(rows) != 50 or header.get("scenario_count") != 50 or header.get("policy_outcome_count") != 150:
        errors.append("denominator")
    unsafe_packet, unsafe_opaque, detected = 0, 0, 0
    benign_packet, benign_replay = [], []
    for index, (row, context) in enumerate(zip(rows, expected)):
        if row.get("scenario_id") != index:
            errors.append("scenario_id")
        calculated = calculate(context)
        if row.get("outcomes") != calculated:
            errors.append("policy_outcome_mismatch:" + str(index))
        unsafe_packet += int(calculated["TYPED_PACKET"]["unsafe"])
        unsafe_opaque += int(calculated["OPAQUE_SUMMARY"]["unsafe"])
        detected += int(calculated["TYPED_PACKET"]["detected"])
        if context["interruption"] == "before_action" and context["fault"] == "none":
            benign_packet.append(calculated["TYPED_PACKET"]["steps"])
            benign_replay.append(calculated["FULL_REPLAY"]["steps"])
    if header.get("packet_unsafe_admissions") != unsafe_packet or unsafe_packet != 0:
        errors.append("typed_unsafe_admission")
    if header.get("opaque_unsafe_admissions") != unsafe_opaque or unsafe_opaque == 0:
        errors.append("comparison_signal")
    if header.get("packet_invalidation_detections") != detected or detected != 48:
        errors.append("invalidation_detection")
    if header.get("benign_packet_steps_mean") != sum(benign_packet) / len(benign_packet):
        errors.append("packet_step_mean")
    if header.get("benign_full_replay_steps_mean") != sum(benign_replay) / len(benign_replay):
        errors.append("replay_step_mean")
    if not sum(benign_packet) / len(benign_packet) < sum(benign_replay) / len(benign_replay):
        errors.append("no_benign_step_benefit")
    if header.get("formal_invocations") != 1:
        errors.append("invocation_count")
    return errors, rows, header


def audit(raw_path):
    digest = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    records = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines()]
    errors, rows, header = validate(records)
    mutations = []
    altered = json.loads(json.dumps(records))
    row = next(r for r in altered if r.get("kind") == "scenario" and r["context"]["fault"] == "authority_revoked")
    row["outcomes"]["TYPED_PACKET"]["attempts"] = 1
    mutations.append(bool(validate(altered)[0]))
    altered = json.loads(json.dumps(records))
    row = next(r for r in altered if r.get("kind") == "scenario" and r["context"]["fault"] == "duplicate_receipt")
    row["outcomes"]["TYPED_PACKET"]["decision"] = "RESUME"
    mutations.append(bool(validate(altered)[0]))
    dropped = [r for r in records if not (r.get("kind") == "scenario" and r.get("scenario_id") == 0)]
    mutations.append(bool(validate(dropped)[0]))
    altered = json.loads(json.dumps(records))
    row = next(r for r in altered if r.get("kind") == "scenario" and r.get("scenario_id") == 0)
    row["context"]["current_authority_generation"] = 999
    mutations.append(bool(validate(altered)[0]))
    if mutations != [True] * 4:
        errors.append("mutation_controls")
    return {
        "status": "PASS_TYPED_RESUMPTION_SCOPED" if not errors else "FAIL_OR_STOP",
        "raw_sha256": digest,
        "scenario_rows": len(rows),
        "policy_rows": len(rows) * 3,
        "packet_unsafe_admissions": header.get("packet_unsafe_admissions"),
        "opaque_unsafe_admissions": header.get("opaque_unsafe_admissions"),
        "benign_packet_steps_mean": header.get("benign_packet_steps_mean"),
        "benign_full_replay_steps_mean": header.get("benign_full_replay_steps_mean"),
        "mutation_controls_rejected": mutations,
        "errors": errors,
    }


def main():
    result = audit(Path("/out/formal.jsonl"))
    Path("/out/audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_TYPED_RESUMPTION_SCOPED" else 1)


if __name__ == "__main__":
    main()
