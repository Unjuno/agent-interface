#!/usr/bin/env python3
"""Separate raw-only reconstruction using the frozen integer-state oracle."""
import collections
import itertools
import json
import sys
import hashlib
import pathlib
import predecessor_auditor as oracle

ACTORS = oracle.ACTORS
IDENTITY = oracle.ID
SWAP = oracle.SWAP
INITIAL = oracle.INITIAL
FIELD_ORDER = ("lease_holder", "replyers", "generation", "commit_by", "effect_target", "receipt_target")


def state_tuple_key(s):
    return (oracle.ROLE_NAMES.get(s[0]), tuple(oracle.ROLE_NAMES[a] for a in ACTORS if s[1] & (1 << a)), s[2],
            oracle.ROLE_NAMES.get(s[3]), s[4], s[5])


def state_doc(s):
    return {
        "lease_holder": oracle.ROLE_NAMES.get(s[0]),
        "replyers": [oracle.ROLE_NAMES[a] for a in ACTORS if s[1] & (1 << a)],
        "generation": s[2],
        "commit_by": oracle.ROLE_NAMES.get(s[3]),
        "effect_target": s[4],
        "receipt_target": s[5],
    }


def action_doc(a):
    op, actor, target = a
    return [op, None if actor is None else oracle.ROLE_NAMES[actor], target]


def model_key(s, omit=False):
    doc = state_doc(s)
    fields = [name for name in FIELD_ORDER if not (omit and name == "effect_target")]
    return tuple((name, tuple(doc[name]) if name == "replyers" else doc[name]) for name in fields)


def canonical(s, group, omit=False):
    options = []
    for permutation in group:
        renamed = oracle._rename(s, permutation)
        options.append((repr(model_key(renamed, omit)), renamed, permutation))
    _, renamed, permutation = min(options, key=lambda item: item[0])
    return renamed, permutation


def transitions(s, cfg):
    return oracle._edges(s, cfg)


def full_bfs(cfg):
    states = {INITIAL}
    parents = {INITIAL: None}
    todo = collections.deque([INITIAL])
    generated = 0
    peak = 1
    while todo:
        current = todo.popleft()
        outgoing = transitions(current, cfg)
        generated += len(outgoing)
        for action, nxt in outgoing:
            if nxt not in states:
                states.add(nxt)
                parents[nxt] = (current, action)
                todo.append(nxt)
        peak = max(peak, len(todo))
    return states, parents, generated, peak


def labels(states, cfg):
    return sorted({
        name for state in states
        for name, value in oracle._predicates(state, cfg).items() if value
    })


def named_equivariance(states, cfg, group):
    checked = 0
    for state in sorted(states, key=lambda item: repr(state_tuple_key(item))):
        for permutation in group:
            checked += 1
            renamed_expected = {
                (oracle._rename_action(action, permutation), oracle._rename(nxt, permutation))
                for action, nxt in transitions(state, cfg)
            }
            if renamed_expected != set(transitions(oracle._rename(state, permutation), cfg)):
                return False, checked
    return True, checked


def named_invariance(states, cfg, group):
    checked = 0
    for state in sorted(states, key=lambda item: repr(state_tuple_key(item))):
        for permutation in group:
            checked += 1
            if oracle._predicates(state, cfg) != oracle._predicates(oracle._rename(state, permutation), cfg):
                return False, checked
    return True, checked


def grouped_collision(states, cfg, group, omit):
    partitions = collections.defaultdict(list)
    for state in states:
        reduced, _ = canonical(state, group, omit)
        partitions[repr(model_key(reduced, omit))].append(state)
    return any(
        len({tuple(sorted(oracle._predicates(state, cfg).items())) for state in members}) > 1
        for members in partitions.values()
    )


def quotient_bfs(cfg, group, omit=False):
    first, _ = canonical(INITIAL, group, omit)
    nodes = {first}
    parents = {first: None}
    queue = collections.deque([first])
    generated = 0
    peak = 1
    edge_records = []
    while queue:
        source = queue.popleft()
        outgoing = transitions(source, cfg)
        generated += len(outgoing)
        for action, raw_next in outgoing:
            dest, permutation = canonical(raw_next, group, omit)
            edge_records.append({
                "source": state_doc(source),
                "action": action_doc(action),
                "raw_next": state_doc(raw_next),
                "canonical_next": state_doc(dest),
                "renaming": {
                    oracle.ROLE_NAMES[old]: oracle.ROLE_NAMES[new]
                    for old, new in permutation.items()
                },
            })
            if dest not in nodes:
                nodes.add(dest)
                parents[dest] = (source, action, raw_next, permutation)
                queue.append(dest)
        peak = max(peak, len(queue))
    return nodes, parents, generated, peak, edge_records


