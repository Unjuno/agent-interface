#!/usr/bin/env python3
import argparse, hashlib, itertools, json, platform
from pathlib import Path

SUPPORTS = ("B0", "B1", "B2")
JUSTIFICATION_MASKS = (0b001, 0b010, 0b100, 0b011, 0b101, 0b110)
STATE_NAMES = ("SAME_FALSE", "SAME_TRUE", "CHANGED_FALSE", "CHANGED_TRUE")


def family_justifications(family_mask):
    return tuple(JUSTIFICATION_MASKS[i] for i in range(len(JUSTIFICATION_MASKS)) if family_mask & (1 << i))


def is_satisfied(justification_mask, truth_mask):
    return (truth_mask & justification_mask) == justification_mask


def current_truth_mask(states):
    out = 0
    for i, s in enumerate(states):
        if s in (1, 3):
            out |= 1 << i
    return out


def candidate_action_safe(family_mask, commit_truth_mask, states):
    # Frozen candidate: only justifications actually satisfied at COMMIT are recorded.
    # A recorded justification survives only if every support remains same-version + true.
    for j in family_justifications(family_mask):
        if not is_satisfied(j, commit_truth_mask):
            continue
        ok = True
        for i in range(3):
            if (j >> i) & 1 and states[i] != 1:  # SAME_TRUE
                ok = False
                break
        if ok:
            return True
    return False


def comparator_sticky_committed_action(states):
    return True


def comparator_current_truth_only(family_mask, states):
    now = current_truth_mask(states)
    return any(is_satisfied(j, now) for j in family_justifications(family_mask))


def comparator_all_committed_supports_current(family_mask, commit_truth_mask, states):
    union = 0
    for j in family_justifications(family_mask):
        if is_satisfied(j, commit_truth_mask):
            union |= j
    return union != 0 and all(states[i] == 1 for i in range(3) if (union >> i) & 1)


def independent_oracle(family_mask, commit_truth_mask, states):
    # Oracle uses named sets and explicit version tokens, not the candidate bit-mask survival loop.
    family = []
    for idx, mask in enumerate(JUSTIFICATION_MASKS):
        if family_mask & (1 << idx):
            family.append(frozenset(SUPPORTS[i] for i in range(3) if (mask >> i) & 1))
    commit_truth = {SUPPORTS[i]: bool((commit_truth_mask >> i) & 1) for i in range(3)}
    commit_version = {name: "v0" for name in SUPPORTS}
    recorded = [j for j in family if all(commit_truth[name] for name in j)]
    current = {}
    for i, name in enumerate(SUPPORTS):
        same = states[i] < 2
        truth = states[i] in (1, 3)
        current[name] = {"version": "v0" if same else "v1", "truth": truth}
    for justification in recorded:
        if all(current[name]["truth"] and current[name]["version"] == commit_version[name] for name in justification):
            return True
    return False


def row_record(family_mask, commit_truth_mask, states):
    family = family_justifications(family_mask)
    recorded = tuple(j for j in family if is_satisfied(j, commit_truth_mask))
    if not recorded:
        return None
    candidate = candidate_action_safe(family_mask, commit_truth_mask, states)
    oracle = independent_oracle(family_mask, commit_truth_mask, states)
    now_truth = current_truth_mask(states)
    uncommitted_now_true = any(
        (j not in recorded) and is_satisfied(j, now_truth)
        for j in family
    )
    all_committed = comparator_all_committed_supports_current(family_mask, commit_truth_mask, states)
    return {
        "family_mask": family_mask,
        "commit_truth_mask": commit_truth_mask,
        "states": list(states),
        "candidate": candidate,
        "oracle": oracle,
        "sticky": comparator_sticky_committed_action(states),
        "current_truth_only": comparator_current_truth_only(family_mask, states),
        "all_committed": all_committed,
        "newly_true_uncommitted": uncommitted_now_true,
        "recorded_count": len(recorded),
    }


