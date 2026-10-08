"""Independent finite reconstruction; deliberately does not import candidate.py."""

import copy


POLICIES = ("FULL_RESTART", "EARLIEST_CONFLICT_SUFFIX", "SELECTIVE_VALIDITY_RECOVERY")
COMPUTATIONS = {"observe", "compute", "prepare"}


def _expand_input(payload):
    if not isinstance(payload, dict):
        return None
    if "base_nodes" not in payload:
        return payload.get("cases")
    base = payload.get("base_nodes")
    scenarios = payload.get("cases")
    if not isinstance(base, list) or not isinstance(scenarios, list):
        return None
    expanded = []
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            return None
        rows = copy.deepcopy(base)
        overrides = scenario.get("receipt_overrides", {})
        if not isinstance(overrides, dict):
            return None
        for node in rows:
            if node.get("id") in overrides:
                node["receipt"] = overrides[node["id"]]
        expanded.append({
            "case_id": scenario.get("case_id"),
            "provenance_complete": scenario.get("provenance_complete"),
            "current_versions": copy.deepcopy(scenario.get("current_versions")),
            "nodes": rows,
        })
    return expanded


def _expand_truth(truth):
    if not isinstance(truth, dict):
        return None
    if "base_nodes" not in truth:
        return truth.get("cases")
    base = truth.get("base_nodes")
    controls = truth.get("cases")
    if not isinstance(base, list) or not isinstance(controls, dict):
        return None
    expanded = {}
    for case_id, control in controls.items():
        if not isinstance(control, dict):
            return None
        rows = copy.deepcopy(base)
        overrides = control.get("receipt_overrides", {})
        if not isinstance(overrides, dict):
            return None
        for node in rows:
            if node.get("id") in overrides:
                node["receipt"] = overrides[node["id"]]
        expanded[case_id] = {
            "provenance_complete": control.get("provenance_complete"),
            "current_versions": copy.deepcopy(control.get("current_versions")),
            "nodes": rows,
        }
    return expanded


def _same_version(left, right):
    return type(left) is int and type(right) is int and left == right


def _reconstruct(case):
    rows = case.get("nodes")
    if not isinstance(rows, list):
        return {"disposition": "INVALID_PLAN", "recompute": {}, "reused": {},
                "dispatch_effects": [], "reconcile_effects": [], "preserved_effects": [],
                "historical_verifications": []}
    names = [row.get("id") for row in rows if isinstance(row, dict)]
    if len(names) != len(rows) or len(set(names)) != len(names):
        return {"disposition": "INVALID_PLAN", "recompute": {}, "reused": {},
                "dispatch_effects": [], "reconcile_effects": [], "preserved_effects": [],
                "historical_verifications": []}

    positions = {name: n for n, name in enumerate(names)}
    stale = set()
    now = case.get("current_versions", {})
    for n, row in enumerate(rows):
        deps = row.get("deps")
        reads = row.get("reads", {})
        if (row.get("kind") not in COMPUTATIONS | {"effect", "verify"}
                or not isinstance(deps, list) or not isinstance(reads, dict)
                or any(dep not in positions or positions[dep] >= n for dep in deps)):
            return {"disposition": "INVALID_PLAN", "recompute": {}, "reused": {},
                    "dispatch_effects": [], "reconcile_effects": [], "preserved_effects": [],
                    "historical_verifications": []}
        version_drift = any(key not in now or not _same_version(now[key], ver)
                            for key, ver in reads.items())
        upstream_drift = any(dep in stale for dep in deps)
        if version_drift or upstream_drift:
            stale.add(row["id"])

    compute_names = [row["id"] for row in rows if row["kind"] in COMPUTATIONS]
    stale_compute = [row["id"] for row in rows
                     if row["kind"] in COMPUTATIONS and row["id"] in stale]
    first_bad = min((positions[name] for name in stale_compute), default=None)
    suffix = [row["id"] for n, row in enumerate(rows)
              if first_bad is not None and n >= first_bad and row["kind"] in COMPUTATIONS]
    recompute = {
        "FULL_RESTART": compute_names,
        "EARLIEST_CONFLICT_SUFFIX": suffix,
        "SELECTIVE_VALIDITY_RECOVERY": stale_compute,
    }
    disposition = "PASS_PLAN"
    if case.get("provenance_complete") is not True:
        disposition = "HOLD_INCOMPLETE_PROVENANCE"
        recompute["SELECTIVE_VALIDITY_RECOVERY"] = list(compute_names)

    unsettled = [row["id"] for row in rows if row["kind"] == "effect"
                 and row.get("receipt") not in {"verified_effect", "verified_no_effect"}]
    if unsettled:
        disposition = "HOLD_EFFECT_RECONCILIATION"
    known_effects = [row["id"] for row in rows if row["kind"] == "effect"]
    preserved = [row["id"] for row in rows
                 if row["kind"] == "effect" and row.get("receipt") == "verified_effect"]
    historical_verifications = [row["id"] for row in rows
                                if row["kind"] == "verify"
                                and row.get("receipt") == "verified_terminal"]
    reused = {policy: [name for name in compute_names if name not in recompute[policy]]
              for policy in POLICIES}
    return {
        "disposition": disposition,
        "recompute": recompute,
        "reused": reused,
        "dispatch_effects": [],
        "reconcile_effects": unsettled,
        "preserved_effects": preserved,
        "historical_verifications": historical_verifications,
        "effect_nodes": known_effects,
    }


