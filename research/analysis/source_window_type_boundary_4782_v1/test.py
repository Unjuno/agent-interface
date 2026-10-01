import json
import sys
from pathlib import Path

from research.observation_gating.o3_relevant_region_successor_v1.gate import evaluate_region
from research.observation_gating.o3_relevant_region_3131_v1.source_window_verifier import verify_source_window

CASES = [
    ("int_int_same", 2097155, 2097155),
    ("str_str_same", "2097155", "2097155"),
    ("int_str_cross", 2097155, "2097155"),
    ("str_int_cross", "2097155", 2097155),
    ("int_str_leading_zero", 2097155, "02097155"),
    ("str_int_different", "2097155", 2097156),
]

def run():
    rows = []
    for name, observed, trusted in CASES:
        evidence = {"observation_id":"o1", "intent_epoch":1, "region_id":"r1",
                    "coverage":"COMPLETE", "freshness":"CURRENT", "effect_binding":"BOUND",
                    "authority_grants":0, "ambiguous":False, "source_window":observed}
        decision = evaluate_region(evidence, observation_id="o1", intent_epoch=1,
                                   region_id="r1", trusted_source_window=trusted)
        bound, bind_reason = verify_source_window(evidence, trusted)
        rows.append({"case":name, "observed":observed, "trusted":trusted,
                     "gate_admitted":decision.admitted, "gate_reason":decision.reason,
                     "verifier_bound":bound, "verifier_reason":bind_reason,
                     "strict_identity_matches":type(observed) is type(trusted) and observed == trusted})
    return rows

if __name__ == "__main__":
    if len(sys.argv) != 2: raise SystemExit("usage: python -B test.py RAW.json")
    Path(sys.argv[1]).write_text(json.dumps({"rows":run()}, sort_keys=True,
        separators=(",", ":"))+"\n", encoding="utf-8")
