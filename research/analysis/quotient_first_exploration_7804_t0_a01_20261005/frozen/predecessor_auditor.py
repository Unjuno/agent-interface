"""Independent raw-only checker for Issue #6251's bounded finite model.

This file re-encodes the transition system with integer actor IDs and tuple
states. It intentionally does not import candidate.py.
"""
from __future__ import annotations

import argparse
import collections
import itertools
import json
import pathlib
import sys

REQUESTER, VERIFIER_A, VERIFIER_B = 0, 1, 2
ACTORS = (REQUESTER, VERIFIER_A, VERIFIER_B)
ROLE_NAMES = {REQUESTER: "requester", VERIFIER_A: "verifier_a", VERIFIER_B: "verifier_b"}
ID = {actor: actor for actor in ACTORS}
SWAP = {REQUESTER: REQUESTER, VERIFIER_A: VERIFIER_B, VERIFIER_B: VERIFIER_A}
# Tuple order: holder, reply bitmask, observation generation, committer, target, receipt.
INITIAL = (None, 0, 0, None, None, None)


def _from_named(state):
    actor = {name: number for number, name in ROLE_NAMES.items()}
    mask = sum(1 << actor[name] for name in state["replyers"])
    return (
        actor.get(state["lease_holder"]), mask, state["generation"],
        actor.get(state["commit_by"]), state["effect_target"], state["receipt_target"],
    )


def _to_named(state):
    holder, mask, generation, committer, target, receipt = state
    return {
        "lease_holder": ROLE_NAMES.get(holder),
        "replyers": [ROLE_NAMES[actor] for actor in (VERIFIER_A, VERIFIER_B) if mask & (1 << actor)],
        "generation": generation,
        "commit_by": ROLE_NAMES.get(committer),
        "effect_target": target,
        "receipt_target": receipt,
    }


def _rename(state, permutation):
    holder, mask, generation, committer, target, receipt = state
    renamed_mask = sum(1 << permutation[actor] for actor in ACTORS if mask & (1 << actor))
    return (permutation.get(holder, holder), renamed_mask, generation,
            permutation.get(committer, committer), target, receipt)


def _enabled_permutations(config):
    if config["fixed_verifier"] or config["fixed_lease_holder"] or config["named_property_actor"]:
        return [ID]
    return [ID, SWAP]


def _key(state, omit_target=False):
    if omit_target:
        holder, replies, generation, committer, _, receipt = state
        return (holder, replies, generation, committer, receipt)
    return state


def _canonical_key(state, config):
    keys = [_key(_rename(state, p), config["omit_effect_target"]) for p in _enabled_permutations(config)]
    return min(keys, key=repr)


def _predicates(state, config):
    holder, _, generation, committer, target, receipt = state
    committed = committer is not None
    result = {
        "requester_committed": committed and committer == REQUESTER,
        "commit_without_lease_owner": committed and committer != holder,
        "commit_on_stale_observation": committed and generation != 0,
        "wrong_effect_target": committed and target != "record_x",
        "receipt_target_mismatch": committed and receipt is not None and receipt != target,
    }
    if config["named_property_actor"]:
        named = {value: key for key, value in ROLE_NAMES.items()}[config["named_property_actor"]]
        result["named_actor_committed"] = committed and committer == named
    return result


def _edges(state, config):
    holder, replies, generation, committer, target, receipt = state
    edges = []
    if holder is None:
        if config["fixed_lease_holder"]:
            names = [config["fixed_lease_holder"]]
        elif config["fixed_verifier"]:
            names = [config["fixed_verifier"]]
        else:
            names = ["verifier_a", "verifier_b"]
        for name in names:
            number = {value: key for key, value in ROLE_NAMES.items()}[name]
            edges.append((("grant", number, None), (number, replies, generation, committer, target, receipt)))
    else:
        edges.append((("revoke", holder, None), (None, replies, generation, committer, target, receipt)))
    if generation == 0:
        edges.append((("observation_stale", None, None), (holder, replies, 1, committer, target, receipt)))
    for verifier in (VERIFIER_A, VERIFIER_B):
        bit = 1 << verifier
        op = "duplicate_reply" if replies & bit else "reply"
        edges.append(((op, verifier, None), (holder, replies | bit, generation, committer, target, receipt)))
    if committer is None:
        for actor in ACTORS:
            for effect in ("record_x", "record_y"):
                edges.append((("commit", actor, effect), (holder, replies, generation, actor, effect, None)))
    elif receipt is None:
        edges.append((("effect_receipt", committer, target), (holder, replies, generation, committer, target, target)))
    return edges


