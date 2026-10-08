#!/usr/bin/env python3
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

OPS = ("OBS0", "OBS1", "VALIDATE", "COMMIT", "ADVANCE", "CONTRADICT", "TRY_ACTION")
NONE, TENTATIVE, VALIDATED, COMMITTED, QUARANTINED = range(5)
INITIAL = (NONE, 0, -1, -1, False, ())


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def independent_step(s, op):
    phase, generation, value, support_generation, contradiction, archive = s
    accepted = False
    action = None

    if op[0:3] == "OBS":
        value = 0 if op == "OBS0" else 1
        support_generation = generation
        contradiction = False
        phase = TENTATIVE
        accepted = True
    elif op == "VALIDATE":
        if (phase, support_generation, contradiction) == (TENTATIVE, generation, False):
            phase = VALIDATED
            accepted = True
    elif op == "COMMIT":
        if (phase, support_generation, contradiction) == (VALIDATED, generation, False):
            archive = (*archive, (value, support_generation))
            phase = COMMITTED
            accepted = True
    elif op == "ADVANCE":
        if generation == 0:
            generation = 1
            accepted = True
    elif op == "CONTRADICT":
        if support_generation == generation and phase in (TENTATIVE, VALIDATED, COMMITTED) and contradiction is False:
            contradiction = True
            phase = QUARANTINED
            accepted = True
    elif op == "TRY_ACTION":
        accepted = True
        action = phase == COMMITTED and support_generation == generation and contradiction is False
    else:
        raise RuntimeError(op)

    return (phase, generation, value, support_generation, contradiction, archive), (accepted, action)


def encode_record(depth, code, state, result):
    phase, gen, value, support_gen, contradicted, archive = state
    accepted, action = result
    action_code = 2 if action is None else int(bool(action))
    b = bytearray(struct.pack("!BQ", depth, code))
    b.extend(bytes((phase, gen, value + 1, support_gen + 1, int(contradicted), len(archive), int(accepted), action_code)))
    for v, g in archive:
        b.extend(bytes((v + 1, g + 1)))
    return bytes(b)


def audit_enumeration(max_depth=8):
    digest = hashlib.sha256()
    metrics = {
        "trace_count_including_empty": 1,
        "transition_count": 0,
        "stale_generation_action_safe_admissions": 0,
        "contradicted_action_safe_admissions": 0,
        "commit_from_unvalidated_admissions": 0,
        "fresh_recommit_action_safe": 0,
        "provenance_retained_across_generation_change": 0,
        "committed_only_unsafe_stale_or_contradicted": 0,
    }

    def walk(depth, code, state):
        if depth >= max_depth:
            return
        for idx, op in enumerate(OPS):
            before = state
            after, result = independent_step(state, op)
            d = depth + 1
            child_code = code * len(OPS) + idx + 1
            metrics["trace_count_including_empty"] += 1
            metrics["transition_count"] += 1
            digest.update(encode_record(d, child_code, after, result))

            phase, gen, _v, support_gen, contradicted, archive = before
            if op == "COMMIT" and phase != VALIDATED and result[0]:
                metrics["commit_from_unvalidated_admissions"] += 1
            if op == "ADVANCE" and result[0] and before[5] and after[5] == before[5]:
                metrics["provenance_retained_across_generation_change"] += 1
            if op == "TRY_ACTION":
                stale = phase == COMMITTED and support_gen != gen
                contradiction_case = (contradicted or phase == QUARANTINED) and bool(archive)
                if stale and result[1]:
                    metrics["stale_generation_action_safe_admissions"] += 1
                if contradiction_case and result[1]:
                    metrics["contradicted_action_safe_admissions"] += 1
                if result[1]:
                    gens = [g for _x, g in after[5]]
                    if after[1] == 1 and 0 in gens and gens[-1] == 1:
                        metrics["fresh_recommit_action_safe"] += 1
                if archive and not result[1] and (stale or contradiction_case):
                    metrics["committed_only_unsafe_stale_or_contradicted"] += 1
            walk(d, child_code, after)

    walk(0, 0, INITIAL)
    return digest.hexdigest(), metrics


def run_trace(step, trace):
    s = INITIAL
    last = (False, None)
    for op in trace:
        s, last = step(s, op)
    return s, last


