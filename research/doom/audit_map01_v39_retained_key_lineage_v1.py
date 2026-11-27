"""Join retained V39 admissions to per-key UP or verified cancellation cleanup.

The audit identifies X-server keymap state only. It does not claim physical-key
release, useful-task-effect timing, or a successful MAP01 task outcome.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def rows(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def _identity(row):
    return (row.get("id"), row.get("step"), row.get("intent_token"),
            row.get("owner_id"), row.get("key"), row.get("keycode"))


def _attempt_ok(attempt):
    start = attempt.get("keyrelease_started_ns")
    sync = attempt.get("sync_returned_ns")
    sample = attempt.get("keymap_sampled_ns")
    return (
        attempt.get("server_key_down_before") is True
        and attempt.get("server_key_down_after") is False
        and attempt.get("keyrelease_error") is None
        and attempt.get("sync_error") is None
        and attempt.get("keymap_before_error") is None
        and attempt.get("keymap_after_error") is None
        and type(start) is int and type(sync) is int and type(sample) is int
        and start <= sync <= sample
    )


def audit(events, owner_events, score, scorer_samples):
    admissions = [row for row in events if row.get("event") == "input_admission"]
    transitions = [row for row in events if row.get("event") == "input_release_transition"
                   and row.get("operation") == "up"]
    releases = [row for row in owner_events if row.get("event") == "owner_release"]
    if len({_identity(row) for row in admissions}) != len(admissions):
        return {"schema": "map01-v39-retained-key-lineage-audit-v1",
                "pass": False, "error": "duplicate admission identity"}

    unmatched = set(range(len(admissions)))
    matches = []
    invalid = []
    for transition in transitions:
        receipt = transition.get("admission_receipt")
        candidates = [i for i in unmatched if isinstance(receipt, dict)
                      and _identity(admissions[i]) == _identity(receipt)]
        if len(candidates) != 1:
            invalid.append({"kind": "direct_transition_identity", "id": transition.get("id"),
                            "step": transition.get("step"), "candidate_count": len(candidates)})
            continue
        i = candidates[0]
        admission = admissions[i]
        detail = transition.get("owner_thread_keyup_receipt")
        attempts = detail.get("server_keyup_attempts", []) if isinstance(detail, dict) else []
        valid = (
            transition.get("admission_receipt_valid") is True
            and transition.get("owner_transition_verified") is True
            and transition.get("ordinary_release_candidate") is True
            and transition.get("owner_cleanup_intervened") is False
            and transition.get("owner_id") == admission.get("owner_id")
            and transition.get("intent_token") == admission.get("intent_token")
            and transition.get("key") == admission.get("key")
            and transition.get("release_batch_complete") is True
            and isinstance(detail, dict)
            and detail.get("event") == "owner_explicit_keyup"
            and detail.get("owner_id") == admission.get("owner_id")
            and detail.get("intent_token") == admission.get("intent_token")
            and detail.get("key") == admission.get("key")
            and detail.get("keycode") == admission.get("keycode")
            and detail.get("server_keyup_verified") is True
            and len(attempts) == 1 and _attempt_ok(attempts[0])
        )
        if not valid:
            invalid.append({"kind": "direct_transition_receipt_invalid",
                            "id": transition.get("id"), "step": transition.get("step")})
            continue
        attempt = attempts[0]
        ack = admission.get("input_ack_ns")
        if type(ack) is not int or ack > attempt["keyrelease_started_ns"]:
            invalid.append({"kind": "direct_transition_time_invalid",
                            "id": transition.get("id"), "step": transition.get("step")})
            continue
        unmatched.remove(i)
        matches.append({
            "id": admission["id"], "step": admission["step"], "key": admission["key"],
            "keycode": admission["keycode"], "intent_token": admission["intent_token"],
            "release_evidence": "explicit_up",
            "ack_to_keyrelease_start_ms": (attempt["keyrelease_started_ns"] - ack) / 1e6,
            "ack_to_server_keymap_up_ms": (attempt["keymap_sampled_ns"] - ack) / 1e6,
            "server_key_down_before": True, "server_key_down_after": False,
            "physical_verification_authoritative": False,
        })

    # Aggregate cancellation cleanup has no direct transition, so match only an
    # otherwise-unmatched admission with the same owner token, keycode and target.
    for release in releases:
        if release.get("reason") != "cancelled" or release.get("verified") is not True:
            continue
        if release.get("keys_down") != [] or release.get("keys_unknown") != []:
            continue
        token = release.get("intent_token")
        identity = release.get("target_process_identity")
        attempts_by_code = release.get("key_release_attempts")
        if not isinstance(attempts_by_code, dict):
            continue
        for code, state in attempts_by_code.items():
            attempts = state.get("attempts", []) if isinstance(state, dict) else []
            valid_attempts = [item for item in attempts if _attempt_ok(item)]
            if len(valid_attempts) != 1:
                continue
            attempt = valid_attempts[0]
            candidates = [i for i in unmatched
                          if admissions[i].get("intent_token") == token
                          and admissions[i].get("keycode") == int(code)
                          and admissions[i].get("target_process_identity") == identity
                          and type(admissions[i].get("input_ack_ns")) is int
                          and admissions[i]["input_ack_ns"] <= attempt["keyrelease_started_ns"]]
            if len(candidates) != 1:
                if candidates:
                    invalid.append({"kind": "cleanup_match_ambiguous", "keycode": int(code),
                                    "candidate_count": len(candidates)})
                continue
            i = candidates[0]
            admission = admissions[i]
            if state.get("verified") is not True:
                invalid.append({"kind": "cleanup_keycode_unverified", "keycode": int(code)})
                continue
            unmatched.remove(i)
            matches.append({
                "id": admission["id"], "step": admission["step"], "key": admission["key"],
                "keycode": admission["keycode"], "intent_token": admission["intent_token"],
                "release_evidence": "verified_cancel_cleanup",
                "ack_to_keyrelease_start_ms": (
                    attempt["keyrelease_started_ns"] - admission["input_ack_ns"]) / 1e6,
                "ack_to_server_keymap_up_ms": (
                    attempt["keymap_sampled_ns"] - admission["input_ack_ns"]) / 1e6,
                "server_key_down_before": True, "server_key_down_after": False,
                "physical_verification_authoritative": False,
            })

    scorer = score if isinstance(score, dict) else {}
    score_ok = (scorer.get("event") == "post_control_score"
                and type(scorer.get("kill_count")) is int
                and type(scorer.get("death_count")) is int
                and type(scorer.get("map_exit")) is bool)
    sample_payloads = []
    for row in scorer_samples:
        payload = row.get("payload") if isinstance(row, dict) else None
        if (row.get("controller_visible") is not False or not isinstance(payload, dict)
                or payload.get("schema") != "independent-progress-sample-v2"
                or type(payload.get("sample_ns")) is not int
                or type(payload.get("kill_count")) is not int
                or type(payload.get("map_exit")) is not bool):
            invalid.append({"kind": "independent_scorer_sample_invalid"})
            sample_payloads = []
            break
        sample_payloads.append(payload)
    sample_times = [row["sample_ns"] for row in sample_payloads]
    samples_ok = bool(sample_payloads) and sample_times == sorted(sample_times)
    if sample_payloads and not samples_ok:
        invalid.append({"kind": "independent_scorer_clock_invalid"})
    earliest_admission = min((row.get("input_ack_ns") for row in admissions
                              if type(row.get("input_ack_ns")) is int), default=None)
    post_admission_samples = [row for row in sample_payloads
                              if earliest_admission is not None
                              and row["sample_ns"] >= earliest_admission]
    useful = next((row for row in post_admission_samples
                   if row["kill_count"] > 0 or row["map_exit"] is True), None)
    result = {
        "schema": "map01-v39-retained-key-lineage-audit-v1",
        "admission_count": len(admissions),
        "direct_transition_count": len(transitions),
        "verified_key_release_count": len(matches),
        "explicit_up_count": sum(x["release_evidence"] == "explicit_up" for x in matches),
        "cancel_cleanup_count": sum(x["release_evidence"] == "verified_cancel_cleanup" for x in matches),
        "unresolved_admissions": [_identity(admissions[i]) for i in sorted(unmatched)],
        "invalid_evidence": invalid,
        "key_release_lineage_complete": not unmatched and not invalid,
        "matches": matches,
        "task_effect": ({"independent_score_present": score_ok and samples_ok,
                         "kill_count": scorer.get("kill_count"),
                         "death_count": scorer.get("death_count"),
                         "map_exit": scorer.get("map_exit"),
                         "independent_sample_count": len(sample_payloads),
                         "first_post_admission_useful_progress_ns": (
                             useful["sample_ns"] if useful is not None else None),
                         "first_post_admission_useful_progress_ms": (
                             (useful["sample_ns"] - earliest_admission) / 1e6
                             if useful is not None else None),
                         "useful_progress_observed": useful is not None}
                        if score_ok else {"independent_score_present": False}),
        "scope_note": ("X-server keymap verification only; no physical-key timing or "
                       "independent useful-feedback onset is inferred."),
    }
    result["pass"] = result["key_release_lineage_complete"] and score_ok and samples_ok
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("runtime", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    root = args.runtime
    input_paths = {name: root / name for name in
                   ("events.jsonl", "owner-events.json", "score.json")}
    scorer_samples = rows(root / "scorer-samples.jsonl")
    input_paths["scorer-samples.jsonl"] = root / "scorer-samples.jsonl"
    result = audit(rows(input_paths["events.jsonl"]),
                   json.loads(input_paths["owner-events.json"].read_text(encoding="utf-8")),
                   json.loads(input_paths["score.json"].read_text(encoding="utf-8")),
                   scorer_samples)
    prereg = root.parent.parent / "PREREG.json"
    result["evidence_sha256"] = {
        name: hashlib.sha256(path.read_bytes()).hexdigest()
        for name, path in input_paths.items()}
    if prereg.is_file():
        result["evidence_sha256"]["PREREG.json"] = hashlib.sha256(
            prereg.read_bytes()).hexdigest()
    result["audit_code_sha256"] = hashlib.sha256(
        Path(__file__).read_bytes()).hexdigest()
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    raise SystemExit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
