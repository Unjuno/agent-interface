#!/usr/bin/env python3
"""Quotient-first candidate over the byte-frozen #6251 model module."""
import collections
import itertools
import json
import sys
import predecessor_model as model

FIELDS = model.STATE_FIELDS
ACTORS = model.ACTORS
IDENTITY = model.IDENTITY
SWAP = model.SWAP_VERIFIERS
INITIAL = model._initial_state()


def canonical(state, group, omit=False):
    key, mapping = model._canonical_form(state, group, omit)
    return model.permute_state(state, mapping), mapping


def bfs(config, group=None, omit=False):
    if group is None:
        group = [IDENTITY]
    start_state, _ = canonical(INITIAL, group, omit)
    start = model._state_id(start_state)
    states = {start: start_state}
    parents = {start: None}
    queue = collections.deque([start])
    generated = 0
    peak = 1
    while queue:
        sid = queue.popleft()
        outgoing = model._transitions(states[sid], config)
        generated += len(outgoing)
        for action, nxt in outgoing:
            normalized, _ = canonical(nxt, group, omit)
            nid = model._state_id(normalized)
            if nid not in states:
                states[nid] = normalized
                parents[nid] = (sid, action, nxt, _)
                queue.append(nid)
        peak = max(peak, len(queue))
    return states, parents, generated, peak


def full_named(config):
    return bfs(config, [IDENTITY])


def predicate_labels(states, config):
    return sorted({
        label for state in states.values()
        for label, truth in model._predicates(state, config).items() if truth
    })


def equivariance(states, config, group):
    checks = 0
    for state in sorted(states.values(), key=state_sort_key):
        for mapping in group:
            checks += 1
            expected = {
                (model._permuted_action(action, mapping),
                 model._state_id(model.permute_state(next_state, mapping)))
                for action, next_state in model._transitions(state, config)
            }
            mapped = model.permute_state(state, mapping)
            actual = {
                (action, model._state_id(next_state))
                for action, next_state in model._transitions(mapped, config)
            }
            if expected != actual:
                return False, checks
    return True, checks


def invariant(states, config, group):
    checks = 0
    for state in sorted(states.values(), key=state_sort_key):
        for mapping in group:
            checks += 1
            if model._predicates(state, config) != model._predicates(model.permute_state(state, mapping), config):
                return False, checks
    return True, checks


def group_collision(states, config, group, omit):
    groups = collections.defaultdict(list)
    for sid, state in states.items():
        key = model.typed_key(state, config)
        groups[key].append(state)
    return any(
        len({tuple(sorted(model._predicates(s, config).items())) for s in rows}) > 1
        for rows in groups.values()
    )


def state_sort_key(state):
    return repr(model._state_id(state))


def witness_for(target_sid, states, parents, config):
    steps = []
    cursor = target_sid
    while parents[cursor] is not None:
        parent_sid, action, raw_next, mapping = parents[cursor]
        steps.append((states[parent_sid], action, raw_next, states[cursor], mapping))
        cursor = parent_sid
    steps.reverse()

    concrete = INITIAL
    canonical_to_named = dict(IDENTITY)
    lifted = []
    for source, action, raw_next, canonical_next, mapping in steps:
        actual_action = model._permuted_action(action, canonical_to_named)
        actual_next = next(
            (nxt for candidate_action, nxt in model._transitions(concrete, config)
             if candidate_action == actual_action),
            None,
        )
        if actual_next is None:
            raise AssertionError("quotient witness edge has no named transition")
        if model.permute_state(raw_next, canonical_to_named) != actual_next:
            raise AssertionError("quotient witness edge fails mapped transition")
        inverse = {new: old for old, new in mapping.items()}
        canonical_to_named = {
            actor: canonical_to_named[inverse[actor]] for actor in ACTORS
        }
        if model.permute_state(canonical_next, canonical_to_named) != actual_next:
            raise AssertionError("quotient witness inverse map does not compose")
        concrete = actual_next
        lifted.append({"action": list(actual_action), "state": concrete})
    if not any(model._predicates(concrete, config).values()):
        raise AssertionError("lifted quotient trace does not end in a counterexample")
    return {
        "quotient_state": states[target_sid],
        "quotient_path_length": len(steps),
        "lifted_trace": lifted,
        "final_canonical_to_named": canonical_to_named,
    }


