"""Post-allocation diagnostic: test whether declared mutations are materialized."""
import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).parent
spec = importlib.util.spec_from_file_location("speech_candidate_diagnostic", ROOT / "candidate.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)
cases = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))["cases"]
by_id = {case["id"]: case for case in cases}

cases_to_mutate = {
    "quote_boundary_removed": ("quoted_third_party", lambda case: case.update(force="EXECUTE_REQUEST")),
    "negation_dropped": ("prepare_only", lambda case: case.update(force="EXECUTE_REQUEST", prohibitions=[])),
    "turn_author_swapped": ("later_authenticated_adoption", lambda case: case["turns"][-1].update(author="assistant")),
    "stale_quoted_instruction_reused": ("quoted_own_prior_for_analysis", lambda case: case.update(force="EXECUTE_REQUEST")),
    "paraphrase_elevated_to_source": ("capability_question", lambda case: case.update(force="EXECUTE_REQUEST")),
    "premise_truth_confused_with_force": ("direct", lambda case: case.update(world="unknown")),
}
diagnostics = {}
for name, (case_id, mutate) in cases_to_mutate.items():
    changed = copy.deepcopy(by_id[case_id])
    mutate(changed)
    result = candidate.decide(changed)
    diagnostics[name] = {"input_changed": changed != by_id[case_id], "transition": result["transition"], "errors": result["errors"]}
diagnostics["status"] = "DIAGNOSTIC_PASS" if all(v["input_changed"] for v in diagnostics.values() if isinstance(v, dict)) else "DIAGNOSTIC_FAIL"
(ROOT / "diagnostic_mutations.raw.json").write_text(json.dumps(diagnostics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(diagnostics, sort_keys=True))
raise SystemExit(0 if diagnostics["status"] == "DIAGNOSTIC_PASS" else 1)
