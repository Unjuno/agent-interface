"""Audit fixed correct/wrong single-anchor model decisions."""
import hashlib
import json
import tempfile
from pathlib import Path

from PIL import Image

from anchor_evidence_contract_v1 import validate
from openttd_compact_hover_sheet_v1 import build
import preregister_openttd_anchor_evidence_abba_v1 as preregister


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-anchor-evidence-abba-01"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def pixel_sha(path):
    with Image.open(path) as image: return hashlib.sha256(image.convert("RGB").tobytes()).hexdigest()


def main():
    plan, report = read(OUT / "preregistration.json"), read(OUT / "report.json")
    for name, digest in plan["sources"].items(): assert sha(HERE / name) == digest, name
    for condition, evidence in plan["fixed_evidence"].items():
        for key in ("result", "events", "dwell_image"):
            assert sha(HERE / evidence[key]) == evidence[f"{key}_sha256"]
        readiness = read(OUT / f"{condition}-readiness.json")
        source_root = (HERE / evidence["events"]).parent
        with tempfile.TemporaryDirectory() as temporary:
            rebuilt = Path(temporary) / "rebuilt.png"
            manifest = build(readiness, source_root, rebuilt)
            assert pixel_sha(rebuilt) == evidence["presentation_pixels_sha256"]
            assert manifest["pixels_sha256"] == evidence["presentation_pixels_sha256"]
    calls = []
    for row in report["results"]:
        name = row["name"]; condition = row["condition"]
        result = read(OUT / f"{name}-result.json")
        model_plan = read(OUT / name / "plan.json"); process = read(OUT / name / "process.json")
        events = [json.loads(line) for line in (OUT / name / "events.jsonl").read_text(
            encoding="utf-8").splitlines()]
        messages = [event for event in events if event.get("type") == "item.completed"
                    and event.get("item", {}).get("type") == "agent_message"]
        turns = [event for event in events if event.get("type") == "turn.completed"]
        assert len(messages) == len(turns) == 1
        assert json.loads(messages[0]["item"]["text"]) == result["typed"]
        assert turns[0]["usage"] == result["usage"] == row["model"]["usage"]
        assert model_plan["requested_model"] == "gpt-5.6-luna"
        assert model_plan["requested_effort"] == "low"
        assert model_plan["instructions_sha256"] == sha(HERE / "anchor_evidence_responder_v1.txt")
        assert model_plan["schema_sha256"] == sha(HERE / "anchor_evidence_contract_schema_v1.json")
        assert model_plan["image_sha256"] == sha(OUT / f"{condition}.png")
        assert process["exit_code"] == 0
        assert process["observed_model_identity"] is None and process["cost"] is None
        decision = validate(result["typed"], read(OUT / f"{condition}-readiness.json"))
        assert decision == row["decision"]
        assert result["typed"]["op"] == row["expected_op"]
        calls.append({"name": name, "condition": condition, "op": result["typed"]["op"],
                      "point": result["typed"]["point"],
                      "input_tokens": result["usage"]["input_tokens"]})
    assert report["promotion_gate"]["passed"] is True
    audit = {"audit_passed": True, "preregistered_sources_match": True,
             "compact_presentations_rebuilt": 2, "calls": calls,
             "correct_anchor_accepts": 2, "wrong_anchor_expands": 2,
             "same_single_model": "gpt-5.6-luna low", "subagents": 0,
             "observed_model_identity": None, "reported_cost": None,
             "decision": report["decision"], "limits": report["scope"]}
    (OUT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n",
                                    encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__": main()
