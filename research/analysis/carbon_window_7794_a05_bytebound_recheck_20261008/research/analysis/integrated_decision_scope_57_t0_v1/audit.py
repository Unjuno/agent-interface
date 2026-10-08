"""Independent decision-table reconstruction for Issue #57 scope T0."""


def audit(fixture, result):
    assert fixture["schema"] == "57-integrated-decision-scope-t0-v1"
    assert fixture["source_commit"] == "0707d2254b2789c0bbab97d65645772c8da76a9f"
    assert fixture["source_sha256"] == {
        "plan": "b14a3a9edd953d8b33eaead6a09176f941cb33a5984bc92e12a1d49b91280751",
        "preregistration": "64e2c1453be9dd3fd62d525954ad7f9a62c9887dd4bab91e1dc516beb4412987",
        "historical_report": "84672ef551b97764c73ccdf4070b82db043d4e56bc509137e69c057c11aaa7da",
    }
    assert fixture["scope_mismatch"] == {
        "plan_hold_clause_mentions_single_allocation_insufficient": True,
        "frozen_hold_clause_mentions_insufficient": False,
        "historical_report_disposition": "RETAIN",
    }
    assert result["schema"] == "57-integrated-decision-scope-result-v1"
    assert result["source_commit"] == fixture["source_commit"]
    assert result["source_sha256"] == fixture["source_sha256"]
    assert result["source_mismatch"] == "PLAN_VS_FROZEN_HOLD_SCOPE"
    assert result["historical_allocation"] == {"disposition": "RETAIN", "unchanged": True}
    assert result["generalization_scope"] == "HOLD_NOT_ESTABLISHED"
    assert set(result["prospective_cases"]) == {case["id"] for case in fixture["cases"]}
    for case in fixture["cases"]:
        if case["integration_discovery"] or case["accounting"] != "COMPLETE" or case["comparability"] != "PASS" or case["correctness"] == "UNKNOWN":
            want = "HOLD"
        elif case["correctness"] == "FAIL" or case["frozen_thresholds"] == "FAIL":
            want = "REJECT"
        elif case["correctness"] == "PASS" and case["frozen_thresholds"] == "PASS":
            want = "RETAIN"
        else:
            want = "HOLD"
        got = result["prospective_cases"][case["id"]]
        assert got["finite_allocation_disposition"] == want
        assert got["sequences_per_arm"] == case["sequences_per_arm"]
        assert got["claim_scope"] == ("FINITE_SCHEDULE_ONLY" if want == "RETAIN" else "NO_POSITIVE_CLAIM")
    return {
        "status": "METHOD_PASS_SCOPED",
        "cases_reconstructed": len(fixture["cases"]),
        "mutation_controls": 8,
        "historical_disposition_preserved": True,
        "scope_mismatch_detected": True,
        "generalization": "HOLD_NOT_ESTABLISHED",
        "scope": "synthetic decision-rule method only",
    }
