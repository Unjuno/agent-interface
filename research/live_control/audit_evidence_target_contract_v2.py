"""Audit the archived authority controls and endpoint schema call."""
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
OUT = HERE / "results/evidence-target-contract-v2-01"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    prereg, report = read(OUT / "preregistration.json"), read(OUT / "report.json")
    for name, digest in prereg["sources"].items(): assert sha(HERE / name) == digest, name
    assert report["passed"] is True
    local = report["local_controls"]
    assert local["positive_authority"] == "TARGET_REFERENCE_ONLY"
    assert local["negative_authorities"] == ["NO_TARGET_AUTHORITY"] * 4
    assert len(local["invalid_controls"]) == 4
    assert local["mindustry_operational_classes"] == {"positive": "TARGET_REFERENCE_ONLY", "no-match": "NO_TARGET_AUTHORITY", "unreadable": "NO_TARGET_AUTHORITY"}
    result = report["endpoint_preflight"]
    assert result["endpoint_status"] == "ENDPOINT_COMPATIBLE" and result["model_call_performed"] is True
    root = OUT / "endpoint-preflight/model-call"
    process = read(root / "process.json"); assert process["exit_code"] == 0 and process["mode"] == "handle"
    events = [json.loads(line) for line in (root / "events.jsonl").read_text().splitlines()]
    turns = [row for row in events if row.get("type") == "turn.completed"]
    messages = [row for row in events if row.get("type") == "item.completed" and row.get("item", {}).get("type") == "agent_message"]
    assert len(turns) == len(messages) == 1 and turns[0]["usage"] == result["usage"]
    Draft202012Validator(read(HERE / "evidence_target_contract_schema_v3.json")).validate(json.loads(messages[0]["item"]["text"]))
    assert not list(OUT.rglob("*.png")) and not list(OUT.rglob("*.ait"))
    audit = {"passed": True, "decision": "RETAIN_EVIDENCE_TARGET_CONTRACT_V2",
        "positive_authority": "TARGET_REFERENCE_ONLY", "negative_authority": "NO_TARGET_AUTHORITY",
        "diagnostics_preserved": True, "invalid_controls": 4, "endpoint_usage": result["usage"],
        "gui_artifacts": 0, "scope": prereg["scope"]}
    (OUT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__": main()
