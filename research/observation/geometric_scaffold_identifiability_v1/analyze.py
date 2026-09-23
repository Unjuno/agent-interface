import json
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "RESULT.json"
INV = ROOT / "FORMAL_INVOCATION.json"

if OUT.exists() or INV.exists():
    raise SystemExit("formal output already exists; rerun forbidden")

m = json.loads((ROOT / "manifest.json").read_text())
scaffold_terms = [
    "top-down", "topdown", "geometric scaffold", "depth map",
    "side view", "occupancy sketch", "spatial scaffold"
]
indexed_scaffold_hits = sum(m["indexed_counts"][k] for k in scaffold_terms)
delta_scaffold_hits = m["delta_scan"]["scaffold_term_hits"]
explicit_scaffold_hits = indexed_scaffold_hits + delta_scaffold_hits
matched = m["candidate_matched_pairs"]
errors = []
if m["indexed_to_main_added_files"] != m["delta_scan"]["files_scanned"]:
    errors.append("delta_coverage_mismatch")
if m["indexed_counts"]["model_image"] <= 0:
    errors.append("model_facing_reference_set_empty")
if m["indexed_counts"]["temporal-sheet"] <= 0:
    errors.append("known_temporal_representation_reference_set_empty")
if matched and explicit_scaffold_hits == 0:
    errors.append("matched_pair_without_explicit_scaffold_evidence")

if errors:
    decision = "FAIL_INTEGRITY"
elif matched:
    decision = "PASS_RETAINED_GEOMETRIC_SCAFFOLD_IDENTIFIABLE_SCOPED"
else:
    decision = "HOLD_NO_RETAINED_GEOMETRIC_SCAFFOLD_CONTRAST"

inv = {"formal_invocations": 1, "reruns": 0, "replacements": 0, "tuning": 0}
INV.write_text(json.dumps(inv, indent=2, sort_keys=True) + "\n")
result = {
    "task": m["task"],
    "issue": m["issue"],
    "decision": decision,
    "integrity_errors": errors,
    "explicit_scaffold_hits": explicit_scaffold_hits,
    "indexed_model_image_files": m["indexed_counts"]["model_image"],
    "indexed_temporal_sheet_files": m["indexed_counts"]["temporal-sheet"],
    "delta_files_scanned": m["delta_scan"]["files_scanned"],
    "matched_pair_count": len(matched),
    "invocation": inv,
    "scope": "retained explicit auditable metadata identifiability only; no efficacy claim"
}
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, sort_keys=True))
