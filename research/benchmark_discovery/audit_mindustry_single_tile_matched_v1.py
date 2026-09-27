"""Audit the retained positive/no-match/unreadable Mindustry block."""
import hashlib
import json
import sys
import tempfile
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
LIVE = HERE.parent / "live_control"
sys.path.insert(0, str(LIVE))

from audit_local_visual_barrier_v1 import Decoder, Frame
from compact_world_receipt_v2 import build as build_world
from mindustry_single_tile_score_v1 import score

OUT = HERE / "results/mindustry-single-tile-matched-01"
CACHE = LIVE / "results/schema-preflight-gate-01/cache"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def pixel_sha(path):
    with Image.open(path) as image: return hashlib.sha256(image.convert("RGB").tobytes()).hexdigest()
def source(name): return HERE.parent / name if name.startswith("live_control/") else HERE / name


def audit_model(root, stage):
    result = read(root / f"{stage}-result.json")
    plan = read(root / stage / "plan.json")
    process = read(root / stage / "process.json")
    events = [json.loads(line) for line in (root / stage / "events.jsonl").read_text().splitlines()]
    turns = [row for row in events if row.get("type") == "turn.completed"]
    messages = [row for row in events if row.get("type") == "item.completed" and row.get("item", {}).get("type") == "agent_message"]
    assert len(turns) == len(messages) == 1 and turns[0]["usage"] == result["usage"]
    assert json.loads(messages[0]["item"]["text"]) == result["typed"]
    assert process["exit_code"] == 0 and plan["requested_model"] == "gpt-5.6-luna" and plan["requested_effort"] == "low"
    return result


def audit_case(condition, expected_calls, expected_buttons):
    root = OUT / condition
    report = read(root / "report.json")
    result = report["result"]
    ledger = read(root / "model-usage-ledger.json")
    assert ledger == result["model_usage_ledger"] and len(ledger) == expected_calls
    models = {row["stage"]: audit_model(root, row["stage"]) for row in ledger}
    fields = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens", "output_tokens", "reasoning_output_tokens")
    totals = {field: sum(row["usage"].get(field, 0) for row in ledger) for field in fields}
    assert totals == result["model_usage_total"]
    events = [json.loads(line) for line in (root / "runtime/events.jsonl").read_text().splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]
    decoder = Decoder("live-control")
    for index, observation in enumerate(observations, 1):
        frame = decoder.accept((root / "runtime" / f"{index:03d}.ait").read_bytes())
        with Image.open(root / "runtime" / Path(observation["image"]).name) as opened:
            image = opened.convert("RGB")
        assert frame == Frame(image.width, image.height, image.mode, image.tobytes())
    buttons = [row["id"] for row in events if row.get("event") == "pointer_admission" and row.get("operation") == "button_down"]
    assert buttons == expected_buttons
    terminals = [row for row in events if row.get("event") == "terminal"]
    assert all(row["status"] == "completed" and row["release"]["verified"] is True for row in terminals)
    task = read(HERE / "mindustry_single_tile_plan_v1.json")
    evaluation = score(read(root / "runtime/before.json"), read(root / "runtime/after.json"), task)
    assert evaluation == read(root / "runtime/evaluation.json")
    assert evaluation == {key: value for key, value in result["driver_evaluation"].items() if key not in ("event", "emitted_ns")}
    assert read(root / "runtime/cleanup.json") == {"all_owned_processes_exited": True, "save_unchanged": True}
    if condition in ("positive", "unreadable"):
        mode = "normal" if condition == "positive" else "unreadable"
        with tempfile.TemporaryDirectory() as temporary:
            rebuilt = Path(temporary) / "world.png"
            manifest = build_world(result["world_readiness"], root / "runtime", rebuilt, mode)
            assert pixel_sha(rebuilt) == pixel_sha(root / "world-receipt.png")
            assert manifest == result["world_manifest"]
    else:
        assert result["world_readiness"] is None and result["world_receipt_model"] is None
        assert not (root / "world-receipt.png").exists()
        assert not [row for row in events if row.get("id") == "hover-world"]
    return {"decision": report["decision"], "gate_passed": report["promotion_gate"]["passed"],
        "world_candidate": result["world_candidate"], "world_decision": result["world_decision"],
        "button_down_ids": buttons, "model_calls": len(ledger), "usage": totals,
        "socket_exchanges": result["socket_exchanges"], "exact_frames": len(observations),
        "terminals": len(terminals), "timing_ms": result["timing_ms"], "evaluation": evaluation}


def main():
    prereg, report = read(OUT / "preregistration.json"), read(OUT / "report.json")
    for name, digest in prereg["sources"].items(): assert sha(source(name)) == digest, name
    for name, digest in prereg["preflight_cache"].items(): assert sha(CACHE / name) == digest, name
    preflight = report["preflight"]
    assert preflight["accepted"] is True and preflight["model_calls"] == 0
    assert all(row["result"]["cache_hit"] is True and row["result"]["usage"] is None for row in preflight["results"])
    cases = {
        "positive": audit_case("positive", 4, ["select-conveyor", "place-one-conveyor"]),
        "no-match": audit_case("no-match", 3, ["select-conveyor"]),
        "unreadable": audit_case("unreadable", 4, ["select-conveyor"]),
    }
    assert cases["positive"]["evaluation"]["contract_satisfied"] is True
    assert cases["positive"]["world_decision"]["status"] == "EVIDENCE_BOUND"
    assert cases["no-match"]["world_candidate"] == {"status": "NEEDS_DECISION", "reason": "ambiguous", "points": []}
    assert cases["no-match"]["world_decision"] == {"status": "NEEDS_DECISION", "reason": "ambiguous", "point": None}
    assert cases["no-match"]["gate_passed"] is False
    assert cases["unreadable"]["world_decision"] == {"status": "NEEDS_DECISION", "reason": "unreadable_evidence", "point": None}
    assert cases["unreadable"]["gate_passed"] is True
    assert cases["no-match"]["evaluation"]["contract_satisfied"] is False
    assert cases["unreadable"]["evaluation"]["contract_satisfied"] is False
    assert report["passed"] is False
    audit = {"passed": True, "formal_block_passed": False,
        "decision": "RETAIN_PARTIAL_BRANCH_EVIDENCE",
        "preflight_model_calls": 0, "cases": cases,
        "failed_preregistered_check": "no-match returned ambiguous rather than no_candidate/no_match",
        "safety_result": "both negative conditions carry no coordinates past their stop and admit no placement button",
        "scope": prereg["scope"]}
    (OUT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__": main()