def audit_payload(inputs, truth, raw):
    errors = []
    cases = _expand_input(inputs)
    truth_cases = _expand_truth(truth)
    results = raw.get("results") if isinstance(raw, dict) else None
    if not isinstance(cases, list) or not isinstance(truth_cases, dict) or not isinstance(results, list):
        return {"errors": ["malformed top-level payload"], "reconstructed_cases": 0}

    by_id = {}
    for result in results:
        if not isinstance(result, dict) or not isinstance(result.get("case_id"), str):
            errors.append("malformed raw result")
        elif result["case_id"] in by_id:
            errors.append("duplicate raw case id: " + result["case_id"])
        else:
            by_id[result["case_id"]] = result
    input_ids = [case.get("case_id") for case in cases if isinstance(case, dict)]
    if len(input_ids) != len(cases) or len(set(input_ids)) != len(input_ids):
        errors.append("malformed or duplicate input case id")
    if set(by_id) != set(input_ids):
        errors.append("raw/input case denominator mismatch")

    reconstructed = 0
    for case in cases:
        if not isinstance(case, dict):
            continue
        case_id = case.get("case_id")
        canonical = truth_cases.get(case_id)
        if not isinstance(canonical, dict):
            errors.append("missing independent truth case: " + str(case_id))
            continue
        for field in ("provenance_complete", "current_versions", "nodes"):
            if case.get(field) != canonical.get(field):
                errors.append(f"{case_id}: input/truth mismatch in {field}")
        expected = _reconstruct(canonical)
        found = by_id.get(case_id, {}).get("plan")
        if found != expected:
            errors.append(f"{case_id}: raw plan differs from independent reconstruction")
        else:
            reconstructed += 1
    return {"errors": errors, "reconstructed_cases": reconstructed}


def mutation_suite(inputs, truth, raw):
    rejected = []
    expanded_cases = _expand_input(inputs)
    if not isinstance(expanded_cases, list):
        return {"rejected": [], "errors": ["could not expand frozen input"]}
    expanded_inputs = {"cases": expanded_cases}

    def probe(name, changed_inputs, changed_raw):
        if audit_payload(changed_inputs, truth, changed_raw)["errors"]:
            rejected.append(name)

    original = audit_payload(inputs, truth, raw)
    if original["errors"]:
        return {"rejected": [], "errors": ["baseline audit did not pass"]}
    raw_by_id = {row["case_id"]: row for row in raw["results"]}

    # A missing dependency edge must disagree with the auditor-only frozen graph.
    changed_inputs = copy.deepcopy(expanded_inputs)
    edge_case = next((case for case in changed_inputs["cases"]
                      if any(node.get("deps") for node in case.get("nodes", []))), None)
    if edge_case is not None:
        node = next(node for node in edge_case["nodes"] if node.get("deps"))
        node["deps"] = node["deps"][1:]
        probe("missing_dependency_edge", changed_inputs, copy.deepcopy(raw))

    # Inject a stale generation into a result that claims selective reuse.
    changed_raw = copy.deepcopy(raw)
    stale_case = next((case for case in expanded_cases
                       if raw_by_id.get(case.get("case_id"), {}).get("plan", {}).get("recompute", {}).get("SELECTIVE_VALIDITY_RECOVERY")), None)
    if stale_case is not None:
        case_id = stale_case["case_id"]
        changed_raw_by_id = {row["case_id"]: row for row in changed_raw["results"]}
        changed_raw_by_id[case_id]["plan"]["reused"]["SELECTIVE_VALIDITY_RECOVERY"].append("STALE_GENERATION")
        probe("stale_generation_reused", copy.deepcopy(expanded_inputs), changed_raw)

    # Forge a clean no-effect status over a source-bound ambiguous receipt.
    changed_inputs = copy.deepcopy(expanded_inputs)
    changed_raw = copy.deepcopy(raw)
    ambiguous = next((case for case in changed_inputs["cases"]
                      if any(node.get("kind") == "effect" and node.get("receipt") == "ambiguous_delivery"
                             for node in case.get("nodes", []))), None)
    if ambiguous is not None:
        effect = next(node for node in ambiguous["nodes"]
                      if node.get("kind") == "effect" and node.get("receipt") == "ambiguous_delivery")
        effect["receipt"] = "verified_no_effect"
        changed_raw_by_id = {row["case_id"]: row for row in changed_raw["results"]}
        plan = changed_raw_by_id[ambiguous["case_id"]]["plan"]
        plan["disposition"] = "PASS_PLAN"
        plan["reconcile_effects"] = []
        probe("forged_no_effect_receipt", changed_inputs, changed_raw)

        # Even an asserted idempotency flag never grants automatic dispatch.
        changed_inputs = copy.deepcopy(expanded_inputs)
        effect_case = next(case for case in changed_inputs["cases"]
                           if any(node.get("kind") == "effect" for node in case.get("nodes", [])))
        effect = next(node for node in effect_case["nodes"] if node.get("kind") == "effect")
        effect["idempotent"] = True
        changed_raw = copy.deepcopy(raw)
        changed_raw_by_id = {row["case_id"]: row for row in changed_raw["results"]}
        changed_raw_by_id[effect_case["case_id"]]["plan"]["dispatch_effects"].append(effect["id"])
        probe("false_idempotency_dispatch", changed_inputs, changed_raw)

        changed_raw = copy.deepcopy(raw)
        changed_raw_by_id = {row["case_id"]: row for row in changed_raw["results"]}
        changed_raw_by_id[ambiguous["case_id"]]["plan"]["dispatch_effects"].append(effect["id"])
        probe("ambiguous_effect_replayed", copy.deepcopy(expanded_inputs), changed_raw)

    return {"rejected": rejected, "errors": []}