def lift_path(target, parents, cfg):
    route = []
    cursor = target
    while parents[cursor] is not None:
        source, action, raw_next, dest_perm = parents[cursor]
        route.append((source, action, raw_next, cursor, dest_perm))
        cursor = source
    route.reverse()
    concrete = INITIAL
    canonical_to_concrete = dict(IDENTITY)
    lifted = []
    for source, action, raw_next, canonical_next, permutation in route:
        mapped_action = oracle._rename_action(action, canonical_to_concrete)
        valid = [
            nxt for actual, nxt in transitions(concrete, cfg)
            if actual == mapped_action
        ]
        if len(valid) != 1:
            raise ValueError("lifted action is not a unique concrete transition")
        actual_next = valid[0]
        if oracle._rename(raw_next, canonical_to_concrete) != actual_next:
            raise ValueError("mapped quotient edge does not equal concrete successor")
        inverse = {new: old for old, new in permutation.items()}
        canonical_to_concrete = {
            actor: canonical_to_concrete[inverse[actor]] for actor in ACTORS
        }
        if oracle._rename(canonical_next, canonical_to_concrete) != actual_next:
            raise ValueError("composed inverse map fails at quotient successor")
        concrete = actual_next
        lifted.append({"action": action_doc(mapped_action), "state": state_doc(concrete)})
    if not route or not any(oracle._predicates(concrete, cfg).values()):
        raise ValueError("lifted trace fails to reach a safety predicate")
    return {
        "quotient_state": state_doc(target),
        "quotient_path_length": len(route),
        "lifted_trace": lifted,
        "final_canonical_to_named": {
            oracle.ROLE_NAMES[key]: oracle.ROLE_NAMES[value]
            for key, value in canonical_to_concrete.items()
        },
    }


def typed_arm(cfg, full_states):
    group = [IDENTITY, SWAP]
    trans_ok, trans_n = named_equivariance(full_states, cfg, group)
    prop_ok, prop_n = named_invariance(full_states, cfg, group)
    collision = grouped_collision(full_states, cfg, group, cfg["omit_effect_target"])
    breaker = bool(cfg["fixed_verifier"] or cfg["fixed_lease_holder"] or cfg["named_property_actor"])
    fallback = breaker or not trans_ok or not prop_ok or collision
    used_group = [IDENTITY] if fallback else group
    use_omit = cfg["omit_effect_target"] and not fallback
    nodes, parents, generated, peak, edge_log = quotient_bfs(cfg, used_group, use_omit)
    full_partition = {canonical(state, used_group, use_omit)[0] for state in full_states}
    unsafe_nodes = sorted(
        (state for state in nodes if any(oracle._predicates(state, cfg).values())),
        key=lambda state: repr(state_tuple_key(state)),
    )
    witnesses = [lift_path(target, parents, cfg) for target in unsafe_nodes]
    full_labels = labels(full_states, cfg)
    quotient_labels = labels(nodes, cfg)
    return {
        "reachable_classes": len(nodes),
        "expanded_nodes": len(nodes),
        "generated_transitions": generated,
        "peak_frontier": peak,
        "unsafe_classes": len(unsafe_nodes),
        "reachable_unsafe_predicates": quotient_labels,
        "full_unsafe_predicates": full_labels,
        "predicate_labels_preserved": quotient_labels == full_labels,
        "transition_equivariant": trans_ok,
        "transition_checks": trans_n,
        "property_invariant": prop_ok,
        "property_checks": prop_n,
        "fallback_to_named_states": fallback,
        "fallback_reason": "declared_identity_breaker" if breaker else (
            "noninvariant_or_key_collision" if fallback else None
        ),
        "quotient_matches_full_partition": nodes == full_partition,
        "nodes": [state_doc(s) for s in sorted(nodes, key=lambda x: repr(state_tuple_key(x)))],
        "quotient_edges": edge_log,
        "counterexample_witnesses": witnesses,
    }


def naive_arm(cfg, full_states):
    group = [
        dict(zip(ACTORS, permutation))
        for permutation in itertools.permutations(ACTORS)
    ]
    trans_ok, trans_n = named_equivariance(full_states, cfg, group)
    prop_ok, prop_n = named_invariance(full_states, cfg, group)
    nodes, _, generated, peak, _ = quotient_bfs(cfg, group)
    qlabels = labels(nodes, cfg)
    full_labels = labels(full_states, cfg)
    return {
        "reachable_classes": len(nodes),
        "expanded_nodes": len(nodes),
        "generated_transitions": generated,
        "peak_frontier": peak,
        "transition_equivariant": trans_ok,
        "transition_checks": trans_n,
        "property_invariant": prop_ok,
        "property_checks": prop_n,
        "reachable_unsafe_predicates": qlabels,
        "full_unsafe_predicates": full_labels,
        "lost_predicate_labels": sorted(set(full_labels) - set(qlabels)),
        "invented_predicate_labels": sorted(set(qlabels) - set(full_labels)),
        "unsound": not trans_ok or not prop_ok or qlabels != full_labels,
    }


