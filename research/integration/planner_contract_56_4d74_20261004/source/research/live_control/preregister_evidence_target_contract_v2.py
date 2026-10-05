"""Freeze local authority controls plus one endpoint compatibility call."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "results/evidence-target-contract-v2-01"
SOURCES = ["evidence_target_contract_schema_v3.json", "evidence_target_contract_v2.py",
    "evidence_target_reference_responder_v3.txt", "test_evidence_target_contract_v2.py",
    "preregister_evidence_target_contract_v2.py", "run_evidence_target_contract_v2.py",
    "schema_preflight_v1.py", "schema_preflight_responder_v1.txt", "target_handle_model_runner_v2.py"]


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False); (OUT / "empty-workspace").mkdir()
    plan = {"status": "preregistered_before_one_fresh_endpoint_preflight",
        "study": "evidence-target-contract-v2-01", "model": "gpt-5.6-luna", "reasoning_effort": "low",
        "gate": "local OpenTTD/Mindustry authority controls pass and the new flat schema is endpoint compatible",
        "failure_policy": "retain first endpoint result; no retry",
        "sources": {name: sha(HERE / name) for name in SOURCES},
        "scope": "contract compatibility and archived authority semantics only; no fresh GUI, model selection quality, speed, token saving or human-tempo claim"}
    (OUT / "preregistration.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__": main()
