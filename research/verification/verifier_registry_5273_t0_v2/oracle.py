"""Test-side expected labels; the raw-only auditor has a separate literal map."""
EXPECTED = {
    "warm_cpu_feasible": ("COMPATIBLE", ()),
    "unsupported_primitive": ("REJECTED", ("unsupported_primitive", "wrong_evidence_role")),
    "wrong_input_role": ("REJECTED", ("wrong_evidence_role",)),
    "wrong_output_role": ("REJECTED", ("wrong_output_role",)),
    "stale_version": ("REJECTED", ("stale_version",)),
    "unknown_verifier": ("UNAVAILABLE", ("verifier_unknown",)),
    "resource_unavailable": ("UNAVAILABLE", ("resource_unavailable", "latency_unqualified")),
    "cold_budget_violation": ("REJECTED", ("budget_exceeded",)),
    "hard_incompatibility_precedes_unavailable": ("REJECTED", ("stale_version", "side_effect_prohibited", "resource_unavailable", "latency_unqualified")),
    "deadline_infeasible": ("REJECTED", ("deadline_infeasible",)),
}