def reconstruct(spec):
    base = {
        "fixed_verifier": None,
        "fixed_lease_holder": None,
        "named_property_actor": None,
        "omit_effect_target": False,
    }
    full_states, _, full_edges, full_peak = full_bfs(base)
    q = typed_arm(base, full_states)
    posthoc = {canonical(s, [IDENTITY, SWAP])[0] for s in full_states}
    arms = {
        "FULL_NAMED_BFS": {
            "reachable_states": len(full_states),
            "expanded_nodes": len(full_states),
            "generated_transitions": full_edges,
            "peak_frontier": full_peak,
            "reachable_unsafe_predicates": labels(full_states, base),
        },
        "POSTHOC_GROUPING": {
            "reachable_states": len(full_states),
            "quotient_classes_after_full_exploration": len(posthoc),
            "expanded_nodes": len(full_states),
            "generated_transitions": full_edges,
            "counts_as_search_savings": False,
        },
        "QUOTIENT_FIRST_BFS": q,
        "NAIVE_ALL_ID_QUOTIENT": naive_arm(base, full_states),
    }
    controls = {}
    for name, cfg in spec["controls"].items():
        states, _, full_generated, full_peak_control = full_bfs(cfg)
        result = typed_arm(cfg, states)
        controls[name] = {
            "reachable_states": len(states),
            "quotient_classes": result["reachable_classes"],
            "expanded_nodes": result["expanded_nodes"],
            "generated_transitions": result["generated_transitions"],
            "full_generated_transitions": full_generated,
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


def compare(actual, expected):
    return [] if actual == expected else ["candidate raw differs from independent reconstruction"]


def main(spec_path, candidate_path, audit_path, freeze_path, prior_candidate_path, prior_audit_path):
    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)
    with open(candidate_path, encoding="utf-8") as f:
        actual = json.load(f)
    expected = reconstruct(spec)
    errors = compare(actual, expected)
    q = expected["arms"]["QUOTIENT_FIRST_BFS"]
    if not q["predicate_labels_preserved"] or not q["quotient_matches_full_partition"]:
        errors.append("typed quotient does not preserve the full named reachable partition")
    if q["expanded_nodes"] >= expected["arms"]["FULL_NAMED_BFS"]["expanded_nodes"]:
        errors.append("quotient-first did not strictly reduce expanded states")
    if q["generated_transitions"] >= expected["arms"]["FULL_NAMED_BFS"]["generated_transitions"]:
        errors.append("quotient-first did not strictly reduce generated transitions")
    if len(q["counterexample_witnesses"]) != q["unsafe_classes"]:
        errors.append("not every unsafe quotient class has a witness")
    if not all(row["fallback_to_named_states"] and row["expanded_nodes"] == row["reachable_states"]
               for row in expected["identity_breaking_controls"].values()):
        errors.append("an identity-breaking control did not fall back to full named exploration")
    if not expected["arms"]["NAIVE_ALL_ID_QUOTIENT"]["unsound"]:
        errors.append("deliberately naive all-ID control did not expose unsoundness")
    with open(freeze_path, encoding="utf-8") as f:
        freeze = json.load(f)
    for path, key in ((prior_candidate_path, "candidate_raw"), (prior_audit_path, "audit_raw")):
        data = pathlib.Path(path).read_bytes()
        if hashlib.sha256(data).hexdigest() != freeze["predecessor_raw_actual_sha256"][key]:
            errors.append(key + " tracked bytes disagree with frozen actual digest")
    audit = {
        "schema": "issue7804-quotient-first-a01-audit-v1",
        "disposition": "PASS_METHOD_AND_SEARCH_SCOPED" if not errors else "FAIL_AUDIT",
        "errors": errors,
        "reconstructed_full_states": expected["arms"]["FULL_NAMED_BFS"]["reachable_states"],
        "reconstructed_quotient_classes": q["reachable_classes"],
        "expanded_nodes_full_vs_quotient": [
            expected["arms"]["FULL_NAMED_BFS"]["expanded_nodes"], q["expanded_nodes"]
        ],
        "generated_transitions_full_vs_quotient": [
            expected["arms"]["FULL_NAMED_BFS"]["generated_transitions"], q["generated_transitions"]
        ],
        "quotient_edges_reconstructed": len(q["quotient_edges"]),
        "quotient_witnesses_replayed": len(q["counterexample_witnesses"]),
        "identity_breaking_controls_fallback": sum(
            1 for row in expected["identity_breaking_controls"].values()
            if row["fallback_to_named_states"]
        ),
        "predecessor_raw_sha256_verified": True,
        "scope": "finite authored transition model only; no wall-clock or production-runtime claim",
    }
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(audit, f, sort_keys=True, separators=(",", ":"))
        f.write("\n")
    print(json.dumps({
        "disposition": audit["disposition"],
        "errors": errors,
        "states": audit["reconstructed_full_states"],
        "quotient": audit["reconstructed_quotient_classes"],
        "quotient_edges": audit["quotient_edges_reconstructed"],
        "witnesses": audit["quotient_witnesses_replayed"],
    }, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:]))
