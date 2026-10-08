"""Freeze the size-aware Mindustry anchor-first selection allocation."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/mindustry-anchor-first-select-live-02"
REFERENCE = HERE / "results/mindustry-bend-v2-self-use-01/004.png"
PRIOR_FAILURE = HERE / "results/mindustry-anchor-first-select-live-01/failure.json"
SOURCES = [
    "preregister_mindustry_anchor_first_select_live_v2.py",
    "run_mindustry_anchor_first_select_live_v2.py",
    "mindustry_palette_slots_v1.py",
    "mindustry_palette_hover_receipt_v1.py",
    "mindustry_conveyor_selection_oracle_v1.py",
    "mindustry_palette_target_responder_v1.txt",
    "mindustry_socket_v2.py",
    "mindustry_bend_interactive_v2.py",
    "live_control/anchor_evidence_contract_schema_v1.json",
    "live_control/anchor_evidence_contract_v1.py",
    "live_control/anchor_evidence_responder_v1.txt",
    "live_control/uncertain_target_contract_schema_v1.json",
    "live_control/uncertain_target_contract_v1.py",
    "live_control/target_handle_model_runner_v2.py",
    "live_control/compact_hover_sheet_v2.py",
]


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "empty-workspace").mkdir()
    plan = {
        "status": "preregistered_before_one_fresh_mindustry_live_allocation",
        "study": "mindustry-anchor-first-select-live-02",
        "model": "gpt-5.6-luna", "reasoning_effort": "low",
        "task": "Select Conveyor in the visible Mindustry build palette without placing any block.",
        "policy": ("ask the model for a coarse palette point; normalize it to the fresh screen-derived "
                   "4x4 palette; acquire one click-free pixel-quiet persistent hover receipt; require "
                   "the same model to bind Conveyor to that receipt before one ordinary click"),
        "positive_gate": ("one verified receipt is accepted; hover-only visual oracle remains false; "
                          "only the final selection emits button_down; release and the independent "
                          "fixed-fixture title-plus-selection-border RGB oracle pass"),
        "failure_policy": ("retain the first runtime allocation; if the anchor requests expansion, "
                           "stop without target click; no model, runtime or task retry"),
        "reference_image": REFERENCE.relative_to(HERE).as_posix(),
        "reference_sha256": sha(REFERENCE),
        "prior_failure": PRIOR_FAILURE.relative_to(HERE).as_posix(),
        "prior_failure_sha256": sha(PRIOR_FAILURE),
        "sources": {name: sha(HERE.parent / name) if name.startswith("live_control/")
                    else sha(HERE / name) for name in SOURCES},
        "scope": ("one fixed-layout paused Mindustry palette selection task after a retained "
                  "fixed-row presentation failure, using requested Luna-low "
                  "and no subagents; tests cross-domain active semantic evidence and selection only, "
                  "not placement, expansion recovery, window translation, broad GUI reliability, "
                  "causal speed or human-tempo operation"),
    }
    (OUT / "preregistration.json").write_text(json.dumps(plan, indent=2) + "\n",
                                               encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
