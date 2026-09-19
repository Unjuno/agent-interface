"""Freeze one integrated real-threat v38 run before the first model call."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PLAN = HERE / "map01_v38_integrated_live_v1_prereg.json"
OUTPUT = REPO / "results-local/doom/map01-v38-integrated-threat-live-01"


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if PLAN.exists() or OUTPUT.exists(): raise FileExistsError("frozen plan/output already exists")
    sources = [
        "research/doom/map01_overlap_controller_v38.py",
        "research/doom/session_map01_v12.py",
        "research/doom/doom_typed_release_backend_v1.py",
        "research/doom/doom_typed_coast_backend_v1.py",
        "research/doom/map01_cover_policy_schema_v6.json",
        "research/doom/map01_motor_responder_v10.txt",
        "research/doom/doom_typed_observation_v1.py",
        "research/doom/doom_hud_signal_v3.py",
        "research/doom/doom_action_validity_contract_v1.py",
        "research/doom/doom_action_snapshot_v1.py",
        "research/live_control/running_action_guard_v3.py",
        "research/live_control/running_action_guard_v2.py",
        "research/live_control/executor_v12.py",
        "research/live_control/executor_v3.py",
        "research/live_control/input_owner_v10.py",
        "research/live_control/lease.py",
        "research/live_control/coast_backend_v1.py",
        "research/live_control/final_action_admission_v2.py",
        "research/live_control/action_validity_admission_v1.py",
        "research/live_control/observable_signal_guard_v2.py",
        "research/live_control/persistent_planner_adapter_v2.py",
        "research/live_control/codex_app_server_client_v2.py",
        "research/doom/fixtures/map01-threat-contact-v2/fixture.json",
        "research/doom/fixtures/map01-threat-contact-v2/save.png",
        "research/doom/fixtures/map01-threat-contact-v2/source.png",
        "research/doom/test_map01_overlap_controller_v38.py",
        "research/doom/audit_map01_v38_integrated_live_v1.py",
        "research/doom/preregister_map01_v38_integrated_live_v1.py",
    ]
    command = ["env", "PYTHONPATH=_vizdoom:research/doom:research/live_control",
               "python3", "research/doom/map01_overlap_controller_v38.py",
               "--out", "results-local/doom/map01-v38-integrated-threat-live-01",
               "--iterations", "6", "--seed", "990619", "--session-span", "6",
               "--model", "gpt-5.6-luna", "--effort", "low",
               "--load-fixture-manifest", "research/doom/fixtures/map01-threat-contact-v2/fixture.json"]
    plan = {"schema": "map01-v38-integrated-live-prereg-v1",
            "status": "FROZEN_BEFORE_FIRST_V38_MODEL_CALL",
            "allocation_id": "map01-v38-integrated-threat-live-01",
            "output": "results-local/doom/map01-v38-integrated-threat-live-01",
            "requested_model": "gpt-5.6-luna", "requested_effort": "low",
            "iterations_max": 6, "seed": 990619, "session_span": 6,
            "fixture": "map01-threat-contact-v2", "mode": "continuously advancing MAP01",
            "command": command, "retry_limit": 0, "model_boundary_limit": 6,
            "schema_v6_preflight_report_sha256": sha(HERE / "results/map01-schema-v6-preflight-01/report.json"),
            "v32_retained_report_sha256": sha(HERE / "results/map01-final-admission-v32-live-01/report.json"),
            "source_sha256": {name: sha(REPO / name) for name in sources},
            "stop_rule": "first outcome at six decisions, death, terminal, runtime failure or independent episode end; no retry or in-place repair",
            "formal_mechanics": "every model decision has typed final receipt; rejected decisions admit no plan input; all accepted programs match empty terminals; exact typed/full frames reconcile; admitted primary/fallback programs bind semantic commands, submitted steps, SHA and intent token; active invalidation matches early physical release and later terminal",
            "exposure_rule": "integrated running path is exposed only if one active model-authored schema-v6 answer passes fresh immediate validity and at least one primary program is accepted with a running-action-v3 receipt",
            "dynamic_rule": "classify active typed health/ammo revocation, early physical release and terminal closure separately; no natural revocation remains unexposed",
            "performance_rule": "report correctness, accepted/rejected plans, cover renewals, model wait, first exact/useful feedback where measured, observation/tool/image/token counts, release and score; do not infer causal v32 speed or human tempo from one nondeterministic episode",
            "failure_rule": "retain raw first partial output and exact error; do not rerun this ID; version any repair",
            "scope": "one finite same-fixture real-time integrated v38 planner episode; no MAP01-clear, cross-domain, reliability, causal speed/token or human-tempo claim"}
    PLAN.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"frozen": plan["allocation_id"], "sources": len(sources),
                      "model_boundary_limit": 6}, indent=2))


if __name__ == "__main__": main()
