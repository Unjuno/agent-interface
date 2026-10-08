"""Finite, offline planner for reuse vs. external-effect replay eligibility."""


COMPUTATION_KINDS = {"observe", "compute", "prepare"}
EFFECT_KINDS = {"effect"}


def _valid_version(actual, expected):
    return type(actual) is int and type(expected) is int and actual == expected


def plan_recovery(case):
    nodes = case.get("nodes")
    if not isinstance(nodes, list):
        return {"disposition": "INVALID_PLAN", "recompute": {}, "reused": {},
                "dispatch_effects": [], "reconcile_effects": [], "preserved_effects": [],
                "historical_verifications": []}

    ids = [node.get("id") for node in nodes if isinstance(node, dict)]
    if len(ids) != len(nodes) or len(set(ids)) != len(ids):
        return {"disposition": "INVALID_PLAN", "recompute": {}, "reused": {},
                "dispatch_effects": [], "reconcile_effects": [], "preserved_effects": [],
                "historical_verifications": []}

    index = {node_id: position for position, node_id in enumerate(ids)}
    invalid = set()
    current_versions = case.get("current_versions", {})
    for position, node in enumerate(nodes):
        if node.get("kind") not in COMPUTATION_KINDS | EFFECT_KINDS | {"verify"}:
            return {"disposition": "INVALID_PLAN", "recompute": {}, "reused": {},
                    "dispatch_effects": [], "reconcile_effects": [], "preserved_effects": [],
                    "historical_verifications": []}
        deps = node.get("deps")
        reads = node.get("reads", {})
        if not isinstance(deps, list) or not isinstance(reads, dict):
            return {"disposition": "INVALID_PLAN", "recompute": {}, "reused": {},
                    "dispatch_effects": [], "reconcile_effects": [], "preserved_effects": [],
                    "historical_verifications": []}
        if any(dep not in index or index[dep] >= position for dep in deps):
            return {"disposition": "INVALID_PLAN", "recompute": {}, "reused": {},
                    "dispatch_effects": [], "reconcile_effects": [], "preserved_effects": []}
        changed = any(
            key not in current_versions or not _valid_version(current_versions[key], version)
            for key, version in reads.items()
        )
        if changed or any(dep in invalid for dep in deps):
            invalid.add(node["id"])

    compute_ids = [node["id"] for node in nodes if node["kind"] in COMPUTATION_KINDS]
    invalid_compute_ids = [node["id"] for node in nodes
                           if node["kind"] in COMPUTATION_KINDS and node["id"] in invalid]
    first_invalid_position = min((index[node_id] for node_id in invalid_compute_ids), default=None)
    suffix_ids = [node["id"] for position, node in enumerate(nodes)
                  if first_invalid_position is not None
                  and position >= first_invalid_position
                  and node["kind"] in COMPUTATION_KINDS]

    recompute = {
        "FULL_RESTART": list(compute_ids),
        "EARLIEST_CONFLICT_SUFFIX": suffix_ids,
        "SELECTIVE_VALIDITY_RECOVERY": invalid_compute_ids,
    }
    disposition = "PASS_PLAN"
    if case.get("provenance_complete") is not True:
        disposition = "HOLD_INCOMPLETE_PROVENANCE"
        recompute["SELECTIVE_VALIDITY_RECOVERY"] = list(compute_ids)

    settled_receipts = {"verified_effect", "verified_no_effect"}
    ambiguous_effects = [node["id"] for node in nodes
                         if node["kind"] in EFFECT_KINDS
                         and node.get("receipt") not in settled_receipts]
    if ambiguous_effects:
        disposition = "HOLD_EFFECT_RECONCILIATION"

    effect_ids = [node["id"] for node in nodes if node["kind"] in EFFECT_KINDS]
    preserved_effects = [node["id"] for node in nodes
                         if node["kind"] in EFFECT_KINDS
                         and node.get("receipt") == "verified_effect"]
    historical_verifications = [node["id"] for node in nodes
                                if node["kind"] == "verify"
                                and node.get("receipt") == "verified_terminal"]
    reused = {
        policy: [node_id for node_id in compute_ids if node_id not in planned]
        for policy, planned in recompute.items()
    }
    return {
        "disposition": disposition,
        "recompute": recompute,
        "reused": reused,
        "dispatch_effects": [],
        "reconcile_effects": ambiguous_effects,
        "preserved_effects": preserved_effects,
        "historical_verifications": historical_verifications,
        "effect_nodes": effect_ids,
    }