def _explore(config):
    seen = {INITIAL}
    parents = {INITIAL: None}
    queue = collections.deque([INITIAL])
    while queue:
        state = queue.popleft()
        for _, nxt in _edges(state, config):
            if nxt not in seen:
                seen.add(nxt)
                parents[nxt] = state
                queue.append(nxt)
    return seen, parents


def _equivariance(states, config):
    mappings = _enabled_permutations(config)
    tested = 0
    for state in states:
        for permutation in mappings:
            mapped_state = _rename(state, permutation)
            expected = {
                (_rename_action(action, permutation), _rename(nxt, permutation))
                for action, nxt in _edges(state, config)
            }
            observed = set(_edges(mapped_state, config))
            tested += 1
            if expected != observed:
                return False, tested
    return True, tested


def _rename_action(action, permutation):
    op, actor, target = action
    return (op, permutation.get(actor, actor) if actor is not None else None, target)


def _property_check(states, config):
    tested = 0
    for state in states:
        original = _predicates(state, config)
        for permutation in _enabled_permutations(config):
            tested += 1
            if original != _predicates(_rename(state, permutation), config):
                return False, tested
    return True, tested


def _trace(state, parents):
    path = []
    cursor = state
    while parents[cursor] is not None:
        previous = parents[cursor]
        action = next(action for action, nxt in _edges(previous, _ACTIVE_CONFIG[0]) if nxt == cursor)
        path.append((action, cursor))
        cursor = previous
    path.reverse()
    return path


_ACTIVE_CONFIG = [None]


def _replay_witness(witness, config):
    current = INITIAL
    for row in witness["trace"]:
        named_action = row["action"]
        action = (named_action[0], {value: key for key, value in ROLE_NAMES.items()}.get(named_action[1]), named_action[2])
        nxt = _from_named(row["state"])
        if (action, nxt) not in _edges(current, config):
            return False
        current = nxt
    return bool(witness["trace"]) and any(_predicates(current, config).values()) and current == _from_named(witness["concrete_state"])


def _independent_summary(config):
    _ACTIVE_CONFIG[0] = config
    states, parents = _explore(config)
    groups = collections.defaultdict(list)
    for state in states:
        groups[_canonical_key(state, config)].append(state)
    group_predicate_collision = any(
        len({tuple(sorted(_predicates(state, config).items())) for state in members}) > 1
        for members in groups.values()
    )
    equivariant, edge_checks = _equivariance(states, config)
    invariant, property_checks = _property_check(states, config)
    breaker = bool(config["fixed_verifier"] or config["fixed_lease_holder"] or config["named_property_actor"])
    fallback = breaker or not equivariant or not invariant or group_predicate_collision
    if fallback:
        groups = collections.defaultdict(list)
        for state in states:
            groups[_key(state)] .append(state)
    unsafe = {state for state in states if any(_predicates(state, config).values())}
    unsafe_groups = []
    witnesses = []
    for key, members in groups.items():
        bad = [state for state in members if state in unsafe]
        if not bad:
            continue
        unsafe_groups.append(key)
        concrete = sorted(bad, key=repr)[0]
        path = _trace(concrete, parents)
        witnesses.append((key, concrete, path))
    return {
        "full_state_count": len(states),
        "quotient_state_count": len(groups),
        "unsafe_full_count": len(unsafe),
        "unsafe_quotient_count": len(unsafe_groups),
        "unsafe_exists_full": bool(unsafe),
        "unsafe_exists_quotient": bool(unsafe_groups),
        "transition_equivariant": equivariant,
        "transition_checks": edge_checks,
        "property_invariant": invariant,
        "property_checks": property_checks,
        "fallback_to_named_states": fallback,
        "fallback_reason": "declared_identity_breaker" if breaker else ("property_or_transition_not_invariant" if fallback else None),
        "naive_all_id_loses_property_distinction": None,
        "naive_mismatched_classes": None,
        "witnesses": witnesses,
    }


