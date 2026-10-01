"""T1 paired adjudication rule. Pure logic; no runtime, game, or input imports."""
from __future__ import annotations

EXPECTED_ORDER = [
    (1, "recovery"), (1, "coast"),
    (2, "coast"), (2, "recovery"),
    (3, "recovery"), (3, "coast"),
]
HORIZON_MS = 60_000


def _stop(reason: str) -> dict:
    return {
        "instrumentation_status": "STOP_INTEGRITY",
        "comparative_status": "STOP_INTEGRITY",
        "reason": reason,
    }


def _progress(row: dict) -> tuple[int, int, int, int]:
    return (
        int(row["map_exit"]),
        int(row["alive_at_horizon"]),
        -int(row["death_count_gain"]),
        int(row["kill_count_gain"]),
    )


def _exposure_sign(recovery: dict, coast: dict) -> int:
    if recovery["unsafe_upper_ms"] < coast["unsafe_lower_ms"]:
        return -1
    if recovery["unsafe_lower_ms"] > coast["unsafe_upper_ms"]:
        return 1
    return 0


def comparative_from_signs(progress_signs, exposure_signs, *, threat_present: bool, useful_present: bool) -> str:
    """Classify exactly three pair signs: -1 recovery wins, 0 tie/overlap, +1 coast wins."""
    if len(progress_signs) != 3 or len(exposure_signs) != 3:
        raise ValueError("exactly three matched-pair signs required")
    if any(type(x) is not int or x not in (-1, 0, 1) for x in list(progress_signs) + list(exposure_signs)):
        raise ValueError("pair signs must be -1, 0, or 1 integers")
    if not threat_present or not useful_present:
        return "HOLD_NOT_EVALUATED"
    p_win, p_loss = progress_signs.count(1), progress_signs.count(-1)
    e_win, e_loss = exposure_signs.count(-1), exposure_signs.count(1)
    if p_win >= 2 and p_loss == 0 and e_win >= 2 and e_loss == 0:
        return "PASS_DIRECTIONAL_FIXTURE_SCOPED"
    if p_loss >= 2 and p_win == 0 and e_loss >= 2 and e_win == 0:
        return "FAIL_DIRECTIONAL_FIXTURE_SCOPED"
    return "UNCERTAIN"


