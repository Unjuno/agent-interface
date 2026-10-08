"""Small fail-closed evidence eligibility gate for Issue #6576 construction."""

from __future__ import annotations

REQUIRED = {
    "endpoint_identity",
    "mode_manifest",
    "observed_modes",
    "tail_events_by_mode",
    "min_tail_events_per_mode",
    "temporal_stability",
    "dependence_checked",
    "censor_count",
    "missing_endpoint_count",
}


def decide(evidence: dict) -> str:
    """Return ELIGIBLE_REFERENCE or a typed NOT_ESTIMABLE reason."""
    if not isinstance(evidence, dict) or not REQUIRED.issubset(evidence):
        return "NOT_ESTIMABLE_INCOMPLETE_EVIDENCE"
    if not evidence["endpoint_identity"]:
        return "NOT_ESTIMABLE_ENDPOINT"
    manifest = evidence["mode_manifest"]
    observed = evidence["observed_modes"]
    if (
        not isinstance(manifest, list)
        or not manifest
        or any(not isinstance(mode, str) or not mode for mode in manifest)
        or len(set(manifest)) != len(manifest)
        or not isinstance(observed, list)
        or any(not isinstance(mode, str) or not mode for mode in observed)
    ):
        return "NOT_ESTIMABLE_MODE_METADATA"
    if set(manifest) != set(observed):
        return "NOT_ESTIMABLE_MODE_COVERAGE"
    # Missing/censored endpoints are structural failures and take precedence
    # over diagnostics inferred from the remaining observed sample.
    if evidence["censor_count"] != 0:
        return "NOT_ESTIMABLE_CENSORED_ENDPOINT"
    if evidence["missing_endpoint_count"] != 0:
        return "NOT_ESTIMABLE_MISSING_ENDPOINT"
    counts = evidence["tail_events_by_mode"]
    minimum = evidence["min_tail_events_per_mode"]
    if (
        not isinstance(counts, dict)
        or set(counts) != set(manifest)
        or isinstance(minimum, bool)
        or not isinstance(minimum, int)
        or minimum < 1
        or any(isinstance(counts[m], bool) or not isinstance(counts[m], int) or counts[m] < 0 for m in manifest)
    ):
        return "NOT_ESTIMABLE_MODE_METADATA"
    if any(counts[m] < minimum for m in manifest):
        return "NOT_ESTIMABLE_INSUFFICIENT_TAIL_EVENTS"
    if evidence["temporal_stability"] is not True:
        return "NOT_ESTIMABLE_NONSTATIONARY"
    if evidence["dependence_checked"] is not True:
        return "NOT_ESTIMABLE_DEPENDENCE"
    return "ELIGIBLE_REFERENCE"
