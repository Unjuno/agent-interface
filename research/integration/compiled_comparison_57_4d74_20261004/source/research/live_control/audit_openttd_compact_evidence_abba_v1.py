"""Reconstruct the compact-evidence ABBA result from frozen artifacts."""
import hashlib
import json
import tempfile
from pathlib import Path

from PIL import Image

from evidence_target_contract_v1 import validate
from openttd_compact_hover_sheet_v1 import build


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-compact-evidence-abba-01"
PRIOR = HERE / "results/openttd-active-evidence-pair-02/2-stable-seed991004"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pixel_sha(path):
    with Image.open(path) as opened:
        return hashlib.sha256(opened.convert("RGB").tobytes()).hexdigest()


def main():
    plan, report = read(OUT / "preregistration.json"), read(OUT / "report.json")
    for name, digest in plan["sources"].items():
        assert sha(HERE / name) == digest, name
    for name, digest in plan["fixed_evidence"].items():
        assert sha(HERE / name) == digest, name
    stable = read(PRIOR / "result.json")
    readiness = stable["hover_readiness"]
    with tempfile.TemporaryDirectory() as temporary:
        rebuilt = Path(temporary) / "compact.png"
        manifest = build(readiness, PRIOR / "runtime", rebuilt)
        # PNG encoders may emit different container bytes across Pillow builds.
        # The presented RGB pixels are the portable evidence invariant.
        assert pixel_sha(rebuilt) == pixel_sha(OUT / "compact-presentation.png")
        assert manifest["pixels_sha256"] == read(OUT / "compact-manifest.json")["pixels_sha256"]
    assert sha(OUT / "full-presentation.png") == sha(PRIOR / "hover-presentation.png")
    with Image.open(OUT / "full-presentation.png") as image:
        full_size = list(image.size)
    with Image.open(OUT / "compact-presentation.png") as image:
        compact_size = list(image.size)

    audited = []
    for row in report["results"]:
        name = row["name"]
        result = read(OUT / f"{name}-result.json")
        plan_row = read(OUT / name / "plan.json")
        process = read(OUT / name / "process.json")
        events = [json.loads(line) for line in (OUT / name / "events.jsonl").read_text(
            encoding="utf-8").splitlines()]
        messages = [event for event in events if event.get("type") == "item.completed"
                    and event.get("item", {}).get("type") == "agent_message"]
        turns = [event for event in events if event.get("type") == "turn.completed"]
        assert len(messages) == len(turns) == 1
        assert json.loads(messages[0]["item"]["text"]) == result["typed"]
        assert turns[0]["usage"] == result["usage"] == row["model"]["usage"]
        assert plan_row["requested_model"] == "gpt-5.6-luna"
        assert plan_row["requested_effort"] == "low"
        assert plan_row["instructions_sha256"] == sha(
            HERE / "evidence_target_reference_responder_v2.txt")
        assert plan_row["schema_sha256"] == sha(HERE / "evidence_target_contract_schema_v2.json")
        assert plan_row["image_sha256"] == row["image_sha256"]
        assert process["exit_code"] == 0
        assert process["observed_model_identity"] is None and process["cost"] is None
        binding = validate(result["typed"], readiness)
        assert binding == row["binding"]
        assert row["correct"] == (binding["point"] == [485, 51]
                                   and binding["receipt"]["receipt_index"] == 5)
        audited.append({"name": name, "condition": row["condition"],
                        "input_tokens": result["usage"]["input_tokens"],
                        "correct": row["correct"]})

    full = [row["input_tokens"] for row in audited if row["condition"] == "full"]
    compact = [row["input_tokens"] for row in audited if row["condition"] == "compact"]
    full_mean, compact_mean = sum(full) / 2, sum(compact) / 2
    assert report["mean_reported_input_tokens"] == {"full": full_mean, "compact": compact_mean}
    assert report["promotion_gate"]["passed"] is True
    result = {
        "audit_passed": True, "preregistered_sources_match": True,
        "fixed_evidence_match": True, "compact_rebuild_exact": True,
        "execution_order": [row["name"] for row in audited],
        "image_dimensions": {"full": full_size, "compact": compact_size},
        "calls": audited, "mean_reported_input_tokens": report["mean_reported_input_tokens"],
        "mean_reduction_tokens": report["mean_reduction_tokens"],
        "mean_reduction_fraction": report["mean_reduction_fraction"],
        "same_single_model": "gpt-5.6-luna low", "subagents": 0,
        "observed_model_identity": None, "reported_cost": None,
        "decision": report["decision"], "limits": report["scope"],
    }
    (OUT / "audit.json").write_text(json.dumps(result, indent=2) + "\n",
                                    encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
