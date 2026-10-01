"""Freeze the two-condition Mindustry receipt revalidation follow-up."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/mindustry-receipt-revalidation-followup-03"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    sources = [
        "benchmark_discovery/run_mindustry_receipt_revalidation_followup_live_v3.py",
        "benchmark_discovery/mindustry_single_tile_interactive_v3.py",
        "benchmark_discovery/mindustry_single_tile_socket_v3.py",
        "benchmark_discovery/mindustry_palette_candidate_responder_v3.txt",
        "benchmark_discovery/mindustry_conveyor_selection_oracle_v1.py",
        "benchmark_discovery/mindustry_palette_binding_v2.py",
        "benchmark_discovery/mindustry_palette_hover_receipt_v1.py",
        "benchmark_discovery/mindustry_palette_slots_v1.py",
        "benchmark_discovery/mindustry_single_tile_plan_v1.json",
        "live_control/mindustry_receipt_session_v2.py",
        "live_control/mindustry_receipt_session_v1.py",
        "live_control/receipt_target_admission_v1.py",
        "live_control/anchor_evidence_contract_v1.py",
        "live_control/anchor_evidence_responder_v1.txt",
        "live_control/anchor_evidence_contract_schema_v1.json",
        "live_control/bounded_visual_target_contract_v3.py",
        "live_control/bounded_visual_target_contract_schema_v3.json",
        "live_control/compact_hover_sheet_v2.py",
        "live_control/schema_preflight_gate_v1.py",
        "live_control/unix_json_deadline.py",
    ]
    root = HERE.parent
    prior = Path("results/mindustry-receipt-revalidation-01/positive/report.json")
    plan = {
        "name": "mindustry-receipt-revalidation-followup-03",
        "base_main": "339c4ac597c4945e19a1318c5086308a0e3b8ac0",
        "task": ("Place exactly one north-facing Conveyor in the empty tile "
                 "directly above the copper item source, then finish paused "
                 "with no pending build plans."),
        "condition_order": ["binding-unavailable", "surface-resized"],
        "expected": {
            "binding-unavailable": {
                "reason": "current_evidence_unavailable",
                "authority": "NO_TARGET_AUTHORITY",
                "point": None, "target_button_downs": 0,
                "binding_restored": True},
            "surface-resized": {
                "reason": "surface_size_changed",
                "authority": "NO_TARGET_AUTHORITY",
                "point": None, "target_button_downs": 0,
                "geometry_restored": True}},
        "prior_positive": str(prior).replace("\\", "/"),
        "prior_positive_sha256": sha(HERE / prior),
        "sources": {name: sha(root / name) for name in sources},
        "preflight_schemas": [
            {"name": "candidate",
             "schema": "live_control/bounded_visual_target_contract_schema_v3.json"},
            {"name": "palette-receipt",
             "schema": "live_control/anchor_evidence_contract_schema_v1.json"}],
        "model": "gpt-5.6-luna",
        "reasoning_effort": "low",
        "faults": {
            "binding-unavailable":
                "real mapped override-redirect InputOnly X11 focus yields pointer_binding null",
            "surface-resized":
                "remove EWMH maximization and change the real Mindustry surface width by -64"},
        "accounting": {
            "attempt_ledger_written_before_each_call": True,
            "missing_usage": "unavailable, never zero-filled",
            "measure": ["input_tokens", "cached_input_tokens",
                        "cache_write_input_tokens", "output_tokens",
                        "reasoning_output_tokens", "socket_exchanges",
                        "exact_frames", "decision_and_checked_latency"]},
        "policy": {
            "single_ordered_allocation": True,
            "condition_retries": 0,
            "subagents": 0,
            "formal_sources_immutable_after_preregistration": True,
            "preserve_failures": True},
        "scope": ("two fresh Linux/X11 fault-injected palette-refusal cases "
                  "following the retained positive block; not natural fault "
                  "frequency, broad reliability, causal speedup, token saving, "
                  "atomic OS admission or human tempo")}
    (OUT / "preregistration.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    (OUT / "empty-workspace").mkdir()
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
