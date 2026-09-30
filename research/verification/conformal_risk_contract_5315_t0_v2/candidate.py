"""Digest- and scope-checking candidate for the synthetic #5315 successor."""

import hashlib
import json


def record_digest(record_bytes):
    return "sha256:" + hashlib.sha256(record_bytes).hexdigest()


def derived_stats(records):
    if not isinstance(records, list) or not records or any(value not in (0, 1) for value in records):
        raise ValueError("calibration rows must be a non-empty list of binary losses")
    return len(records), sum(records)


def crc_upper(n, errors, loss_bound):
    if n <= 0 or errors < 0 or errors > n or loss_bound < 0:
        raise ValueError("invalid bounded-loss calibration record")
    return n / (n + 1) * (errors / n) + loss_bound / (n + 1)


def check_certificate(cal, arm, record_bytes, records):
    required = (
        "population_id", "calibration_set_id", "calibration_digest", "n", "errors",
        "loss_bound", "target_risk", "version", "age_hours", "freshness_limit_hours",
        "exchangeable", "method", "claim_scope",
    )
    if any(key not in cal for key in required):
        return "REJECT_MISSING_BINDING"
    if cal["calibration_digest"] != record_digest(record_bytes):
        return "REJECT_CALIBRATION_DIGEST_MISMATCH"
    try:
        n, errors = derived_stats(records)
    except (TypeError, ValueError):
        return "REJECT_INVALID_CALIBRATION_ROWS"
    if (cal["n"], cal["errors"]) != (n, errors):
        return "REJECT_CALIBRATION_STATS_MISMATCH"
    if cal["method"] != "CRC_MARGINAL":
        return "REJECT_UNSUPPORTED_METHOD"
    if cal["claim_scope"] != "MARGINAL_POPULATION_RISK":
        return "REJECT_UNSUPPORTED_SCOPE"
    if crc_upper(n, errors, cal["loss_bound"]) > cal["target_risk"]:
        return "REJECT_TARGET_NOT_MET"
    if cal["population_id"] != arm["population_id"]:
        return "REJECT_POPULATION_MISMATCH"
    if cal["version"] != arm["version"]:
        return "REJECT_VERSION_MISMATCH"
    if arm["age_hours"] > cal["freshness_limit_hours"]:
        return "REJECT_STALE"
    if not cal["exchangeable"] or not arm["exchangeable"]:
        return "REJECT_ASSUMPTION_INVALID"
    if arm["assumption_status"] != "VALIDATED":
        return "REJECT_ASSUMPTION_INVALID"
    return "ALLOW_MARGINAL_CLAIM_ONLY"
