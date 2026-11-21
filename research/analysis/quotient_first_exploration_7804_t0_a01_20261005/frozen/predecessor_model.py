"""Finite typed-identity symmetry-reduction experiment for Issue #6251.

This is a synthetic transition system only. It has no runtime, GUI, or I/O
authority. The independent checker intentionally does not import this module.
"""
from __future__ import annotations

import collections
import argparse
import itertools
import json
import pathlib
import sys

ACTORS = ("requester", "verifier_a", "verifier_b")
STATE_FIELDS = (
    "lease_holder",
    "replyers",
    "generation",
    "commit_by",
    "effect_target",
    "receipt_target",
)
IDENTITY = {actor: actor for actor in ACTORS}
SWAP_VERIFIERS = {
    "requester": "requester",
    "verifier_a": "verifier_b",
    "verifier_b": "verifier_a",
}


def world(**overrides):
    value = {
        "fixed_verifier": None,
        "fixed_lease_holder": None,
        "named_property_actor": None,
        "omit_effect_target": False,
    }
    value.update(overrides)
    return value


def permute_state(state, mapping):
    result = dict(state)
    for field in ("lease_holder", "commit_by", "replyers"):
        value = result[field]
        if field == "replyers":
            result[field] = sorted(mapping.get(actor, actor) for actor in value)
        elif value is not None:
            result[field] = mapping.get(value, value)
    return result


def _permuted_action(action, mapping):
    op, actor, target = action
    return (op, mapping.get(actor, actor) if actor is not None else None, target)


def _identity_key(state, omit_effect_target=False):
    fields = [field for field in STATE_FIELDS if not (omit_effect_target and field == "effect_target")]
    return tuple((field, tuple(state[field]) if field == "replyers" else state[field]) for field in fields)


def _canonical_form(state, permutations, omit_effect_target=False):
    forms = []
    for mapping in permutations:
        renamed = permute_state(state, mapping)
        forms.append((_identity_key(renamed, omit_effect_target), mapping))
    return min(forms, key=lambda item: repr(item[0]))


def typed_key(state, config):
    mappings = [IDENTITY]
    if not config["fixed_verifier"] and not config["fixed_lease_holder"] and not config["named_property_actor"]:
        mappings.append(SWAP_VERIFIERS)
    return repr(_canonical_form(state, mappings, config["omit_effect_target"])[0])


def _initial_state():
    return {
        "lease_holder": None,
        "replyers": [],
        "generation": 0,
        "commit_by": None,
        "effect_target": None,
        "receipt_target": None,
    }


def _transitions(state, config):
    out = []
    holder = state["lease_holder"]
    if holder is None:
        grantees = (config["fixed_lease_holder"],) if config["fixed_lease_holder"] else ("verifier_a", "verifier_b")
        for actor in grantees:
            if config["fixed_verifier"] and actor != config["fixed_verifier"]:
                continue
            nxt = dict(state, lease_holder=actor)
            out.append((("grant", actor, None), nxt))
    else:
        out.append((("revoke", holder, None), dict(state, lease_holder=None)))
    if state["generation"] == 0:
        out.append((("observation_stale", None, None), dict(state, generation=1)))
    for actor in ("verifier_a", "verifier_b"):
        if actor not in state["replyers"]:
            out.append((("reply", actor, None), dict(state, replyers=sorted(state["replyers"] + [actor]))))
        else:
            # Duplicate replies are retained as an explicit self-loop event.
            out.append((("duplicate_reply", actor, None), dict(state)))
    if state["commit_by"] is None:
        for actor in ACTORS:
            for target in ("record_x", "record_y"):
                nxt = dict(state, commit_by=actor, effect_target=target, receipt_target=None)
                out.append((("commit", actor, target), nxt))
    elif state["receipt_target"] is None:
        out.append((("effect_receipt", state["commit_by"], state["effect_target"]),
                    dict(state, receipt_target=state["effect_target"])))
    return out


def _predicates(state, config):
    committed = state["commit_by"] is not None
    values = {
        "requester_committed": committed and state["commit_by"] == "requester",
        "commit_without_lease_owner": committed and state["commit_by"] != state["lease_holder"],
        "commit_on_stale_observation": committed and state["generation"] != 0,
        "wrong_effect_target": committed and state["effect_target"] != "record_x",
        "receipt_target_mismatch": committed and state["receipt_target"] is not None and state["receipt_target"] != state["effect_target"],
    }
    if config["named_property_actor"]:
        values["named_actor_committed"] = committed and state["commit_by"] == config["named_property_actor"]
    return values


def _unsafe(state, config):
    return any(_predicates(state, config).values())


def _state_id(state):
    return _identity_key(state)


def _enumerate(config):
    initial = _initial_state()
    start = _state_id(initial)
    states = {start: initial}
    parent = {start: None}
    todo = collections.deque([start])
    while todo:
        current_id = todo.popleft()
        current = states[current_id]
        for action, nxt in _transitions(current, config):
            nxt_id = _state_id(nxt)
            if nxt_id in states:
                continue
            states[nxt_id] = nxt
            parent[nxt_id] = (current_id, action)
            todo.append(nxt_id)
    return states, parent


def _trace_to(state_id, states, parent):
    reversed_steps = []
    cursor = state_id
    while parent[cursor] is not None:
        previous, action = parent[cursor]
        reversed_steps.append({"action": list(action), "state": states[cursor]})
        cursor = previous
    return list(reversed(reversed_steps))


