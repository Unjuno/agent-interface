"""Freeze one fresh changed-geometry Mindustry placement allocation."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "results/mindustry-single-tile-live-01"
REFERENCE = HERE / "results/mindustry-bend-v2-self-use-01/004.png"
SOURCES = [
    "preregister_mindustry_single_tile_live_v1.py", "run_mindustry_single_tile_live_v1.py",
    "mindustry_single_tile_plan_v1.json", "mindustry_single_tile_score_v1.py",
    "mindustry_single_tile_interactive_v1.py", "mindustry_single_tile_socket_v1.py",
    "mindustry_single_tile_mod_v1/mod.json", "mindustry_single_tile_mod_v1/scripts/main.js",
    "mindustry_palette_slots_v1.py", "mindustry_palette_hover_receipt_v1.py",
    "mindustry_conveyor_selection_oracle_v1.py", "mindustry_palette_target_responder_v1.txt",
    "mindustry_world_candidate_responder_v1.txt", "mindustry_world_hover_receipt_v1.py",
    "mindustry_world_target_responder_v1.txt", "mindustry_world_target_contract_schema_v1.json",
    "mindustry_world_target_contract_v1.py", "compact_world_receipt_v1.py",
    "live_control/anchor_evidence_contract_schema_v1.json", "live_control/anchor_evidence_contract_v1.py",
    "live_control/anchor_evidence_responder_v1.txt", "live_control/uncertain_target_contract_schema_v1.json",
    "live_control/uncertain_target_contract_v1.py", "live_control/compact_hover_sheet_v2.py",
    "live_control/target_handle_model_runner_v2.py", "live_control/cause_servo_session_v1.py",
    "live_control/executor_v8.py", "live_control/stopped_socket_v1.py",
]


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False); (OUT / "empty-workspace").mkdir()
    task = json.loads((HERE / "mindustry_single_tile_plan_v1.json").read_text())["task"]
    plan = {
        "status": "preregistered_before_one_fresh_mindustry_live_allocation",
        "study": "mindustry-single-tile-live-01", "base_main": "cacf6dcd098b5233e839a14813af33654f1430b0",
        "model": "gpt-5.6-luna", "reasoning_effort": "low", "model_calls_max": 4,
        "task": task,
        "policy": ("separately bind the Conveyor palette through a persistent tooltip receipt; select it once; "
                   "ask for a world candidate on the fresh selected frame; acquire a click-free animated placement-preview "
                   "receipt; require a separate typed world decision before one placement click; resume, wait three seconds, "
                   "pause, then expose engine state only to the independent scorer"),
        "positive_gate": ("palette and world receipts bind; palette selection oracle passes; exactly two button-down admissions "
                          "belong to palette selection and world placement; exact target block/team/rotation, one-copper cost, "
                          "112-tile guard, source/core and paused idle completion all pass"),
        "abstention_gate": ("world needs_decision carries no coordinates, emits no placement button-down and remains a positive "
                            "task failure; it may establish safe branch behavior but not task completion"),
        "accounting_gate": ("all four actual model calls are listed in one ledger and aggregate input, cached input, cache-write "
                            "input, output and reasoning-output counts reconcile with raw records"),
        "failure_policy": "retain the first allocation and all available usage/runtime evidence; no model, GUI or task retry",
        "reference_image": REFERENCE.relative_to(HERE).as_posix(), "reference_sha256": sha(REFERENCE),
        "sources": {name: sha(HERE.parent / name) if name.startswith("live_control/") else sha(HERE / name)
                    for name in SOURCES},
        "scope": ("one fresh fixed-screen Linux/X11 Mindustry task at a target outside the earlier eight-tile route; integrates "
                  "separate palette/world evidence, animated semantic feedback, typed abstention and branch-complete call "
                  "accounting; no delivery, route planning, reliability rate, causal speed, token-saving or human-tempo claim"),
    }
    (OUT / "preregistration.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__": main()
