"""Freeze the remaining receipt-oneOf refusal and cached production gate."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "results/schema-preflight-gate-01"
SEED = HERE / "results/schema-preflight-01/cache"
SOURCES = [
    "schema_preflight_responder_v1.txt", "schema_preflight_v1.py",
    "schema_preflight_gate_v1.py", "run_schema_preflight_gate_v1.py",
    "preregister_schema_preflight_gate_v1.py", "target_handle_model_runner_v2.py",
    "bounded_visual_target_contract_schema_v3.json", "anchor_evidence_contract_schema_v1.json",
    "../benchmark_discovery/mindustry_world_target_contract_schema_v1.json",
    "../benchmark_discovery/mindustry_world_target_contract_schema_v3.json",
]


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "empty-workspace").mkdir()
    seed_files = sorted(SEED.glob("*.json"))
    assert len(seed_files) == 5
    plan = {
        "status": "preregistered_before_one_fresh_remaining-refusal_and_one_cached-positive-gate",
        "study": "schema-preflight-gate-01",
        "negative": [{"name": "world-receipt-oneof", "schema": "benchmark_discovery/mindustry_world_target_contract_schema_v1.json"}],
        "positive": [
            {"name": "flat-candidate", "schema": "live_control/bounded_visual_target_contract_schema_v3.json"},
            {"name": "anchor-receipt", "schema": "live_control/anchor_evidence_contract_schema_v1.json"},
            {"name": "typed-world-receipt", "schema": "benchmark_discovery/mindustry_world_target_contract_schema_v3.json"},
        ],
        "gate": "negative is refused before caller continuation; positive accepts three production schemas entirely from copied pinned cache",
        "failure_policy": "retain the first finite block; no endpoint retry",
        "sources": {name: sha((HERE / name).resolve()) for name in SOURCES},
        "seed_cache": {path.name: sha(path) for path in seed_files},
        "scope": "schema authority ordering only; no GUI, semantic task quality, speed, token saving or human-tempo claim",
    }
    (OUT / "preregistration.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__": main()
