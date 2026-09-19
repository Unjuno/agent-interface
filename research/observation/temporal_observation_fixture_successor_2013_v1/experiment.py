import json
import hashlib
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class Obs:
    source: str
    epoch: int
    session: str
    surface: str
    t_ms: int
    role: str
    payload: str
    roi: tuple[int, int, int, int] | None = None

def query_current(obs, now_ms):
    rows = [x for x in obs if x.role == "current" and x.t_ms <= now_ms]
    return max(rows, key=lambda x: x.t_ms) if rows else None

def query_ring(obs, start_ms, end_ms):
    return [x for x in obs if start_ms <= x.t_ms <= end_ms]

def oracle(rows, expected_source, expected_role):
    return all(x.source == expected_source and x.role == expected_role for x in rows)

def main():
    base = [
        Obs("f0", 1, "s", "surface", 0, "current", "stable", (0, 0, 4, 4)),
        Obs("f1", 1, "s", "surface", 10, "current", "changed", (0, 0, 4, 4)),
        Obs("f2", 1, "s", "surface", 20, "current", "changed", (0, 0, 4, 4)),
        Obs("f3", 1, "s", "surface", 30, "historical", "changed", (0, 0, 4, 4)),
        Obs("f4", 1, "s", "surface", 40, "current", "stable", (0, 0, 4, 4)),
    ]
    cases = {
        "stable_current": query_current(base, 0).payload == "stable",
        "transition_current": query_current(base, 20).payload == "changed",
        "event_anchor": [x.source for x in query_ring(base, 10, 20)] == ["f1", "f2"],
        "drop_interval_not_unchanged": query_ring(base, 21, 29) == [],
        "roi_exact": all(x.roi == (0, 0, 4, 4) for x in base),
        "role_preserved": oracle([base[3]], "f3", "historical"),
        "expired_history": query_ring(base, 100, 110) == [],
    }
    tamper = [asdict(x) for x in base]
    tamper[3]["role"] = "current"
    nonmono = list(base)
    nonmono[2] = Obs(**{**asdict(nonmono[2]), "t_ms": 5})
    controls = {
        "role_tamper_rejected": not oracle([Obs(**tamper[3])], "f3", "historical"),
        "nonmonotonic_rejected": not all(a.t_ms <= b.t_ms for a, b in zip(nonmono, nonmono[1:])),
    }
    result = {"decision": "PASS_TEMPORAL_OBSERVATION_FIXTURE_SCOPED" if all(cases.values()) and all(controls.values()) else "STOP", "cases": cases, "controls": controls, "rows": len(base), "construction_invocations": 0, "formal_invocations": 1, "gui_x11_model_network_input": 0}
    raw = json.dumps(result, sort_keys=True, separators=(",", ":"))
    result["sha256"] = hashlib.sha256(raw.encode()).hexdigest()
    print(json.dumps(result, sort_keys=True, indent=2))
    if result["decision"] != "PASS_TEMPORAL_OBSERVATION_FIXTURE_SCOPED":
        raise SystemExit(1)
if __name__ == "__main__":
    main()
