"""Freeze one finite Mindustry receipt-to-admission regression block."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/mindustry-receipt-revalidation-01"
REFERENCE = HERE / "results/mindustry-bend-v2-self-use-01/004.png"
PRIOR_FAILURE = HERE / "results/mindustry-single-tile-live-04/failure.json"
CACHE = HERE.parent / "live_control/results/schema-preflight-gate-01/cache"
SOURCES = [
    "preregister_mindustry_receipt_revalidation_live_v1.py",
    "run_mindustry_receipt_revalidation_live_v1.py",
    "mindustry_single_tile_plan_v1.json", "mindustry_single_tile_score_v1.py",
    "mindustry_single_tile_interactive_v2.py", "mindustry_single_tile_socket_v2.py",
    "mindustry_single_tile_mod_v1/mod.json", "mindustry_single_tile_mod_v1/scripts/main.js",
    "mindustry_palette_slots_v1.py", "mindustry_palette_hover_receipt_v1.py",
    "mindustry_conveyor_selection_oracle_v1.py", "mindustry_palette_candidate_responder_v3.txt",
    "mindustry_palette_binding_v2.py", "mindustry_world_candidate_responder_v4.txt",
    "mindustry_world_hover_receipt_v1.py", "mindustry_world_target_responder_v4.txt",
    "mindustry_world_target_contract_schema_v3.json", "mindustry_world_target_contract_v3.py",
    "compact_world_receipt_v2.py",
    "live_control/receipt_target_admission_v1.py", "live_control/mindustry_receipt_session_v1.py",
    "live_control/anchor_evidence_contract_schema_v1.json", "live_control/anchor_evidence_contract_v1.py",
    "live_control/anchor_evidence_responder_v1.txt", "live_control/bounded_visual_target_contract_schema_v3.json",
    "live_control/bounded_visual_target_contract_v3.py", "live_control/compact_hover_sheet_v2.py",
    "live_control/schema_preflight_gate_v1.py", "live_control/schema_preflight_v1.py",
    "live_control/schema_preflight_responder_v1.txt", "live_control/target_handle_model_runner_v2.py",
    "live_control/run_openttd_active_evidence_pair_v1.py", "live_control/cause_servo_session_v1.py",
    "live_control/executor_v8.py", "live_control/stopped_socket_v1.py",
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "empty-workspace").mkdir()
    task = json.loads((HERE / "mindustry_single_tile_plan_v1.json").read_text())["task"]
    cache_files = sorted(CACHE.glob("*.json"))
    assert len(cache_files) == 6
    plan = {
        "status": "preregistered_before_one_finite_four-condition-live-block",
        "study": "mindustry-receipt-revalidation-01",
        "base_main": "5b81adaa60238d6690d8a6450f06b307de945210",
        "model": "gpt-5.6-luna", "reasoning_effort": "low",
        "condition_order": ["positive", "changed-palette", "changed-world",
                            "focus-unavailable"],
        "task": task, "model_calls_max": 12,
        "preflight_schemas": [
            {"name": "candidate", "schema": "live_control/bounded_visual_target_contract_schema_v3.json"},
            {"name": "palette-receipt", "schema": "live_control/anchor_evidence_contract_schema_v1.json"},
            {"name": "world-receipt", "schema": "benchmark_discovery/mindustry_world_target_contract_schema_v3.json"}],
        "conditions": {
            "positive": "unchanged palette and world receipt dependencies; require two checked target buttons and independent task success",
            "changed-palette": "after palette receipt model return, move pointer away so tooltip/slot evidence changes; require typed refusal and zero target buttons",
            "changed-world": "after world receipt model return, move pointer away so the placement-preview mask changes; require world refusal and only the earlier checked palette button",
            "focus-unavailable": "after palette receipt model return, move real X11 focus to a private test surface; require current-evidence refusal, zero target buttons and explicit focus restoration",
        },
        "receipt_contract": {
            "palette": "fresh post-model snapshot, same focus/surface and surface size, exact tooltip and slot patches",
            "world": "fresh post-model snapshot, same focus/surface and surface size, exact selected-mode title/slot plus stable target-preview change mask",
            "authority": "only all dependencies together expose TARGET_REFERENCE_ONLY to the existing pointer adapter; every refusal exposes no point",
            "race_limit": "record receipt-check completion to input-owner button acknowledgement; no atomic-OS claim",
        },
        "button_gate": {"positive": ["select-conveyor", "place-one-conveyor"],
                        "changed-palette": [], "changed-world": ["select-conveyor"],
                        "focus-unavailable": []},
        "accounting_gate": "index every attempted model stage; preserve missing usage as unavailable; record all probes, socket exchanges, frames, releases, checked-to-button time and independent outcomes",
        "common_policy": "fresh private Linux/X11 GUI per condition; identical model, effort, fixture, prompts, receipt code and scorer; only declared post-model fault differs; schema gate before first GUI",
        "failure_policy": "retain the first ordered block and every completed condition; no model, GUI, case, task, reason or parameter retry; stop with RETAIN, HOLD or REJECT",
        "reference_image": REFERENCE.relative_to(HERE).as_posix(),
        "reference_sha256": sha(REFERENCE),
        "prior_failure": PRIOR_FAILURE.relative_to(HERE).as_posix(),
        "prior_failure_sha256": sha(PRIOR_FAILURE),
        "sources": {name: sha(HERE.parent / name) if name.startswith("live_control/")
                    else sha(HERE / name) for name in SOURCES},
        "preflight_cache": {path.name: sha(path) for path in cache_files},
        "scope": "one ordered fault-injected four-condition Linux/X11 block; engineering branch evidence, not natural stale-target rate, broad reliability, causal speedup, token saving or human tempo",
    }
    (OUT / "preregistration.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
