"""Freeze one positive/no-match/unreadable Mindustry live block."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "results/mindustry-single-tile-matched-01"
REFERENCE = HERE / "results/mindustry-bend-v2-self-use-01/004.png"
PRIOR_FAILURE = HERE / "results/mindustry-single-tile-live-04/failure.json"
CACHE = HERE.parent / "live_control/results/schema-preflight-gate-01/cache"
SOURCES = [
    "preregister_mindustry_single_tile_matched_v1.py", "run_mindustry_single_tile_matched_v1.py",
    "mindustry_single_tile_plan_v1.json", "mindustry_single_tile_score_v1.py",
    "mindustry_single_tile_interactive_v1.py", "mindustry_single_tile_socket_v1.py",
    "mindustry_single_tile_mod_v1/mod.json", "mindustry_single_tile_mod_v1/scripts/main.js",
    "mindustry_palette_slots_v1.py", "mindustry_palette_hover_receipt_v1.py",
    "mindustry_conveyor_selection_oracle_v1.py", "mindustry_palette_candidate_responder_v3.txt",
    "mindustry_palette_binding_v2.py", "mindustry_world_candidate_responder_v4.txt",
    "mindustry_world_hover_receipt_v1.py", "mindustry_world_target_responder_v4.txt",
    "mindustry_world_target_contract_schema_v3.json", "mindustry_world_target_contract_v3.py",
    "compact_world_receipt_v2.py",
    "live_control/anchor_evidence_contract_schema_v1.json", "live_control/anchor_evidence_contract_v1.py",
    "live_control/anchor_evidence_responder_v1.txt", "live_control/bounded_visual_target_contract_schema_v3.json",
    "live_control/bounded_visual_target_contract_v3.py", "live_control/compact_hover_sheet_v2.py",
    "live_control/schema_preflight_gate_v1.py", "live_control/schema_preflight_v1.py",
    "live_control/schema_preflight_responder_v1.txt", "live_control/target_handle_model_runner_v2.py",
    "live_control/run_openttd_active_evidence_pair_v1.py", "live_control/cause_servo_session_v1.py",
    "live_control/executor_v8.py", "live_control/stopped_socket_v1.py",
]


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "empty-workspace").mkdir()
    task = json.loads((HERE / "mindustry_single_tile_plan_v1.json").read_text())["task"]
    cache_files = sorted(CACHE.glob("*.json")); assert len(cache_files) == 6
    plan = {
        "status": "preregistered_before_one_finite_three-condition-live-block",
        "study": "mindustry-single-tile-matched-01", "base_main": "356200194894c8ba4e80721d4864b6c433606658",
        "model": "gpt-5.6-luna", "reasoning_effort": "low", "condition_order": ["positive", "no-match", "unreadable"],
        "task": task, "model_calls_max": 11,
        "preflight_schemas": [
            {"name": "candidate", "schema": "live_control/bounded_visual_target_contract_schema_v3.json"},
            {"name": "palette-receipt", "schema": "live_control/anchor_evidence_contract_schema_v1.json"},
            {"name": "world-receipt", "schema": "benchmark_discovery/mindustry_world_target_contract_schema_v3.json"}],
        "conditions": {
            "positive": "normal direct-above target and normal verified world receipt; require independent task success",
            "no-match": "ask for a tile thirty tiles north with current viewport as the fixed allowed search area and no pan; require coordinate-free stop before world hover",
            "unreadable": "same direct-above target and live verified hover, then replace only presented receipt pixels with their deterministic mean; require coordinate-free receipt stop"},
        "common_policy": "fresh private GUI per condition; identical palette path, model, effort, fixture and scorer; no condition retry; schema gate before first GUI",
        "button_gate": "positive admits select-conveyor and place-one-conveyor; both negative conditions admit selection only and no placement",
        "accounting_gate": "record every model call, reported usage, socket exchange, terminal, button admission, feedback boundary and independent finish score",
        "failure_policy": "retain the first ordered block and every completed condition; no model, GUI, case or task retry",
        "reference_image": REFERENCE.relative_to(HERE).as_posix(), "reference_sha256": sha(REFERENCE),
        "prior_failure": PRIOR_FAILURE.relative_to(HERE).as_posix(), "prior_failure_sha256": sha(PRIOR_FAILURE),
        "sources": {name: sha(HERE.parent / name) if name.startswith("live_control/") else sha(HERE / name) for name in SOURCES},
        "preflight_cache": {path.name: sha(path) for path in cache_files},
        "scope": "one ordered injected three-condition Linux/X11 block; tests branch safety and accounting, not natural error rate, causal speedup, token saving, broad reliability or human tempo",
    }
    (OUT / "preregistration.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__": main()
