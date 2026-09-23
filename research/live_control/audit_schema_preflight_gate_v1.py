"""Audit the remaining refusal and cached production schema gate."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "results/schema-preflight-gate-01"
SEED = HERE / "results/schema-preflight-01/cache"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan, report = read(OUT / "preregistration.json"), read(OUT / "report.json")
    for name, digest in plan["sources"].items(): assert sha((HERE / name).resolve()) == digest, name
    for name, digest in plan["seed_cache"].items(): assert sha(SEED / name) == digest, name
    assert report["passed"] is True and report["decision"] == "RETAIN_SCHEMA_AUTHORITY_GATE_V1"
    negative = report["negative_gate"]
    assert negative["accepted"] is False and negative["model_calls"] == 1
    result = negative["results"][0]["result"]
    assert result["endpoint_status"] == "ENDPOINT_INCOMPATIBLE" and result["usage"] is None
    assert "'oneOf' is not permitted" in json.dumps(result["endpoint_error"])
    events = [json.loads(line) for line in (OUT / "negative-gate/world-receipt-oneof/model-call/events.jsonl").read_text().splitlines()]
    assert not [row for row in events if row.get("type") == "turn.completed"]
    process = read(OUT / "negative-gate/world-receipt-oneof/model-call/process.json")
    assert process["exit_code"] == 1 and process["mode"] == "handle"
    positive = report["positive_gate"]
    assert positive["accepted"] is True and positive["model_calls"] == 0 and positive["fresh_usage_records"] == 0
    assert len(positive["results"]) == 3
    for row in positive["results"]:
        assert row["result"]["cache_hit"] is True and row["result"]["usage"] is None
        assert not (OUT / "positive-gate" / row["name"] / "model-call").exists()
    assert len(list((OUT / "cache").glob("*.json"))) == 6
    assert not list(OUT.rglob("*.png")) and not list(OUT.rglob("*.ait"))
    audit = {
        "passed": True,
        "decision": report["decision"],
        "remaining_oneof_refused": True,
        "negative_model_calls": 1,
        "negative_completed_turns": 0,
        "negative_usage": None,
        "positive_schema_count": 3,
        "positive_model_calls": 0,
        "gui_artifacts": 0,
        "authority": "caller may continue only after accepted=true",
    }
    (OUT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__": main()
