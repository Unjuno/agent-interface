import json
from pathlib import Path

ROOT = Path(__file__).parent
m = json.loads((ROOT / "manifest.json").read_text())
r = json.loads((ROOT / "RESULT.json").read_text())
errors = []
terms = ["top-down","topdown","geometric scaffold","depth map","side view","occupancy sketch","spatial scaffold"]
explicit = sum(m["indexed_counts"][x] for x in terms) + m["delta_scan"]["scaffold_term_hits"]
if explicit != r["explicit_scaffold_hits"]: errors.append("scaffold_count")
if m["indexed_to_main_added_files"] != m["delta_scan"]["files_scanned"]: errors.append("delta_coverage")
if r["invocation"] != {"formal_invocations":1,"reruns":0,"replacements":0,"tuning":0}: errors.append("invocation")
expected = "PASS_RETAINED_GEOMETRIC_SCAFFOLD_IDENTIFIABLE_SCOPED" if m["candidate_matched_pairs"] else "HOLD_NO_RETAINED_GEOMETRIC_SCAFFOLD_CONTRAST"
if not errors and r["decision"] != expected: errors.append("decision")
if explicit != 0: errors.append("unexpected_explicit_scaffold_hit_in_frozen_corpus")
if len(m["candidate_matched_pairs"]) != 0: errors.append("unexpected_matched_pair_in_frozen_corpus")
out={"decision":"PASS_AUDIT" if not errors else "FAIL_AUDIT","errors":errors}
(ROOT / "AUDIT.json").write_text(json.dumps(out, indent=2, sort_keys=True)+"\n")
print(json.dumps(out, sort_keys=True))
if errors: raise SystemExit(2)
