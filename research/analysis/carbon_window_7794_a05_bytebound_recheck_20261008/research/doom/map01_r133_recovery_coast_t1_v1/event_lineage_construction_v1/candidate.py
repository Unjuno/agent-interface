from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).parent
FIX = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8-sig"))
SCORER = {"THREAT_CONTACT", "KILL_COUNT_INCREASE", "MAP_EXIT"}


def validate(data):
    errors = []
    sessions = data.get("sessions", [])
    expected = {(p, a) for p in FIX["assigned_pairs"] for a in FIX["arms"]}
    actual = [(s.get("pair"), s.get("arm")) for s in sessions]
    if len(actual) != 6 or set(actual) != expected or len(set(actual)) != 6:
        errors.append("ASSIGNED_DENOMINATOR_MISMATCH")
    ids = [e.get("id") for s in sessions for e in s.get("events", [])]
    if len(ids) != len(set(ids)) or None in ids:
        errors.append("EVENT_ID_DUPLICATE_OR_MISSING")
    for s in sessions:
        ev = s.get("events", [])
        kinds = [e.get("kind") for e in ev]
        if any(e.get("kind") in SCORER and e.get("controller_visible") is not False for e in ev):
            errors.append("SCORER_LEAK")
        obs = [e for e in ev if e.get("kind") == "OBSERVATION"]
        for a in [e for e in ev if e.get("kind") == "ACTUATION_ADMITTED"]:
            latest = max((o.get("sequence", -1) for o in obs if o.get("t_ms", -1) <= a.get("t_ms", -1)), default=-1)
            if a.get("observation_sequence", latest) != latest:
                errors.append("STALE_OBSERVATION_SEQUENCE")
        plans = [e for e in ev if e.get("kind") == "PLAN_ADMITTED"]
        acts = [e for e in ev if e.get("kind") == "ACTUATION_ADMITTED"]
        if s.get("arm") == "recovery" and plans:
            if not acts or not any(a.get("plan_id") == plans[0].get("plan_id") and a.get("step_id") == plans[0].get("step_id") for a in acts):
                errors.append("PLAN_ACTUATION_MISMATCH")
            if not {"KEY_DOWN_ACK", "KEY_UP_ACK", "OWNER_EMPTY_RELEASE"}.issubset(kinds):
                errors.append("RELEASE_BRACKET_INCOMPLETE")
        times = [e.get("t_ms") for e in ev]
        if times != sorted(times): errors.append("EVENT_TIME_ORDER")
        if s.get("arm") == "coast" and acts: errors.append("COAST_HAS_ACTUATION")
    pairs = {}
    for s in sessions:
        pairs.setdefault(s["pair"], {})[s["arm"]] = s
    exposure = {p: all(any(e.get("kind") == "THREAT_CONTACT" for e in x.get("events", [])) for x in arms.values()) for p, arms in pairs.items()}
    if not all(exposure.values()): errors.append("PAIR_EXPOSURE_INCOMPLETE")
    useful = any(e.get("kind") in {"KILL_COUNT_INCREASE", "MAP_EXIT"} for s in sessions for e in s.get("events", []))
    if not useful: errors.append("NO_USEFUL_SCORER_EVENT")
    status = "PASS_CONSTRUCTION_ONLY" if not errors else "HOLD_CONSTRUCTION"
    return {"status": status, "errors": sorted(set(errors)), "denominator_sessions": len(sessions), "denominator_pairs": len(pairs), "exposure_by_pair": exposure, "useful_event_observed": useful, "causal_credit": False, "formal_t1_authorized": False}


def main():
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = validate(data)
    print(json.dumps(out, sort_keys=True))
    return 0 if out["status"] == "PASS_CONSTRUCTION_ONLY" else 1

if __name__ == "__main__": raise SystemExit(main())
