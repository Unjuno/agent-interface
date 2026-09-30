"""Small, non-authoritative checker for the #5315 T0 fixture."""


def check_certificate(calibration, arm):
    required = (
        "population_id",
        "calibration_set_id",
        "calibration_digest",
        "n",
        "errors",
        "loss_bound",
        "version",
        "age_hours",
        "freshness_limit_hours",
        "exchangeable",
        "method",
        "claim_scope",
    )
    if any(key not in calibration for key in required):
        return "REJECT_MISSING_BINDING"
    if calibration["method"] != "CRC_MARGINAL":
        return "REJECT_UNSUPPORTED_METHOD"
    if calibration["claim_scope"] != "MARGINAL_POPULATION_RISK":
        return "REJECT_UNSUPPORTED_SCOPE"
    if not calibration["calibration_digest"]:
        return "REJECT_MISSING_BINDING"
    if calibration["population_id"] != arm["population_id"]:
        return "REJECT_POPULATION_MISMATCH"
    if calibration["version"] != arm["version"]:
        return "REJECT_VERSION_MISMATCH"
    if arm["age_hours"] > calibration["freshness_limit_hours"]:
        return "REJECT_STALE"
    if not calibration["exchangeable"] or not arm["exchangeable"]:
        return "REJECT_ASSUMPTION_INVALID"
    if arm["assumption_status"] != "VALIDATED":
        return "REJECT_ASSUMPTION_INVALID"
    return "ALLOW_MARGINAL_CLAIM_ONLY"


def crc_upper(n, errors, loss_bound):
    if n <= 0 or errors < 0 or errors > n or loss_bound < 0:
        raise ValueError("invalid bounded-loss calibration record")
    empirical = errors / n
    return n / (n + 1) * empirical + loss_bound / (n + 1)
