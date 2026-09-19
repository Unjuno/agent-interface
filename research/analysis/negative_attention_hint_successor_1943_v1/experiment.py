#!/usr/bin/env python3
"""Deterministic synthetic attention-hint contract; standard library only."""
import hashlib, json, sys

REGIONS = [
    ("background", "static", "B"),
    ("toolbar", "high", "T"),
    ("target", "critical", "G"),
    ("effect", "high", "E"),
    ("decorative", "low", "D0"),
    ("changed_low", "low", "D1"),
]
CASES = {"unchanged": REGIONS, "changed_low": [(n,p,("D2" if n=="changed_low" else v)) for n,p,v in REGIONS]}
CONTROLS = ("FULL", "ADVISORY_LOW_PRIORITY", "FORCED_EXCLUSION")

def digest(rows):
    return hashlib.sha256(json.dumps(rows, separators=(",", ":"), sort_keys=True).encode()).hexdigest()

def encode(rows, control):
    if control == "FULL":
        return list(rows)
    if control == "ADVISORY_LOW_PRIORITY":
        return [r for r in rows if r[1] != "low"] + [r for r in rows if r[1] == "low"]
    if control == "FORCED_EXCLUSION":
        return [r for r in rows if r[1] != "low"]
    raise ValueError(control)

def main():
    results = []
    for case, rows in CASES.items():
        authoritative = digest(rows)
        for control in CONTROLS:
            packet = encode(rows, control)
            recovered = digest(packet) == authoritative
            results.append({"case": case, "control": control, "recovered": recovered,
                            "packet_bytes": len(json.dumps(packet, separators=(",", ":"))),
                            "authoritative_sha256": authoritative})
    by = {(r["case"], r["control"]): r for r in results}
    assert all(by[(c, "FULL")]["recovered"] for c in CASES)
    assert all(by[(c, "ADVISORY_LOW_PRIORITY")]["recovered"] for c in CASES)
    assert not by[("changed_low", "FORCED_EXCLUSION")]["recovered"]
    assert any(by[(c, "ADVISORY_LOW_PRIORITY")]["packet_bytes"] < by[(c, "FULL")]["packet_bytes"] for c in CASES)
    print(json.dumps({"decision": "PASS_ADVISORY_HINT_CONTRACT_SCOPED", "results": results,
                      "formal_invocations": 1, "reruns": 0, "tuning": 0}, sort_keys=True))
if __name__ == "__main__":
    main()
