import copy
import json
from pathlib import Path
from low_demand_t0_audit import audit

rows = json.loads(Path(__file__).with_name("low_demand_t0_candidate.json").read_text(encoding="utf-8"))
mutations = {}

bad = copy.deepcopy(rows); bad[1]["facts"]["receipt"] = "different"
mutations["mismatched_source_facts"] = bad
bad = copy.deepcopy(rows); next(r for r in bad if r["condition"] == "RETRIEVAL")["exposure"]["question"] += " verified True"
mutations["answer_leak"] = bad
bad = copy.deepcopy(rows); bad[0]["urgent_event"] = True
mutations["urgent_gap"] = bad
bad = copy.deepcopy(rows); bad[0]["delay_bucket"] += 1
mutations["condition_correlated_delay"] = bad
bad = copy.deepcopy(rows); bad[0]["safe_action"] = "blind_replay"
mutations["blind_replay"] = bad

results = {name: audit(candidate)["audit"] for name, candidate in mutations.items()}
out = {"mutation_checks": results, "all_rejected": all(status == "FAIL_METHOD" for status in results.values()),
       "scope": "auditor sensitivity to five declared corruptions; not proof of universal auditor correctness"}
Path(__file__).with_name("low_demand_t0_mutation_audit.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps(out, sort_keys=True))
raise SystemExit(0 if out["all_rejected"] else 1)
