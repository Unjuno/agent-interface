"""Freeze one no-GUI endpoint schema compatibility block."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "results/schema-preflight-01"
SOURCES = ["schema_preflight_responder_v1.txt", "schema_preflight_v1.py",
    "run_schema_preflight_block_v1.py", "preregister_schema_preflight_block_v1.py",
    "target_handle_model_runner_v2.py", "bounded_visual_target_contract_schema_v2.json",
    "bounded_visual_target_contract_schema_v3.json", "anchor_evidence_contract_schema_v1.json",
    "../benchmark_discovery/mindustry_world_target_contract_schema_v2.json",
    "../benchmark_discovery/mindustry_world_target_contract_schema_v3.json"]


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False); (OUT / "empty-workspace").mkdir()
    cases = [
        {"name": "01-reject-candidate-oneof", "schema": "live_control/bounded_visual_target_contract_schema_v2.json", "expected": "ENDPOINT_INCOMPATIBLE"},
        {"name": "02-reject-missing-property-type", "schema": "benchmark_discovery/mindustry_world_target_contract_schema_v2.json", "expected": "ENDPOINT_INCOMPATIBLE"},
        {"name": "03-accept-flat-candidate", "schema": "live_control/bounded_visual_target_contract_schema_v3.json", "expected": "ENDPOINT_COMPATIBLE"},
        {"name": "04-accept-anchor-receipt", "schema": "live_control/anchor_evidence_contract_schema_v1.json", "expected": "ENDPOINT_COMPATIBLE"},
        {"name": "05-accept-typed-world-receipt", "schema": "benchmark_discovery/mindustry_world_target_contract_schema_v3.json", "expected": "ENDPOINT_COMPATIBLE"}]
    plan = {"status": "preregistered_before_five_fresh_no_gui_preflights_and_one_cache_reuse",
        "study": "schema-preflight-01", "model": "gpt-5.6-luna", "reasoning_effort": "low",
        "cases": cases,
        "policy": ("locally validate JSON Schema; on cache miss submit a minimal no-image call through target_handle_model_runner_v2 "
                   "with the same output-schema conversion; cache by schema/runner/instructions/CLI hashes, CLI/Node versions, model, effort and request shape"),
        "positive_gate": ("retained oneOf and missing-type schemas are refused with no completed turn; three production schemas complete; "
                          "all fresh completed usage is reported; same-key reuse performs no call and reports no fresh usage"),
        "failure_policy": "retain the first finite block; no case or model retry",
        "sources": {name: sha((HERE / name).resolve()) for name in SOURCES},
        "scope": ("endpoint compatibility and cache behavior only; no GUI starts, no input authority, no semantic task-quality, "
                  "latency improvement, token saving, endpoint-version completeness or human-tempo claim")}
    (OUT / "preregistration.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__": main()
