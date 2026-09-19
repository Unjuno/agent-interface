"""Audit endpoint refusals, accepted outputs and compatibility-cache reuse."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
OUT = HERE / "results/schema-preflight-01"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def key(identity):
    return hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main():
    prereg, report = read(OUT / "preregistration.json"), read(OUT / "report.json")
    for name, digest in prereg["sources"].items(): assert sha((HERE / name).resolve()) == digest, name
    assert report["passed"] is True and report["decision"] == "RETAIN_SCHEMA_PREFLIGHT_V1"
    fresh = report["results"][:5]; reuse = report["results"][5]["result"]
    assert [row["name"] for row in fresh] == [case["name"] for case in prereg["cases"]]
    cache_files = list((OUT / "cache").glob("*.json")); assert len(cache_files) == 5
    usage = []; errors = []
    for row, case in zip(fresh, prereg["cases"]):
        result = row["result"]; root = OUT / row["name"]; identity = result["identity"]
        assert result["compatibility_key"] == key(identity)
        assert identity["schema_sha256"] == sha((HERE.parent / case["schema"]).resolve())
        assert identity["runner_sha256"] == sha(HERE / "target_handle_model_runner_v2.py")
        assert identity["instructions_sha256"] == sha(HERE / "schema_preflight_responder_v1.txt")
        cached = read(OUT / "cache" / f'{result["compatibility_key"]}.json')
        assert cached["endpoint_status"] == result["endpoint_status"] and cached["usage"] == result["usage"]
        plan = read(root / "model-call/plan.json"); process = read(root / "model-call/process.json")
        assert plan["mode"] == process["mode"] == "handle" and plan["image_sha256"] is None
        assert "-i" not in plan["args"] and plan["schema_sha256"] == identity["schema_sha256"]
        events = [json.loads(line) for line in (root / "model-call/events.jsonl").read_text().splitlines()]
        turns = [event for event in events if event.get("type") == "turn.completed"]
        messages = [event for event in events if event.get("type") == "item.completed" and event.get("item", {}).get("type") == "agent_message"]
        if result["endpoint_status"] == "ENDPOINT_INCOMPATIBLE":
            assert process["exit_code"] == 1 and not turns and not messages and result["usage"] is None
            errors.append(json.dumps(result["endpoint_error"]))
        else:
            assert result["endpoint_status"] == "ENDPOINT_COMPATIBLE" and process["exit_code"] == 0
            assert len(turns) == len(messages) == 1 and turns[0]["usage"] == result["usage"]
            output = json.loads(messages[0]["item"]["text"])
            schema = read(HERE.parent / case["schema"]); Draft202012Validator(schema).validate(output)
            usage.append(result["usage"])
    assert "'oneOf' is not permitted" in errors[0]
    assert "schema must have a 'type' key" in errors[1]
    fields = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens", "output_tokens", "reasoning_output_tokens")
    totals = {field: sum(value.get(field, 0) for value in usage) for field in fields}
    assert totals == report["usage_total_fresh_compatible_calls"]
    assert reuse["cache_hit"] is True and reuse["model_call_performed"] is False and reuse["usage"] is None
    assert not (OUT / "06-cache-reuse/model-call").exists()
    assert reuse["compatibility_key"] == fresh[2]["result"]["compatibility_key"]
    assert reuse["cached_first_observation"]["usage"] == fresh[2]["result"]["usage"]
    base = fresh[2]["result"]["identity"]
    for field, value in (("schema_sha256", "0" * 64), ("cli_version", base["cli_version"] + "-changed"),
                         ("requested_model", "different-model")):
        changed = dict(base); changed[field] = value; assert key(changed) != key(base)
    assert not list(OUT.rglob("*.ait")) and not list(OUT.rglob("*.png"))
    audit = {"passed": True, "decision": report["decision"], "fresh_endpoint_requests": 5,
        "completed_model_calls": 3, "endpoint_refusals": 2, "usage_total": totals,
        "cache_files": len(cache_files), "cache_reuse_model_call": False,
        "request_mode": "handle", "image_inputs": 0, "gui_artifacts": 0,
        "identity": base, "limits": "recorded CLI/model compatibility; endpoint revision is not independently identified"}
    (OUT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__": main()