def corruption_controls():
    controls = {}

    def sticky(s, op):
        ns, r = independent_step(s, op)
        if op == "TRY_ACTION":
            r = (True, bool(s[5]))
        return ns, r
    stale_trace = ["OBS0", "VALIDATE", "COMMIT", "ADVANCE", "TRY_ACTION"]
    _s, sticky_r = run_trace(sticky, stale_trace)
    _s2, correct_r = run_trace(independent_step, stale_trace)
    controls["sticky_action_safe_detected"] = sticky_r[1] is True and correct_r[1] is False

    def loose_commit(s, op):
        if op == "COMMIT" and s[0] == TENTATIVE:
            phase, gen, v, sg, c, archive = s
            return (COMMITTED, gen, v, sg, c, (*archive, (v, sg))), (True, None)
        return independent_step(s, op)
    _s, loose_r = run_trace(loose_commit, ["OBS0", "COMMIT"])
    _s2, correct_r = run_trace(independent_step, ["OBS0", "COMMIT"])
    controls["commit_from_tentative_detected"] = loose_r[0] is True and correct_r[0] is False

    def ignore_contradiction(s, op):
        ns, r = independent_step(s, op)
        if op == "TRY_ACTION" and s[5]:
            phase, gen, _v, sg, _c, _archive = s
            r = (True, phase in (COMMITTED, QUARANTINED) and sg == gen)
        return ns, r
    contradiction_trace = ["OBS0", "VALIDATE", "COMMIT", "CONTRADICT", "TRY_ACTION"]
    _s, bad_r = run_trace(ignore_contradiction, contradiction_trace)
    _s2, good_r = run_trace(independent_step, contradiction_trace)
    controls["ignore_contradiction_detected"] = bad_r[1] is True and good_r[1] is False

    def erase_history(s, op):
        ns, r = independent_step(s, op)
        if op == "ADVANCE" and r[0]:
            ns = (ns[0], ns[1], ns[2], ns[3], ns[4], ())
        return ns, r
    pre, _ = run_trace(independent_step, ["OBS0", "VALIDATE", "COMMIT"])
    bad, _ = erase_history(pre, "ADVANCE")
    good, _ = independent_step(pre, "ADVANCE")
    controls["erase_history_detected"] = bool(good[5]) and not bool(bad[5])

    return controls


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", required=True)
    ap.add_argument("--freeze", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    result_path = Path(args.result)
    freeze_path = Path(args.freeze)
    here = Path(__file__).resolve().parent
    result = json.loads(result_path.read_text(encoding="utf-8"))
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))

    independent_digest, im = audit_enumeration(8)
    corrupt = corruption_controls()

    source_checks = {
        "formal_sha256": sha256_file(here / "formal.py") == freeze["files"]["formal.py"],
        "audit_sha256": sha256_file(here / "audit.py") == freeze["files"]["audit.py"],
        "plan_sha256": sha256_file(here / "PLAN.md") == freeze["files"]["PLAN.md"],
    }
    expected_trace_count = sum(len(OPS) ** d for d in range(0, 9))
    result_metric_subset = {k: result["metrics"][k] for k in im}

    gates = {
        "result_decision_pass": result["decision"] == "PASS_TRANSACTIONAL_BELIEF_ACTION_SAFE_A2_SCOPED",
        "formal_once": result["formal_invocations"] == 1 and result["reruns"] == 0 and result["replacements"] == 0 and result["tuning_after_freeze"] == 0,
        "trace_count_exact": result["metrics"]["trace_count_including_empty"] == expected_trace_count == im["trace_count_including_empty"],
        "candidate_oracle_mismatch_zero": result["metrics"]["candidate_oracle_mismatch"] == 0,
        "candidate_oracle_digest_equal": result["candidate_digest"] == result["oracle_digest"],
        "independent_digest_matches": independent_digest == result["candidate_digest"] == result["oracle_digest"],
        "independent_metric_subset_matches": result_metric_subset == im,
        "no_stale_action_authority": im["stale_generation_action_safe_admissions"] == 0,
        "no_contradicted_action_authority": im["contradicted_action_safe_admissions"] == 0,
        "no_unvalidated_commit": im["commit_from_unvalidated_admissions"] == 0,
        "fresh_recommit_exists": im["fresh_recommit_action_safe"] > 0,
        "provenance_retained": im["provenance_retained_across_generation_change"] > 0,
        "comparator_discriminator_positive": im["committed_only_unsafe_stale_or_contradicted"] > 0,
        "source_integrity": all(source_checks.values()),
        "corruption_controls": all(corrupt.values()),
    }
    passed = all(gates.values())
    audit = {
        "task": "TRANSACTIONAL-BELIEF-ACTION-SAFE-A2-20260919-002",
        "decision": "PASS_AUDIT" if passed else "FAIL_AUDIT",
        "gates": gates,
        "independent_digest": independent_digest,
        "independent_metrics": im,
        "source_checks": source_checks,
        "corruption_controls": corrupt,
        "expected_trace_count": expected_trace_count,
        "audit_source_sha256": sha256_file(here / "audit.py"),
    }
    Path(args.output).write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