def _naive_check():
    config = {"fixed_verifier": None, "fixed_lease_holder": None, "named_property_actor": None, "omit_effect_target": False}
    states, _ = _explore(config)
    all_maps = [dict(zip(ACTORS, row)) for row in itertools.permutations(ACTORS)]
    partitions = collections.defaultdict(set)
    for state in states:
        key = min((_rename(state, p) for p in all_maps), key=repr)
        partitions[key].add(tuple(sorted(_predicates(state, config).items())))
    bad = sum(len(values) > 1 for values in partitions.values())
    return bad > 0, bad


def audit_result(result):
    errors = []
    configs = {
        "symmetric": {"fixed_verifier": None, "fixed_lease_holder": None, "named_property_actor": None, "omit_effect_target": False},
        "verifier_owner_specific": {"fixed_verifier": "verifier_a", "fixed_lease_holder": None, "named_property_actor": None, "omit_effect_target": False},
        "lease_holder_identity_bound": {"fixed_verifier": None, "fixed_lease_holder": "verifier_a", "named_property_actor": None, "omit_effect_target": False},
        "property_names_verifier": {"fixed_verifier": None, "fixed_lease_holder": None, "named_property_actor": "verifier_a", "omit_effect_target": False},
        "effect_target_omitted_from_key": {"fixed_verifier": None, "fixed_lease_holder": None, "named_property_actor": None, "omit_effect_target": True},
    }
    for name, config in configs.items():
        if name not in result if name == "symmetric" else name not in result.get("mutations", {}):
            errors.append(f"missing result {name}")
            continue
        reported = result[name] if name == "symmetric" else result["mutations"][name]
        expected = _independent_summary(config)
        for field in (
            "full_state_count", "quotient_state_count", "unsafe_full_count", "unsafe_quotient_count",
            "unsafe_exists_full", "unsafe_exists_quotient", "transition_equivariant", "transition_checks",
            "property_invariant", "property_checks", "fallback_to_named_states", "fallback_reason",
        ):
            if reported.get(field) != expected[field]:
                errors.append(f"{name}.{field} mismatch: {reported.get(field)!r} != {expected[field]!r}")
        if name == "symmetric":
            lost, lost_classes = _naive_check()
            if reported.get("naive_all_id_loses_property_distinction") != lost:
                errors.append("naive all-ID property-loss result mismatch")
            if reported.get("naive_mismatched_classes") != lost_classes:
                errors.append("naive all-ID mismatch-class count mismatch")
            claimed = reported.get("counterexample_witnesses", [])
            expected_witnesses = expected["witnesses"]
            if len(claimed) != len(expected_witnesses):
                errors.append("witness count mismatch")
            for witness in claimed:
                if not _replay_witness(witness, config):
                    errors.append("counterexample witness failed independent named-trace replay")
                    break
    mutation_names = ("verifier_owner_specific", "lease_holder_identity_bound", "property_names_verifier", "effect_target_omitted_from_key")
    if result.get("mutation_controls_rejected") is not all(
        result.get("mutations", {}).get(name, {}).get("fallback_to_named_states") for name in mutation_names
    ):
        errors.append("mutation-control aggregate mismatch")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate_json", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args(argv)
    payload = json.loads(args.candidate_json.read_text(encoding="utf-8"))
    errors = audit_result(payload)
    record = {"schema": "issue6251-independent-audit-v1", "errors": errors,
              "disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT"}
    args.output.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
