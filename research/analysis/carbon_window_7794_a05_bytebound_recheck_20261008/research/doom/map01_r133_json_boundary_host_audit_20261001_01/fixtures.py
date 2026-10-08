from __future__ import annotations

import copy


def valid_rows():
    base = {
        "session_id": "session-1", "session_order": 1, "pair_id": 1,
        "arm": "recovery", "fixture_sha256": "a" * 64,
        "source_bundle_sha256": "b" * 64, "model_contract_sha256": "c" * 64,
        "seed": 1, "map": "MAP01", "skill": 1,
        "start_fingerprint": "start-1", "ready_ns": 1, "horizon_ms": 60000,
        "threat_contact_confirmed": True, "map_exit": False,
        "alive_at_horizon": True, "kill_count_gain": 1,
        "death_count_gain": 0, "health_loss": 0, "ammo_spent": 0,
        "unsafe_lower_ms": 0, "unsafe_upper_ms": 0,
        "terminal_neutral": True, "stale_action_after_invalidation": False,
        "complete": True, "audit_error_count": 0,
    }
    order = [(1, "recovery"), (1, "coast"), (2, "coast"),
             (2, "recovery"), (3, "recovery"), (3, "coast")]
    rows = []
    for i, (pair_id, arm) in enumerate(order, 1):
        row = dict(base, session_id=f"session-{i}", session_order=i,
                   pair_id=pair_id, arm=arm,
                   start_fingerprint=f"start-{pair_id}")
        rows.append(row)
    return rows


def cases():
    controls = [
        ("pair_id_bool", lambda r: r[0].__setitem__("pair_id", True), "integer:pair_or_order"),
        ("session_order_bool", lambda r: r[0].__setitem__("session_order", True), "integer:pair_or_order"),
        ("ready_ns_float", lambda r: r[0].__setitem__("ready_ns", 1.0), "ready_time"),
        ("map_exit_int", lambda r: r[0].__setitem__("map_exit", 0), "boolean:map_exit"),
        ("kill_count_bool", lambda r: r[0].__setitem__("kill_count_gain", True), "integer:kill_count_gain"),
        ("audit_error_float", lambda r: r[0].__setitem__("audit_error_count", 0.0), "integer:audit_error_count"),
        ("hash_non_string", lambda r: r[0].__setitem__("fixture_sha256", True), "identity_format:fixture_sha256"),
        ("row_count_5", lambda r: r.pop(), "session_count"),
    ]
    result = [("pristine", valid_rows(), "PASS_INSTRUMENTATION_AND_RELEASE", None)]
    for name, mutate, reason in controls:
        rows = copy.deepcopy(valid_rows())
        mutate(rows)
        result.append((name, rows, "STOP_INTEGRITY", reason))
    return result
