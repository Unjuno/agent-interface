"""Frozen, read-only T1 eligibility audit for Issue #6053 / PCAA v1."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
FREEZE = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))


def source(relative):
    path = REPO / relative
    raw = path.read_bytes()
    expected = FREEZE["inputs"][relative]["sha256"]
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected:
        raise RuntimeError(f"source hash mismatch: {relative}: {actual}")
    return raw.decode("utf-8")


frozen_sources = {relative: source(relative) for relative in FREEZE["inputs"]}
arena_text = frozen_sources["research/procedural_control_arena_v1/arena.py"]
engine_text = frozen_sources["research/procedural_control_arena_v1/engine.py"]
readme_text = frozen_sources["research/procedural_control_arena_v1/README.md"]
arena_tree, engine_tree = ast.parse(arena_text), ast.parse(engine_text)


def functions(tree):
    return {node.name: node for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def classes(tree):
    return {node.name: node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}


af, ef = functions(arena_tree), functions(engine_tree)
ec = classes(engine_tree)
arena_options = {
    node.args[0].value
    for node in ast.walk(arena_tree)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    and node.func.attr == "add_argument" and node.args
    and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)
}
session_init = next(node for node in ec["BenchmarkSession"].body
                    if isinstance(node, ast.FunctionDef) and node.name == "__init__")
session_parameters = [arg.arg for arg in session_init.args.args]
public_state = ef["public_state"]
public_keys = sorted({node.value for node in ast.walk(public_state)
                      if isinstance(node, ast.Dict)
                      for node in node.keys
                      if isinstance(node, ast.Constant) and isinstance(node.value, str)})
report_fn = ef["report"]
report_keys = sorted({node.value for node in ast.walk(report_fn)
                      if isinstance(node, ast.Dict)
                      for node in node.keys
                      if isinstance(node, ast.Constant) and isinstance(node.value, str)})
event_class = ec["SessionEvent"]
event_fields = [node.target.id for node in event_class.body
                if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)]
recovery_lines = [line.strip() for line in engine_text.splitlines()
                  if "recovery_interrupt" in line or "target_relocated" in line]

source_terms = (arena_text + "\n" + engine_text).lower()
perturbation_api_terms = ("perturbation", "counterfactual", "checkpoint arm",
                          "disturbance schedule", "matched replay")
paired_or_injection_surface = any(term in source_terms for term in perturbation_api_terms)
has_propagation_t2_control = "--pair" in arena_options or "--arm" in arena_options
isolation_gap_documented = (
    "source tree itself is **not a hardened secrecy boundary**" in
    readme_text
)

observations = {
    "arena_cli_options": sorted(arena_options),
    "session_init_parameters": session_parameters,
    "public_state_keys": public_keys,
    "report_fields_present": [key for key in
                               ("episode", "success", "stage_results", "events")
                               if key in report_keys],
    "event_fields": event_fields,
    "recovery_event_source_lines": recovery_lines,
    "t2_pair_or_arm_cli": has_propagation_t2_control,
    "perturbation_or_counterfactual_terms_in_arena_engine": paired_or_injection_surface,
    "source_isolation_gap_explicitly_documented": isolation_gap_documented,
}

has_stage_ledger = "stage_results" in report_keys and "stage_index" in event_fields
has_matched_perturbation = paired_or_injection_surface or has_propagation_t2_control
has_seed_isolation = not isolation_gap_documented
status = ("ELIGIBLE_FOR_T2_REVIEW" if has_stage_ledger and has_matched_perturbation
          and has_seed_isolation else "HOLD_NO_ELIGIBLE_CHAIN")
result = {
    "schema": "issue-6053-pcaa-stage-propagation-t1-result-v1",
    "status": status,
    "checks": {
        "stage_level_event_and_result_ledger": has_stage_ledger,
        "matched_exogenous_perturbation_or_counterfactual_path": has_matched_perturbation,
        "held_out_source_process_seed_isolation_established": has_seed_isolation,
        "effect_scoring_present_but_within_same_engine":
            "success" in report_keys and "failure_reason" in report_keys,
    },
    "observations": observations,
    "claim_limit": "A source-eligibility HOLD does not show that stagewise amplification occurs or that checkpoints help. No T2 run or controller-effect claim is made.",
}
(ROOT / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                    encoding="utf-8")
print(json.dumps(result, sort_keys=True))