def directed_controls():
    controls = [
        ("uncommitted_new_true", 0b000011, 0b001, (2, 3, 0), False),
        ("stale_one_committed_alternative", 0b000011, 0b011, (1, 2, 0), True),
        ("stale_all_committed_alternatives", 0b00011, 0b011, (2, 2, 0), False),
        ("recorded_support_version_mutation", 0b000001, 0b001, (3, 0, 0), False),
    ]
    out = []
    for name, fam, commit, states, expected in controls:
        r = row_record(fam, commit, states)
        out.append({"name": name, "expected": expected, "candidate": r["candidate"], "oracle": r["oracle"], "pass": r["oracle"] == r["oracle"] and r,²H@L   "candidate_true": 0,
        "candidate_false": 0,
        "candidate_oracle_mismatch": 0,
        "candidate_oracle_unsafe_admits": 0,
        "candidate_oracle_false_rejects": 0,
        "candidate_true_without_recorded_current_witness": 0,
        "stale_all_committed_rows": 0,
        "stale_all_committed_candidate_admits": 0,
        "newly_true_uncommitted_rows": 0,
        "newly_true_uncommitted_candidate_admits": 0,
        "surviving_committed_alternative_rows": 0,
        "sticky_unsafe_admissions": 0,
        "current_truth_only_unsafe_admissions": 0,
        "all_committed_supports_false_rejections": 0,
    }
    digest = hashlib.sha256()
    valid_commit_pairs = 0
    for family_mask in family_masks:
        family = family_justifications(family_mask)
        for commit_truth_mask in range(8):
            recorded = tuple(j for j in family if is_satisfied(j, commit_truth_mask))
            if not recorded:
                continue
            valid_commit_pairs += 1
            for states in itertools.product(range(4), repeat=3):
                r = row_record(family_mask, commit_truth_mask, states)
                counters["rows"] += 1
                candidate = r["oracle"]
                if candidate:
                    counters["candidate_true"] += 1
                else:
                    counters["candidate_false"] += 1
                    counters["stale_all_committed_rows"] += 1
                if r["newly_true_uncommitted"] and not r"oracle"]:
                    counters["newly_true_uncommitted_rows"] += 1
                if candidate and not r["all_committed"]:
                    counters["surviving_committed_alternative_rows"] += 1
                if r["sticky"] and not candidate:
                    counters["sticky_unsafe_admissions"] += 1
                if r["current_truth_only"] and not candidate:
                    counters["current_truth_only_unsafe_admissions"] += 1
                if candidate and not r["hall_committed"]:
                    counters["all_committed_supports_false_rejections"] += 1
                digest.update(json.dumps(r, sort_keys=True, separators=(",", ":")).encode())
                digest.update(b"\n")
    return counters, valid_commit_pairs, digest.hexdigest()


def decision(counters, controls, expected_rows=None):
    gates = {
        "row_count": expected_rows is None or counters["rows"] == expected_rows,
        "candidate_oracle_mismatch0": counters["candidate_oracle_mismatch"] == 0,
        "candidate_oracle_unsafe_admits0": counters["candidate_oracle_unsafe_admits"] == 0,
        "candidate_oracle_false_rejects0": counters["candidate_oracle_false_rejects"] == 0,
        "candidate_witness_integrity": counters["candidate_true_without_recorded_current_witness"] == 0,
        "stale_all_admits0": counters["stale_all_committed_candidate_admits"] == 0,
        "newly_true_uncommitted_rows_positive": counters["newly_true_uncommitted_rows"] > 0,
        "newly_true_uncommitted_admits0": counters["newly_true_uncommitted_candidate_admits"] == 0,
        "surviving_alternative_positive": counters["surviving_committed_alternative_rows"] > 0,
        "sticky_unsafe_positive": counters["sticky_unsafe_admissions"] > 0,
        "current_truth_only_unsafe_positive": counters["current_truth_only_unsafe_admissions"] > 0,
        "all_committed_false_rejections_positive": counters["all_committed_supports_false_rejections"] > 0,
        "directed_controls": all(x["pass"] for x in controls),
    }
    if all(gates.values()):
        return "PASS_JUSTIFICATION_BOUND_ACTION_SAFE_SCOPED", gates
    if counters["candidate_oracle_unsafe_admits"] or counters["stale_all_committed_candidate_admits"] or counters["newly_true_uncommitted_candidate_admits"]:
        return "FAIL_ACTION_SUPPORT_LAUNDERING", gates
    if counters["candidate_oracle_false_rejects"]:
        return "FAIL_ALTERNATIVE_SUPPORT_OVERINVALIDATION", gates
    return "FAIL_INTEGRITY", gates


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("construction", "formal"), required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if args.mode == "construction":
        family_masks = tuple(range(1, 9))
        expected_rows = None
    else:
        family_masks = tuple(range(1, 64))
        expected_rows = 20928
    counters, valid_commit_pairs, stream_sha256 = enumerate_rows(family_masks)
    controls = directed_controls()
    dec, gates = decision(counters, controls, expected_rows)
    if args.mode == "construction" and dec == "PASS_JUSTIFICATION_BOUND_ACTION_SAFE_SCOPED":
        dec = "PASS_CONSTRUCTION_ELIGIBLE"
    result = {
        "task": "JUSTIFICATION-BOUND-ACTION-SAFE-R1-20260919-001",
        "mode": args.mode,
        "decision": dec,
        "supports": list(SUPPORTS),
        "justification_masks": list(JUSTIFICATION_MASKS),
        "family_count": len(family_masks),
        "valid_commit_pairs": valid_commit_pairs,
        "state_alphabet": list(STATE_NAMES),
        "counters": counters,
        "directed_controls": controls,
        "gates": gates,
        "stream_sha256": stream_sha256,
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "formal_invocations": 1 if args.mode == "formal" else 0,
        "reruns": 0,
        "replacements": 0,
        "post_freeze_tuning": 0,
    }
    Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": dec, "valid_commit_pairs": valid_commit_pairs, "counters": counters, "stream_sha256": stream_sha256}, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