def _transition_equivariant(states, config, mappings):
    checked = 0
    for state in states.values():
        for mapping in mappings:
            transformed = permute_state(state, mapping)
            expected = {
                (_permuted_action(action, mapping), _state_id(permute_state(nxt, mapping)))
                for action, nxt in _transitions(state, config)
            }
            actual = {(action, _state_id(nxt)) for action, nxt in _transitions(transformed, config)}
            checked += 1
            if expected != actual:
                return False, checked
    return True, checked


def _property_invariant(states, config, mappings):
    checked = 0
    for state in states.values():
        for mapping in mappings:
            transformed = permute_state(state, mapping)
            if _predicates(state, config) != _predicates(transformed, config):
                return False, checked + 1
            checked += 1
    return True, checked


def _naive_counterexample_loss(states, config):
    all_permutations = [dict(zip(ACTORS, p)) for p in itertools.permutations(ACTORS)]
    classes = collections.defaultdict(set)
    for state in states.values():
        key = _canonical_form(state, all_permutations)[0]
        classes[key].add(tuple(sorted(_predicates(state, config).items())))
    mismatched = [key for key, predicate_sets in classes.items() if len(predicate_sets) > 1]
    return bool(mismatched), len(mismatched)


def reduce_world(config):
    states, parent = _enumerate(config)
    mappings = [IDENTITY]
    if not config["fixed_verifier"] and not config["fixed_lease_holder"] and not config["named_property_actor"]:
        mappings.append(SWAP_VERIFIERS)
    transitions_ok, transition_checks = _transition_equivariant(states, config, mappings)
    properties_ok, property_checks = _property_invariant(states, config, mappings)
    groups = collections.defaultdict(list)
    for sid, state in states.items():
        groups[typed_key(state, config)].append(sid)
    collision = any(
        len({tuple(sorted(_predicates(states[sid], config).items())) for sid in members}) > 1
        for members in groups.values()
    )
    declared_identity_breaker = bool(
        config["fixed_verifier"] or config["fixed_lease_holder"] or config["named_property_actor"]
    )
    fallback = declared_identity_breaker or not transitions_ok or not properties_ok or collision
    if fallback:
        mappings = [IDENTITY]
        groups = collections.defaultdict(list)
        for sid, state in states.items():
            groups[repr(_identity_key(state))].append(sid)
    unsafe_states = {sid for sid, state in states.items() if _unsafe(state, config)}
    unsafe_classes = []
    expanded = []
    for key, members in groups.items():
        bad = [sid for sid in members if sid in unsafe_states]
        if not bad:
            continue
        unsafe_classes.append(key)
        representative_id = sorted(bad)[0]
        representative = states[representative_id]
        _, mapping = _canonical_form(representative, mappings, config["omit_effect_target"] and not fallback)
        inverse = {value: key for key, value in mapping.items()}
        trace = _trace_to(representative_id, states, parent)
        expanded.append({
            "quotient_key": key,
            "concrete_state": representative,
            "canonical_to_named": inverse,
            "trace": trace,
            "replay_valid": _replay(trace, config),
        })
    naive_loses, naive_classes = _naive_counterexample_loss(states, config)
    return {
        "full_state_count": len(states),
        "quotient_state_count": len(groups),
        "unsafe_full_count": len(unsafe_states),
        "unsafe_quotient_count": len(unsafe_classes),
        "unsafe_exists_full": bool(unsafe_states),
        "unsafe_exists_quotient": bool(unsafe_classes),
        "transition_equivariant": transitions_ok,
        "transition_checks": transition_checks,
        "property_invariant": properties_ok,
        "property_checks": property_checks,
        "fallback_to_named_states": fallback,
        "fallback_reason": (
            "declared_identity_breaker" if declared_identity_breaker else
            "property_or_transition_not_invariant" if fallback else None
        ),
        "naive_all_id_loses_property_distinction": naive_loses,
        "naive_mismatched_classes": naive_classes,
        "counterexample_witnesses": expanded,
        "all_counterexamples_expand": all(row["replay_valid"] for row in expanded),
    }


def _replay(trace, config):
    state = _initial_state()
    for row in trace:
        action = tuple(row["action"])
        if not any(candidate_action == action and _state_id(candidate_state) == _state_id(row["state"])
                   for candidate_action, candidate_state in _transitions(state, config)):
            return False
        state = row["state"]
    return bool(trace) and _unsafe(state, config)


def run():
    symmetric = reduce_world(world())
    mutations = {
        "verifier_owner_specific": reduce_world(world(fixed_verifier="verifier_a")),
        "lease_holder_identity_bound": reduce_world(world(fixed_lease_holder="verifier_a")),
        "property_names_verifier": reduce_world(world(named_property_actor="verifier_a")),
        "effect_target_omitted_from_key": reduce_world(world(omit_effect_target=True)),
    }
    rejected = all(row["fallback_to_named_states"] for row in mutations.values())
    return {
        "schema": "issue6251-symmetry-t0-host-v1",
        "model": {
            "actors": list(ACTORS),
            "initial_state": _initial_state(),
            "transitions": ["grant/revoke lease", "stale observation", "reply/duplicate reply", "commit effect", "effect receipt"],
            "bounded_reachable_state_enumeration": True,
            "property_predicates": ["requester_committed", "commit_without_lease_owner", "commit_on_stale_observation", "wrong_effect_target", "receipt_target_mismatch"],
        },
        "symmetric": symmetric,
        "mutations": mutations,
        "mutation_controls_rejected": rejected,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(run(), sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "schema": "issue6251-symmetry-t0-host-v1"}, sort_keys=True))