def quotient(config, named_states):
    group = [IDENTITY, SWAP]
    trans_ok, trans_checks = equivariance(named_states, config, group)
    prop_ok, prop_checks = invariant(named_states, config, group)
    collision = group_collision(named_states, config, group, config["omit_effect_target"])
    breaker = bool(config["fixed_verifier"] or config["fixed_lease_holder"] or config["named_property_actor"])
    fallback = breaker or not trans_ok or not prop_ok or collision
    used_group = [IDENTITY] if fallback else group
    omit = config["omit_effect_target"] and not fallback
    states, parents, generated, peak = bfs(config, used_group, omit)
    full_partition = {
        model._state_id(canonical(state, used_group, omit)[0])
        for state in named_states.values()
    }
    matches = set(states) == full_partition
    unsafe_ids = sorted(
        (sid for sid, state in states.items() if any(model._predicates(state, config).values())),
        key=lambda sid: repr(sid),
    )
    witnesses = [witness_for(sid, states, parents, config) for sid in unsafe_ids]
    full_labels = predicate_labels(named_states, config)
    quotient_labels = predicate_labels(states, config)
    edge_log = []
    for sid in states:
        source = states[sid]
        for action, raw_next in model._transitions(source, config):
            canonical_next, mapping = canonical(raw_next, used_group, omit)
            edge_log.append({
                "source": source,
                "action": list(action),
                "raw_next": raw_next,
                "canonical_next": canonical_next,
                "renaming": mapping,
            })
    return {
        "reachable_classes": len(states),
        "expanded_nodes": len(states),
        "generated_transitions": generated,
        "peak_frontier": peak,
        "unsafe_classes": len(unsafe_ids),
        "reachable_unsafe_predicates": quotient_labels,
        "full_unsafe_predicates": full_labels,
        "predicate_labels_preserved": quotient_labels == full_labels,
        "transition_equivariant": trans_ok,
        "transition_checks": trans_checks,
        "property_invariant": prop_ok,
        "property_checks": prop_checks,
        "fallback_to_named_states": fallback,
        "fallback_reason": "declared_identity_breaker" if breaker else (
            "noninvariant_or_key_collision" if fallback else None
        ),
        "quotient_matches_full_partition": matches,
        "nodes": [states[sid] for sid in sorted(states, key=repr)],
        "quotient_edges": edge_log,
        "counterexample_witnesses": witnesses,
    }


def naive_all_id(config, named_states):
    group = [
        dict(zip(ACTORS, perm))
        for perm in itertools.permutations(ACTORS)
    ]
    trans_ok, trans_checks = equivariance(named_states, config, group)
    prop_ok, prop_checks = invariant(named_states, config, group)
    states, _, generated, peak = bfs(config, group)
    qlabels = predicate_labels(states, config)
    flabels = predicate_labels(named_states, config)
    return {
        "reachable_classes": len(states),
        "expanded_nodes": len(states),
        "generated_transitions": generated,
        "peak_frontier": peak,
        "transition_equivariant": trans_ok,
        "transition_checks": trans_checks,
        "property_invariant": prop_ok,
        "property_checks": prop_checks,
        "reachable_unsafe_predicates": qlabels,
        "full_unsafe_predicates": flabels,
        "lost_predicate_labels": sorted(set(flabels) - set(qlabels)),
        "invented_predicate_labels": sorted(set(qlabels) - set(flabels)),
        "unsound": not trans_ok or not prop_ok or qlabels != flabels,
    }


def run(spec):
    base = {
        "fixed_verifier": None,
        "fixed_lease_holder": None,
        "named_property_actor": None,
        "omit_effect_target": False,
    }
    full_states, _, full_generated, full_peak = full_named(base)
    qresult = quotient(base, full_states)
    posthoc_groups = {
        model._state_id(canonical(state, [IDENTITY, SWAP])[0])
        for state in full_states.values()
    }
    labels = predicate_labels(full_states, base)
    arms = {
        "FULL_NAMED_BFS": {
            "reachable_states": len(full_states),
            "expanded_nodes": len(full_states),
            "generated_transitions": full_generated,
            "peak_frontier": full_peak,
            "reachable_unsafe_predicates": labels,
        },
        "POSTHOC_GROUPING": {
            "reachable_states": len(full_states),
            "quotient_classes_after_full_exploration": len(posthoc_groups),
            "expanded_nodes": len(full_states),
            "generated_transitions": full_generated,
            "counts_as_search_savings": False,
        },
        "QUOTIENT_FIRST_BFS": qresult,
        "NAIVE_ALL_ID_QUOTIENT": naive_all_id(base, full_states),
    }
    controls = {}
    for name, config in spec["controls"].items():
        states, _, full_edges, full_peak_control = full_named(config)
        result = quotient(config, states)
        controls[name] = {
            "reachable_states": len(states),
            "quotient_classes": result["reachable_classes"],
            "expanded_nodes": result["expanded_nodes"],
            "generated_transitions": result["generated_transitions"],
            "full_generated_transitions": full_edges,
            "fallback_to_named_states": result["fallback_to_named_states"],
            "fallback_reason": result["fallback_reason"],
            "transition_equivariant": result["transition_equivariant"],
            "property_invariant": result["property_invariant"],
            "predicate_labels_preserved": result["predicate_labels_preserved"],
            "peak_frontier": full_peak_control,
        }
    return {
        "schema": "issue7804-quotient-first-a01-candidate-v1",
        "model": spec["schema"],
        "arms": arms,
        "identity_breaking_controls": controls,
    }


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        spec = json.load(f)
    result = run(spec)
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(result, f, sort_keys=True, separators=(",", ":"))
        f.write("\n")
    print(json.dumps({"schema": result["schema"], "arms": sorted(result["arms"])}, sort_keys=True))
