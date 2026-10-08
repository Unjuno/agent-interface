"""Exhaustively check the proposed T1 paired decision rule against finite cases."""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

from adjudicator import adjudicate, comparative_from_signs

HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "construction-01"
FREEZE = HERE / "FREEZE.json"


ORDER = [
    (1, "recovery"), (1, "coast"),
    (2, "coast"), (2, "recovery"),
    (3, "recovery"), (3, "coast"),
]


def make_sessions(progress_signs, exposure_signs):
    rows = []
    for order, (pair_id, arm) in enumerate(ORDER, 1):
        pair_index = pair_id - 1
        progress_sign = progress_signs[pair_index]
        exposure_sign = exposure_signs[pair_index]
        score = 1
        if progress_sign == 1 and arm == "recovery":
            score = 2
        elif progress_sign == -1 and arm == "coast":
            score = 2
        if exposure_sign == -1:
            lower, upper = ((0, 0) if arm == "recovery" else (1, 1))
        elif exposure_sign == 1:
            lower, upper = ((1, 1) if arm == "recovery" else (0, 0))
        else:
            lower, upper = (0, 0)
        rows.append({
            "session_id": f"session-{order}", "session_order": order,
            "pair_id": pair_id, "arm": arm,
            "fixture_sha256": "a" * 64, "source_bundle_sha256": "b" * 64,
            "model_contract_sha256": "c" * 64, "seed": 1, "map": "MAP01", "skill": 1,
            "start_fingerprint": f"{pair_id:064x}", "ready_ns": order * 1_000_000_000,
            "horizon_ms": 60_000, "threat_contact_confirmed": True,
            "map_exit": False, "alive_at_horizon": True, "kill_count_gain": score,
            "death_count_gain": 0,
            "health_loss": 0, "ammo_spent": 0,
            "unsafe_lower_ms": lower, "unsafe_upper_ms": upper,
            "terminal_neutral": True, "stale_action_after_invalidation": False,
            "complete": True, "audit_error_count": 0,
        })
    return rows


def main() -> int:
    if OUT.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    for name, expected in freeze["pinned_sha256"].items():
        if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != expected:
            raise SystemExit("STOP_SOURCE_DRIFT:" + name)
    OUT.mkdir(parents=True, exist_ok=False)
    cases = []
    for p in itertools.product((-1, 0, 1), repeat=3):
        for e in itertools.product((-1, 0, 1), repeat=3):
            result = comparative_from_signs(p, e, threat_present=True, useful_present=True)
            integrated = adjudicate(make_sessions(p, e))
            cases.append({"progress_signs": p, "exposure_signs": e, "result": result,
                          "integrated_status": integrated["comparative_status"],
                          "instrumentation_status": integrated["instrumentation_status"]})
    controls = {}

    def record_control(name, mutate=None, expected=None):
        rows = make_sessions((1, 1, 0), (-1, -1, 0))
        if mutate is not None:
            mutate(rows)
        decision = adjudicate(rows)
        controls[name] = {"instrumentation_status": decision.get("instrumentation_status"),
                          "comparative_status": decision.get("comparative_status"),
                          "reason": decision.get("reason"), "expected": expected}

    record_control("no_threat", lambda rows: [row.update(threat_contact_confirmed=False) for row in rows],
                   ("PASS_INSTRUMENTATION_AND_RELEASE", "HOLD_NOT_EVALUATED", None))
    record_control("no_useful_event", lambda rows: [row.update(map_exit=False, kill_count_gain=0) for row in rows],
                   ("PASS_INSTRUMENTATION_AND_RELEASE", "HOLD_NOT_EVALUATED", None))
    record_control("identity_hash_malformed", lambda rows: rows[0].update(model_contract_sha256="not-a-sha256"),
                   ("STOP_INTEGRITY", "STOP_INTEGRITY", "identity_format:model_contract_sha256"))
    record_control("unverified_release", lambda rows: rows[0].update(terminal_neutral=False),
                   ("FAIL_SAFETY", "STOP_SAFETY", "terminal_release"))
    record_control("stale_action", lambda rows: rows[0].update(stale_action_after_invalidation=True),
                   ("FAIL_SAFETY", "STOP_SAFETY", "stale_action"))
    record_control("fixture_mismatch", lambda rows: rows[-1].update(fixture_sha256="d" * 64),
                   ("STOP_INTEGRITY", "STOP_INTEGRITY", "fixture_mismatch"))
    record_control("pair_start_mismatch", lambda rows: rows[1].update(start_fingerprint="e" * 64),
                   ("STOP_INTEGRITY", "STOP_INTEGRITY", "pair_start_mismatch"))
    record_control("duplicate_session", lambda rows: rows[-1].update(session_id=rows[0]["session_id"]),
                   ("STOP_INTEGRITY", "STOP_INTEGRITY", "session_id_duplicate"))
    record_control("wrong_counterbalance", lambda rows: rows[0].update(arm="coast"),
                   ("STOP_INTEGRITY", "STOP_INTEGRITY", "counterbalance_order"))
    record_control("incomplete_audit", lambda rows: rows[2].update(audit_error_count=1),
                   ("STOP_INTEGRITY", "STOP_INTEGRITY", "incomplete_or_audit_errors"))
    record_control("bad_exposure_interval", lambda rows: rows[4].update(unsafe_lower_ms=2, unsafe_upper_ms=1),
                   ("STOP_INTEGRITY", "STOP_INTEGRITY", "exposure_bounds"))
    record_control("source_drift_identity", lambda rows: rows[0].update(source_bundle_sha256="f" * 64),
                   ("STOP_INTEGRITY", "STOP_INTEGRITY", "identity_mismatch:source_bundle_sha256"))
    raw = {
        "schema": "t1-paired-rule-construction-raw-v1",
        "freeze_sha256": hashlib.sha256(FREEZE.read_bytes()).hexdigest(),
        "candidate_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "cases": cases,
        "case_count": len(cases),
        "control_cases": controls,
        "candidate_invocations": 1,
        "candidate_exit_code": 0,
    }
    raw_bytes = (json.dumps(raw, sort_keys=True, indent=2) + "\n").encode("utf-8")
    (OUT / "RAW.json").write_bytes(raw_bytes)
    run = {"status": "CANDIDATE_EXIT_0", "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
           "raw_bytes": len(raw_bytes)}
    (OUT / "RUN.json").write_text(json.dumps(run, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(run, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