def adjudicate(sessions: list[dict]) -> dict:
    if not isinstance(sessions, list) or len(sessions) != 6:
        return _stop("session_count")
    try:
        if any(not isinstance(row, dict) for row in sessions):
            return _stop("session_shape")
        observed_order = [(row["pair_id"], row["arm"]) for row in sessions]
        if observed_order != EXPECTED_ORDER:
            return _stop("counterbalance_order")
        if [row.get("session_order") for row in sessions] != [1, 2, 3, 4, 5, 6]:
            return _stop("session_order")
        required = {
            "session_id", "pair_id", "arm", "fixture_sha256", "source_bundle_sha256",
            "model_contract_sha256", "seed", "map", "skill", "start_fingerprint",
            "session_order",
            "ready_ns", "horizon_ms", "threat_contact_confirmed", "map_exit",
            "alive_at_horizon", "kill_count_gain", "death_count_gain", "health_loss", "ammo_spent",
            "unsafe_lower_ms", "unsafe_upper_ms", "terminal_neutral",
            "stale_action_after_invalidation", "complete", "audit_error_count",
        }
        if any(not isinstance(row, dict) or not required <= row.keys() for row in sessions):
            return _stop("required_fields")
        if any(type(row["pair_id"]) is not int or type(row["session_order"]) is not int
               for row in sessions):
            return _stop("integer:pair_or_order")
        if len({row["session_id"] for row in sessions}) != 6:
            return _stop("session_id_duplicate")
        for row in sessions:
            if row["arm"] not in ("recovery", "coast"):
                return _stop("arm")
            if type(row["horizon_ms"]) is not int or row["horizon_ms"] != HORIZON_MS:
                return _stop("horizon")
            if type(row["ready_ns"]) is not int or row["ready_ns"] < 0:
                return _stop("ready_time")
            for key in ("threat_contact_confirmed", "map_exit", "alive_at_horizon",
                        "terminal_neutral", "stale_action_after_invalidation", "complete"):
                if type(row[key]) is not bool:
                    return _stop("boolean:" + key)
            for key in ("kill_count_gain", "death_count_gain", "health_loss", "ammo_spent", "audit_error_count",
                        "unsafe_lower_ms", "unsafe_upper_ms"):
                if type(row[key]) is not int or row[key] < 0:
                    return _stop("integer:" + key)
            if row["map_exit"] and not row["alive_at_horizon"]:
                return _stop("exit_dead_contradiction")
            if row["unsafe_lower_ms"] > row["unsafe_upper_ms"] or row["unsafe_upper_ms"] > HORIZON_MS:
                return _stop("exposure_bounds")
            if not row["complete"] or row["audit_error_count"] != 0:
                return _stop("incomplete_or_audit_errors")
        if len({row["fixture_sha256"] for row in sessions}) != 1:
            return _stop("fixture_mismatch")
        for key in ("source_bundle_sha256", "model_contract_sha256", "seed", "map", "skill"):
            if len({row[key] for row in sessions}) != 1:
                return _stop("identity_mismatch:" + key)
        for key in ("fixture_sha256", "source_bundle_sha256", "model_contract_sha256"):
            for value in {row[key] for row in sessions}:
                if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value.lower()):
                    return _stop("identity_format:" + key)
        if any(type(row["seed"]) is not int or row["seed"] < 0 for row in sessions):
            return _stop("seed_format")
        if any(type(row["skill"]) is not int or row["skill"] < 1 for row in sessions):
            return _stop("skill_format")
        if any(not isinstance(row["map"], str) or not row["map"] for row in sessions):
            return _stop("map_format")
        for pair_id in (1, 2, 3):
            pair = [row for row in sessions if row["pair_id"] == pair_id]
            if len(pair) != 2 or pair[0]["start_fingerprint"] != pair[1]["start_fingerprint"]:
                return _stop("pair_start_mismatch")
        if any(not row["terminal_neutral"] for row in sessions):
            return {"instrumentation_status": "FAIL_SAFETY", "comparative_status": "STOP_SAFETY",
                    "reason": "terminal_release"}
        if any(row["stale_action_after_invalidation"] for row in sessions):
            return {"instrumentation_status": "FAIL_SAFETY", "comparative_status": "STOP_SAFETY",
                    "reason": "stale_action"}

        instrumentation = "PASS_INSTRUMENTATION_AND_RELEASE"
        recovery_wins = 0
        recovery_losses = 0
        exposure_signs = []
        progress_signs = []
        threat_pairs = 0
        useful_present = False
        for pair_id in (1, 2, 3):
            pair = {row["arm"]: row for row in sessions if row["pair_id"] == pair_id}
            recovery, coast = pair["recovery"], pair["coast"]
            if recovery["threat_contact_confirmed"] and coast["threat_contact_confirmed"]:
                threat_pairs += 1
            rp, cp = _progress(recovery), _progress(coast)
            if rp > cp:
                progress_signs.append(1)
                recovery_wins += 1
            elif rp < cp:
                progress_signs.append(-1)
                recovery_losses += 1
            else:
                progress_signs.append(0)
            exposure_signs.append(_exposure_sign(recovery, coast))
            useful_present = useful_present or any(
                row["map_exit"] or row["kill_count_gain"] > 0 for row in pair.values()
            )

        comparison = comparative_from_signs(
            progress_signs, exposure_signs,
            threat_present=threat_pairs == 3,
            useful_present=useful_present,
        )
        return {
            "instrumentation_status": instrumentation,
            "comparative_status": comparison,
            "progress_pair_signs": progress_signs,
            "exposure_pair_signs": exposure_signs,
            "recovery_progress_wins": recovery_wins,
            "recovery_progress_losses": recovery_losses,
            "threat_confirmed_pairs": threat_pairs,
            "any_positive_useful_outcome": useful_present,
        }
    except (KeyError, TypeError, ValueError):
        return _stop("malformed_input")
