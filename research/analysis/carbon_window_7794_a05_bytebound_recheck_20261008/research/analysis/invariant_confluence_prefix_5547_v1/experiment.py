"""Finite interface-operation model for Issue #5547; stdlib only."""
from dataclasses import dataclass
from itertools import product


@dataclass(frozen=True)
class State:
    evidence: frozenset = frozenset()
    grants: frozenset = frozenset()
    revocations: frozenset = frozenset()
    epoch: int = 0
    admissions: frozenset = frozenset()
    invalidated: frozenset = frozenset()
    reservations: frozenset = frozenset()
    commits: frozenset = frozenset()


INITIAL = State()
QUOTA_LIMIT = 1
AUTHORITY_LIMIT = 1


def invariant_violations(state):
    violations = []
    effective = state.grants - state.revocations
    if len(effective) > AUTHORITY_LIMIT:
        violations.append("authority_capacity")
    if len(state.reservations) > QUOTA_LIMIT:
        violations.append("quota_capacity")
    active_admissions = [item for item in state.admissions
                         if item[0] not in state.invalidated]
    if any(admitted_epoch != state.epoch
           for _, admitted_epoch in active_admissions):
        violations.append("stale_admission_active")
    by_effect = {}
    for _, effect_id in state.commits:
        by_effect[effect_id] = by_effect.get(effect_id, 0) + 1
    if any(count > 1 for count in by_effect.values()):
        violations.append("duplicate_semantic_effect")
    if state.revocations & effective:
        violations.append("revoked_authority_active")
    return sorted(violations)


def join(left, right):
    return State(
        evidence=left.evidence | right.evidence,
        grants=left.grants | right.grants,
        revocations=left.revocations | right.revocations,
        epoch=max(left.epoch, right.epoch),
        admissions=left.admissions | right.admissions,
        invalidated=left.invalidated | right.invalidated,
        reservations=left.reservations | right.reservations,
        commits=left.commits | right.commits,
    )


def transition(state, command):
    """Return a new locally valid state, or None for a rejected command."""
    kind, value = command
    if kind == "ADD_EVIDENCE":
        return State(**{**state.__dict__, "evidence": state.evidence | {value}})
    if kind == "GRANT_TOKEN":
        if len(state.grants - state.revocations) >= AUTHORITY_LIMIT and value not in state.grants:
            return None
        return State(**{**state.__dict__, "grants": state.grants | {value}})
    if kind == "REVOKE_CLAIM":
        return State(**{**state.__dict__, "revocations": state.revocations | {value}})
    if kind == "REFRESH_EPOCH":
        if value <= state.epoch:
            return None
        invalid = state.invalidated | frozenset(
            admission_id for admission_id, admitted_epoch in state.admissions
            if admitted_epoch < value
        )
        return State(**{**state.__dict__, "epoch": value, "invalidated": invalid})
    if kind == "RESERVE_QUOTA":
        if len(state.reservations) >= QUOTA_LIMIT:
            return None
        return State(**{**state.__dict__, "reservations": state.reservations | {value}})
    if kind == "ADMIT_EFFECT":
        admission_id, expected_epoch = value
        if expected_epoch != state.epoch:
            return None
        return State(**{**state.__dict__, "admissions": state.admissions | {(admission_id, expected_epoch)}})
    if kind == "COMMIT_EFFECT":
        dispatch_id, effect_id = value
        if any(existing_effect == effect_id for _, existing_effect in state.commits):
            return None
        return State(**{**state.__dict__, "commits": state.commits | {(dispatch_id, effect_id)}})
    return None


COMMANDS = (
    ("ADD_EVIDENCE", "e0"), ("ADD_EVIDENCE", "e1"),
    ("GRANT_TOKEN", "cap0"), ("GRANT_TOKEN", "cap1"),
    ("REVOKE_CLAIM", "cap0"), ("REVOKE_CLAIM", "cap1"),
    ("REFRESH_EPOCH", 1),
    ("RESERVE_QUOTA", "r0"), ("RESERVE_QUOTA", "r1"),
    ("ADMIT_EFFECT", ("a0", 0)), ("ADMIT_EFFECT", ("a1", 0)),
    ("COMMIT_EFFECT", ("d0", "effect0")),
    ("COMMIT_EFFECT", ("d1", "effect0")),
)

