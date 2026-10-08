"""Pure paired T1 adjudicator. Identity syntax is validated before equality."""
from __future__ import annotations

EXPECTED_ORDER = [(1, "recovery"), (1, "coast"), (2, "coast"),
                  (2, "recovery"), (3, "recovery"), (3, "coast")]
HORIZON_MS = 60_000
HASH_FIELDS = ("fixture_sha256", "source_bundle_sha256", "model_contract_sha256")


def stop(reason: str) -> dict:
    return {"instrumentation_status": "STOP_INTEGRITY",
            "comparative_status": "STOP_INTEGRITY", "reason": reason}


def comparative(progress, exposure, threat_present, useful_present):
    if not threat_present or not useful_present:
        return "HOLD_NOT_EVALUATED"
    pw, pl = progress.count(1), progress.count(-1)
    ew, el = exposure.count(-1), exposure.count(1)
    if pw >= 2 and pl == 0 and ew >= 2 and el == 0:
        return "PASS_DIRECTIONAL_FIXTURE_SCOPED"
    if pl >= 2 and pw == 0 and el >= 2 and ew == 0:
        return "FAIL_DIRECTIONAL_FIXTURE_SCOPED"
    return "UNCERTAIN"


def _progress(row):
    return (int(row["map_exit"]), int(row["alive_at_horizon"]),
            -int(row["death_count_gain"]), int(row["kill_count_gain"]))


def adjudicate(rows):
    if not isinstance(rows, list) or len(rows) != 6:
        return stop("session_count")
    try:
        if any(not isinstance(r, dict) for r in rows):
            return stop("session_shape")
        required = {"session_id", "session_order", "pair_id", "arm", *HASH_FIELDS,
                    "seed", "map", "skill", "start_fingerprint", "ready_ns",
                    "horizon_ms", "threat_contact_confirmed", "map_exit",
                    "alive_at_horizon", "kill_count_gain", "death_count_gain",
                    "health_loss", "ammo_spent", "unsafe_lower_ms", "unsafe_upper_ms",
                    "terminal_neutral", "stale_action_after_invalidation", "complete",
                    "audit_error_count"}
        if any(not required <= r.keys() for r in rows):
            return stop("required_fields")
        # V2 invariant: per-row syntactic validity precedes any equality checks.
        for r in rows:
            for field in HASH_FIELDS:
                value = r[field]
                if (not isinstance(value, str) or len(value) != 64 or
                    any(c not in "0123456789abcdef" for c in value.lower())):
                    return stop("identity_format:" + field)
        if [(r["pair_id"], r["arm"]) for r in rows] != EXPECTED_ORDER:
            return stop("counterbalance_order")
        if [r["session_order"] for r in rows] != [1, 2, 3, 4, 5, 6]:
            return stop("session_order")
        if len({r["session_id"] for r in rows}) != 6:
            return stop("session_id_duplicate")
        for field in HASH_FIELDS:
            if len({r[field] for r in rows}) != 1:
                return stop("identity_mismatch:" + field)
        for field in ("seed", "map", "skill"):
            if len({r[field] for r in rows}) != 1:
                return stop("identity_mismatch:" + field)
        if (type(rows[0]["seed"]) is not int or rows[0]["seed"] < 0 or
            not isinstance(rows[0]["map"], str) or not rows[0]["map"] or
            type(rows[0]["skill"]) is not int or rows[0]["skill"] < 1):
            return stop("identity_scalar_format")
        for r in rows:
            if type(r["pair_id"]) is not int or type(r["session_order"]) is not int:
                return stop("integer:pair_or_order")
            if r["arm"] not in ("recovery", "coast"):
                return stop("arm")
            if type(r["horizon_ms"]) is not int or r["horizon_ms"] != HORIZON_MS:
                return stop("horizon")
            if type(r["ready_ns"]) is not int or r["ready_ns"] < 0:
                return stop("ready_time")
            for key in ("threat_contact_confirmed", "map_exit", "alive_at_horizon",
                        "terminal_neutral", "stale_action_after_invalidation", "complete"):
                if type(r[key]) is not bool:
                    return stop("boolean:" + key)
            for key in ("kill_count_gain", "death_count_gain", "health_loss", "ammo_spent",
                        "audit_error_count", "unsafe_lower_ms", "unsafe_upper_ms"):
                if type(r[key]) is not int or r[key] < 0:
                    return stop("integer:" + key)
            if r["map_exit"] and not r["alive_at_horizon"]:
                return stop("exit_dead_contradiction")
            if r["unsafe_lower_ms"] > r["unsafe_upper_ms"] or r["unsafe_upper_ms"] > HORIZON_MS:
                return stop("exposure_bounds")
            if not r["complete"] or r["audit_error_count"] != 0:
                return stop("incomplete_or_audit_errors")
        for p in (1, 2, 3):
            pair = [r for r in rows if r["pair_id"] == p]
            if (len(pair) != 2 or pair[0]["start_fingerprint"] != pair[1]["start_fingerprint"]):
                return stop("pair_start_mismatch")
        if any(not r["terminal_neutral"] for r in rows):
            return {"instrumentation_status": "FAIL_SAFETY", "comparative_status": "STOP_SAFETY",
                    "reason": "terminal_release"}
        if any(r["stale_action_after_invalidation"] for r in rows):
            return {"instrumentation_status": "FAIL_SAFETY", "comparative_status": "STOP_SAFETY",
                    "reason": "stale_action"}
        progress, exposure, threats, useful = [], [], 0, False
        for p in (1, 2, 3):
            pair = {r["arm"]: r for r in rows if r["pair_id"] == p}
            rec, coast = pair["recovery"], pair["coast"]
            threats += int(rec["threat_contact_confirmed"] and coast["threat_contact_confirmed"])
            rp, cp = _progress(rec), _progress(coast)
            progress.append(1 if rp > cp else -1 if rp < cp else 0)
            exposure.append(-1 if rec["unsafe_upper_ms"] < coast["unsafe_lower_ms"]
                            else 1 if rec["unsafe_lower_ms"] > coast["unsafe_upper_ms"] else 0)
            useful |= any(r["map_exit"] or r["kill_count_gain"] > 0 for r in pair.values())
        return {"instrumentation_status": "PASS_INSTRUMENTATION_AND_RELEASE",
                "comparative_status": comparative(progress, exposure, threats == 3, useful),
                "progress_pair_signs": progress, "exposure_pair_signs": exposure,
                "threat_confirmed_pairs": threats, "any_positive_useful_outcome": useful}
    except (KeyError, TypeError, ValueError):
        return stop("malformed_input")
