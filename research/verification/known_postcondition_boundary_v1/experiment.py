from __future__ import annotations
import argparse, json
from pathlib import Path

TYPES = ("file_digest", "window_geometry", "typed_state")
POLICIES = ("RICH_AGENT_FIRST", "DETERMINISTIC_FIRST", "DETERMINISTIC_ONLY_FOR_KNOWN")
SCENARIOS = ("valid", "no_effect", "stale", "wrong_target", "partial", "ambiguous", "missing_receipt", "malformed", "pixel_only", "cleanup_failure")
KNOWN = {"valid", "no_effect", "stale", "wrong_target", "partial", "pixel_only"}

def contract(kind, scenario):
    expected = {"file_digest":"sha256:new", "window_geometry":"1024x768", "typed_state":"saved"}[kind]
    observed = expected if scenario == "valid" else {
        "no_effect":"sha256:old" if kind == "file_digest" else "800x600" if kind == "window_geometry" else "dirty",
        "partial":"sha256:partial" if kind == "file_digest" else "1024x600" if kind == "window_geometry" else "saving",
        "pixel_only":"sha256:pixel" if kind == "file_digest" else "1024x768" if kind == "window_geometry" else "saved",
    }.get(scenario, expected)
    return {"kind":kind,"scenario":scenario,"target":"target-"+kind,"expected":expected,"observed":observed,
            "receipt": scenario not in {"missing_receipt", "ambiguous"},
            "sequence": 7 if scenario not in {"stale", "malformed"} else 3,
            "target_observed": scenario != "wrong_target",
            "pixel_changed": scenario == "pixel_only"}

def verify(e):
    if not isinstance(e, dict) or e.get("kind") not in TYPES: return {"verdict":"ESCALATE_RICH_AGENT","reason":"malformed"}
    if e.get("scenario") == "cleanup_failure": return {"verdict":"ESCALATE_RICH_AGENT","reason":"cleanup_failure"}
    if not e.get("receipt"): return {"verdict":"ESCALATE_RICH_AGENT","reason":"missing_or_ambiguous_receipt"}
    if e.get("sequence") != 7: return {"verdict":"ESCALATE_RICH_AGENT","reason":"stale_observation"}
    if not e.get("target_observed"): return {"verdict":"ESCALATE_RICH_AGENT","reason":"wrong_target"}
    if e.get("observed") == e.get("expected") and not e.get("pixel_changed"):
        return {"verdict":"PASS_POSTCONDITION","reason":"exact_typed_effect"}
    return {"verdict":"FAIL_POSTCONDITION","reason":"effect_mismatch"}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("out",type=Path); a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=False)
    rows=[]
    for kind in TYPES:
      for scenario in SCENARIOS:
        e=contract(kind,scenario); v=verify(e)
        for policy in POLICIES:
          escalation = policy == "RICH_AGENT_FIRST" or (policy == "DETERMINISTIC_FIRST" and v["verdict"] == "ESCALATE_RICH_AGENT") or (policy == "DETERMINISTIC_ONLY_FOR_KNOWN" and scenario not in KNOWN)
          rows.append({"kind":kind,"scenario":scenario,"policy":policy,"evidence":e,"verifier":v,"rich_agent_calls":int(escalation)})
    (a.out/"raw.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"schema":"agent-interface/known-postcondition-boundary-v1","cases":len(rows),"status":"PASS_SOURCE_EXECUTION"},indent=2))
if __name__ == "__main__": main()
