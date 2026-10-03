"""Separate raw-only checker. Does not import candidate.py."""


def audit(fixture, raw):
    errors = []
    try:
        cases = {case["id"]: case for case in fixture["cases"]}
        rows = {row["id"]: row for row in raw["rows"]}
        if set(rows) != set(cases) or len(raw["rows"]) != len(cases):
            errors.append("case_cardinality_or_identity")
        training = [case for case in fixture["cases"] if case.get("training")]
        if len(training) != 1 or training[0]["classification"] != "REAL_GUARD_MISS" or not training[0]["replay_authenticated"]:
            errors.append("training_lineage_not_authenticated")
        if raw["refinement_alternatives"] != [["effect_allowed"], ["epoch_current"], ["target_fresh"]]:
            errors.append("nonminimal_or_tie_broken_refinement")
        if raw["changed_predicates"] != ["effect_allowed", "epoch_current", "target_fresh"]:
            errors.append("changed_predicate_set")
        if raw["cache_invalidation"] != {"shared": True, "sibling_a": True, "sibling_b": True, "sibling_c": False}:
            errors.append("sibling_dependency_invalidation")
        if raw["task_input_replayed"] or raw["new_authority"]:
            errors.append("authority_or_replay_escape")
        for case_id, case in cases.items():
            f = case["features"]
            if not all(f[p] for p in fixture["original_guard"]):
                expected = "REFUSE_ORIGINAL_GUARD"
            elif not case["coverage_complete"]:
                expected = "UNKNOWN_FALLBACK" if case["fallback_available"] else "STOP_NO_FALLBACK"
            elif all(all(f[p] for p in option) for option in [["effect_allowed"], ["epoch_current"], ["target_fresh"]]):
                expected = "ADMIT"
            else:
                expected = "UNKNOWN_FALLBACK" if case["fallback_available"] else "STOP_NO_FALLBACK"
            if rows.get(case_id, {}).get("decision") != expected:
                errors.append("decision:" + case_id)
            if rows.get(case_id, {}).get("task_input_replayed") is not False or rows.get(case_id, {}).get("new_authority") is not False:
                errors.append("row_authority_or_replay:" + case_id)
        if rows["valid_rare_alias"]["decision"] != rows["heldout_target_stale"]["decision"]:
            errors.append("observational_equivalence_violated")
        # Independent policy baselines over the same complete finite corpus.
        harmful = [c["id"] for c in fixture["cases"] if not c["safe"]]
        admissions = {k: set() for k in ("unchanged", "invalidate_all", "exact_blacklist", "candidate")}
        for case_id in harmful:
            case = cases[case_id]
            if all(case["features"].get(p, False) for p in fixture["original_guard"]):
                admissions["unchanged"].add(case_id)
                if case_id != "training_real_guard_miss":
                    admissions["exact_blacklist"].add(case_id)
                if rows[case_id]["decision"] == "ADMIT":
                    admissions["candidate"].add(case_id)
        if any(admissions["candidate"]):
            errors.append("candidate_false_admission")
        metrics = {
            "harmful_cases": len(harmful),
            "false_admissions": {name: len(value) for name, value in admissions.items()},
            "valid_common_admitted": rows["valid_common"]["decision"] == "ADMIT",
            "valid_rare_unknown": rows["valid_rare_alias"]["decision"] == "UNKNOWN_FALLBACK",
            "heldout_harms_refused": all(rows[x]["decision"] != "ADMIT" for x in ("heldout_permission_denied", "heldout_target_stale", "heldout_epoch_stale")),
            "all_rows_no_replay_or_authority": all(not r["task_input_replayed"] and not r["new_authority"] for r in raw["rows"]),
        }
        return {"status": "PASS" if not errors else "FAIL", "errors": errors, "metrics": metrics}
    except Exception as exc:  # corrupted raw must fail closed, not crash the harness
        return {"status": "FAIL", "errors": errors + ["malformed:" + type(exc).__name__], "metrics": {}}
