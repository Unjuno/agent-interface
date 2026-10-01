"""Single-run finite construction candidate for the frozen v2 rule."""
from __future__ import annotations
import hashlib
import itertools
import json
from pathlib import Path
from adjudicator import adjudicate, comparative

HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "construction-01"
FREEZE = HERE / "FREEZE.json"
ORDER = [(1, "recovery"), (1, "coast"), (2, "coast"),
         (2, "recovery"), (3, "recovery"), (3, "coast")]


def make_rows(progress_signs, exposure_signs):
    rows = []
    for order, (pair_id, arm) in enumerate(ORDER, 1):
        p, e = progress_signs[pair_id - 1], exposure_signs[pair_id - 1]
        score = 1 if p == 0 or (p == 1 and arm == "coast") or (p == -1 and arm == "recovery") else 2
        if e == -1:
            lower, upper = (0, 0) if arm == "recovery" else (1, 1)
        elif e == 1:
            lower, upper = (1, 1) if arm == "recovery" else (0, 0)
        else:
            lower, upper = 0, 0
        rows.append({
            "session_id": f"session-{order}", "session_order": order,
            "pair_id": pair_id, "arm": arm,
            "fixture_sha256": "a" * 64, "source_bundle_sha256": "b" * 64,
            "model_contract_sha256": "c" * 64, "seed": 1, "map": "MAP01", "skill": 1,
            "start_fingerprint": f"{pair_id:064x}", "ready_ns": order * 1_000_000_000,
            "horizon_ms": 60_000, "threat_contact_confirmed": True,
            "map_exit": False, "alive_at_horizon": True, "kill_count_gain": score,
            "death_count_gain": 0, "health_loss": 0, "ammo_spent": 0,
            "unsafe_lower_ms": lower, "unsafe_upper_ms": upper,
            "terminal_neutral": True, "stale_action_after_invalidation": False,
            "complete": True, "audit_error_count": 0,
        })
    return rows


def main():
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
            decision = comparative(p, e, True, True)
            integrated = adjudicate(make_rows(p, e))
            cases.append({"progress_signs": p, "exposure_signs": e,
                          "result": decision,
                          "integrated_status": integrated["comparative_status"],
                          "instrumentation_status": integrated["instrumentation_status"]})
    controls = {}

    def record(name, mutate, expected):
        rows = make_rows((1, 1, 0), (-1, -1, 0))
        mutate(rows)
        result = adjudicate(rows)
        controls[name] = {"instrumentation_status": result.get("instrumentation_status"),
                          "comparative_status": result.get("comparative_status"),
                          "reason": result.get("reason"), "expected": expected}

    record("no_threat", lambda r: [x.update(threat_contact_confirmed=False) for x in r],
           ("PASS_INSTRUMENTATION_AND_RELEASE", "HOLD_NOT_EVALUATED", None))
    record("no_useful_event", lambda r: [x.update(kill_count_gain=0) for x in r],
           ("PASS_INSTRUMENTATION_AND_RELEASE", "HOLD_NOT_EVALUATED", None))
    record("identity_hash_malformed", lambda r: r[0].update(model_contract_sha256="not-a-sha256"),
           ("STOP_INTEGRITY", "STOP_INTEGRITY", "identity_format:model_contract_sha256"))
    record("source_identity_mismatch", lambda r: r[0].update(source_bundle_sha256="d" * 64),
           ("STOP_INTEGRITY", "STOP_INTEGRITY", "identity_mismatch:source_bundle_sha256"))
    record("unverified_release", lambda r: r[0].update(terminal_neutral=False),
           ("FAIL_SAFETY", "STOP_SAFETY", "terminal_release"))
    record("stale_action", lambda r: r[0].update(stale_action_after_invalidation=True),
           ("FAIL_SAFETY", "STOP_SAFETY", "stale_action"))
    record("fixture_mismatch", lambda r: r[-1].update(fixture_sha256="d" * 64),
           ("STOP_INTEGRITY", "STOP_INTEGRITY", "identity_mismatch:fixture_sha256"))
    record("pair_start_mismatch", lambda r: r[1].update(start_fingerprint="e" * 64),
           ("STOP_INTEGRITY", "STOP_INTEGRITY", "pair_start_mismatch"))
    record("duplicate_session", lambda r: r[-1].update(session_id=r[0]["session_id"]),
           ("STOP_INTEGRITY", "STOP_INTEGRITY", "session_id_duplicate"))
    record("wrong_counterbalance", lambda r: r[0].update(arm="coast"),
           ("STOP_INTEGRITY", "STOP_INTEGRITY", "counterbalance_order"))
    record("incomplete_audit", lambda r: r[2].update(audit_error_count=1),
           ("STOP_INTEGRITY", "STOP_INTEGRITY", "incomplete_or_audit_errors"))
    record("bad_exposure_interval", lambda r: r[4].update(unsafe_lower_ms=2, unsafe_upper_ms=1),
           ("STOP_INTEGRITY", "STOP_INTEGRITY", "exposure_bounds"))
    raw = {"schema": "t1-paired-rule-construction-raw-v2",
           "freeze_sha256": hashlib.sha256(FREEZE.read_bytes()).hexdigest(),
           "candidate_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           "cases": cases, "case_count": len(cases), "control_cases": controls,
           "candidate_invocations": 1, "candidate_exit_code": 0}
    encoded = (json.dumps(raw, sort_keys=True, indent=2) + "\n").encode()
    (OUT / "RAW.json").write_bytes(encoded)
    run = {"status": "CANDIDATE_EXIT_0", "raw_sha256": hashlib.sha256(encoded).hexdigest(),
           "raw_bytes": len(encoded)}
    (OUT / "RUN.json").write_text(json.dumps(run, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(run, sort_keys=True))


if __name__ == "__main__":
    main()