EXPECTED_CONFLICT_FAMILIES = {
    ("ADMIT_EFFECT", "REFRESH_EPOCH"),
    ("COMMIT_EFFECT", "COMMIT_EFFECT"),
    ("GRANT_TOKEN", "GRANT_TOKEN"),
    ("RESERVE_QUOTA", "RESERVE_QUOTA"),
}


def state_dict(state):
    serial_safe = all(not row["serial_invariant_errors"] for row in rows)
    joins_commute = all(row["join_lr"] == row["join_rl"] for row in rows)
    return {
        "evidence": sorted(state.evidence),
        "grants": sorted(state.grants),
        "revocations": sorted(state.revocations),
        "epoch": state.epoch,
        "admissions": sorted([list(x) for x in state.admissions]),
        "invalidated": sorted(state.invalidated),
        "reservations": sorted(state.reservations),
        "commits": sorted([list(x) for x in state.commits]),
    }


def state_from_dict(row):
    return State(
        evidence=frozenset(row["evidence"]),
        grants=frozenset(row["grants"]),
        revocations=frozenset(row["revocations"]),
        epoch=row["epoch"],
        admissions=frozenset((item[0], item[1]) for item in row["admissions"]),
        invalidated=frozenset(row["invalidated"]),
        reservations=frozenset(row["reservations"]),
        commits=frozenset((item[0], item[1]) for item in row["commits"]),
    )


def command_dict(command):
    return {"kind": command[0], "value": command[1]}


def execute():
    rows = []
    conflict_pairs = set()
    for left_command, right_command in product(COMMANDS, repeat=2):
        left = transition(INITIAL, left_command)
        right = transition(INITIAL, right_command)
        if left is None or right is None:
            continue
        merged_lr = join(left, right)
        merged_rl = join(right, left)
        merged_errors = invariant_violations(merged_lr)
        if merged_errors:
            family = tuple(sorted((left_command[0], right_command[0])))
            conflict_pairs.add(family)
        serial_lr_mid = transition(left, right_command)
        serial_rl_mid = transition(right, left_command)
        serial_lr = left if serial_lr_mid is None else serial_lr_mid
        serial_rl = right if serial_rl_mid is None else serial_rl_mid
        serial_errors = sorted(set(invariant_violations(serial_lr) + invariant_violations(serial_rl)))
        rows.append({
            "left": command_dict(left_command),
            "right": command_dict(right_command),
            "left_state": state_dict(left),
            "right_state": state_dict(right),
            "join_lr": state_dict(merged_lr),
            "join_rl": state_dict(merged_rl),
            "join_invariant_errors": merged_errors,
            "serial_lr_state": state_dict(serial_lr),
            "serial_rl_state": state_dict(serial_rl),
            "serial_invariant_errors": serial_errors,
        })
    conflicts = sorted([list(pair) for pair in conflict_pairs])
    expected = sorted([list(pair) for pair in EXPECTED_CONFLICT_FAMILIES])
    safe_families = {"ADD_EVIDENCE", "REVOKE_CLAIM"}
    safe_operation_pairs = all(
        not row["join_invariant_errors"]
        for row in rows
        if row["left"]["kind"] in safe_families or row["right"]["kind"] in safe_families
    )
    conflict_participants = {kind for pair in conflict_pairs for kind in pair}
    classifications = {
        kind: ("coordination_required" if kind in conflict_participants else "monotone_safe")
        for kind in sorted({command[0] for command in COMMANDS})
    }
    classifications["UNKNOWN_SCHEMA"] = "coordination_required"
    return {
        "schema": "issue-5547-invariant-confluence-raw-v1",
        "allocation": "ic-prefix-finite-model-5547-20261001-01",
        "source_main": "59ffec5d551b0adcf11057eee6da814237a748c8",
        "command_count": len(COMMANDS),
        "ordered_pair_count": len(rows),
        "pair_rows": rows,
        "actual_conflict_families": conflicts,
        "expected_conflict_families": expected,
        "classifications": classifications,
        "all_join_argument_orders_equal": joins_commute,
        "serial_baseline_invariant_safe": serial_safe,
        "safe_operation_pairs_invariant_safe": safe_operation_pairs,
        "disposition": "PASS_BOUNDED_FINITE_MODEL" if conflicts == expected and safe_operation_pairs and serial_safe and joins_commute else "FAIL_OR_UNCERTAIN",
    }