def audit_formal(inputs, truth, raw):
    base = audit_payload(inputs, truth, raw)
    mutations = mutation_suite(inputs, truth, raw)
    rows = raw.get("results", []) if isinstance(raw, dict) else []
    cases = _expand_input(inputs) or []
    plans = {row.get("case_id"): row.get("plan") for row in rows if isinstance(row, dict)}
    total_recomputes = {policy: 0 for policy in POLICIES}
    strict_advantage = []
    dispatches = 0
    ambiguity_holds = True
    incomplete_reuse = None
    complete_reuse = None
    for case in cases:
        plan = plans.get(case.get("case_id"), {})
        for policy in POLICIES:
            total_recomputes[policy] += len(plan.get("recompute", {}).get(policy, []))
        suffix = plan.get("recompute", {}).get("EARLIEST_CONFLICT_SUFFIX", [])
        selective = plan.get("recompute", {}).get("SELECTIVE_VALIDITY_RECOVERY", [])
        if len(selective) < len(suffix):
            strict_advantage.append(case.get("case_id"))
        dispatches += len(plan.get("dispatch_effects", []))
        if case.get("case_id") == "ambiguous_effect":
            ambiguity_holds = (plan.get("disposition") == "HOLD_EFFECT_RECONCILIATION"
                               and plan.get("reconcile_effects") == ["send_left"]
                               and plan.get("dispatch_effects") == [])
        if case.get("case_id") == "revision_left":
            complete_reuse = len(plan.get("reused", {}).get("SELECTIVE_VALIDITY_RECOVERY", []))
        if case.get("case_id") == "revision_left_incomplete":
            incomplete_reuse = len(plan.get("reused", {}).get("SELECTIVE_VALIDITY_RECOVERY", []))

    monotone = (complete_reuse is not None and incomplete_reuse is not None
                and incomplete_reuse <= complete_reuse and incomplete_reuse == 0)
    conditions = {
        "all_cases_reconstructed": not base["errors"] and base["reconstructed_cases"] == len(cases),
        "all_mutations_rejected": not mutations["errors"] and len(mutations["rejected"]) == 5,
        "selective_strictly_beats_suffix": bool(strict_advantage),
        "ambiguous_effect_held": ambiguity_holds,
        "incomplete_provenance_monotone": monotone,
        "zero_dispatch_replay": dispatches == 0,
    }
    return {
        "status": "PASS_METHOD_SCOPED" if all(conditions.values()) else "FAIL_AUDIT_OR_GATE",
        "errors": base["errors"] + mutations["errors"],
        "reconstructed_cases": base["reconstructed_cases"],
        "mutations_rejected": len(mutations["rejected"]),
        "mutation_names_rejected": mutations["rejected"],
        "conditions": conditions,
        "metrics": {
            "case_count": len(cases),
            "total_recomputes_by_policy": total_recomputes,
            "strict_selective_advantage_cases": len(strict_advantage),
            "strict_selective_advantage_case_ids": strict_advantage,
            "dispatch_attempts": dispatches,
            "incomplete_provenance_reused_nodes": incomplete_reuse,
            "complete_paired_reused_nodes": complete_reuse,
        },
    }
