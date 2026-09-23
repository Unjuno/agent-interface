"""Freeze a correct/wrong single-anchor evidence ABBA before model calls."""
import hashlib
import json
from pathlib import Path

from openttd_compact_hover_sheet_v1 import build


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-anchor-evidence-abba-01"
SOURCES = [
    "preregister_openttd_anchor_evidence_abba_v1.py",
    "run_openttd_anchor_evidence_abba_v1.py",
    "anchor_evidence_contract_schema_v1.json",
    "anchor_evidence_contract_v1.py",
    "anchor_evidence_responder_v1.txt",
    "openttd_compact_hover_sheet_v1.py",
    "run_openttd_active_evidence_pair_v1.py",
    "target_handle_model_runner_v2.py",
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def one(readiness, receipt_index):
    receipt = dict(readiness["receipts"][receipt_index - 1])
    receipt["receipt_index"] = 1
    return {"status": "READY", "binding": readiness["binding"],
            "receipts": [receipt], "batches": 1,
            "authority": "single verified observation receipt only; grants no input authority"}


def prepare(name, root, receipt_index):
    result_path = root / "result.json"
    events_path = root / "runtime/events.jsonl"
    result = read(result_path)
    readiness = one(result["hover_readiness"], receipt_index)
    receipt = readiness["receipts"][0]
    observation = next(json.loads(line) for line in events_path.read_text(
        encoding="utf-8").splitlines() if json.loads(line).get("event") == "observation"
        and json.loads(line).get("sequence") == receipt["dwell_sequence"])
    image_path = root / "runtime" / Path(observation["image"]).name
    (OUT / f"{name}-readiness.json").write_text(
        json.dumps(readiness, indent=2) + "\n", encoding="utf-8", newline="\n")
    manifest = build(readiness, root / "runtime", OUT / f"{name}.png")
    return {"result": str(result_path.relative_to(HERE)),
            "events": str(events_path.relative_to(HERE)),
            "dwell_image": str(image_path.relative_to(HERE)),
            "result_sha256": sha(result_path), "events_sha256": sha(events_path),
            "dwell_image_sha256": sha(image_path),
            "presentation_sha256": sha(OUT / f"{name}.png"),
            "presentation_pixels_sha256": manifest["pixels_sha256"],
            "expected_point": receipt["point"]}


def main():
    OUT.mkdir(parents=True, exist_ok=False); (OUT / "empty-workspace").mkdir()
    correct_root = HERE / "results/openttd-translated-compact-live-01/live-seed991004"
    wrong_root = HERE / "results/openttd-active-evidence-pair-01/2-stable-seed991004"
    evidence = {"correct": prepare("correct", correct_root, 3),
                "wrong": prepare("wrong", wrong_root, 1)}
    plan = {
        "status": "preregistered_before_four_fresh_model_calls",
        "study": "openttd-anchor-evidence-abba-01",
        "execution_order": ["correct-1", "wrong-1", "wrong-2", "correct-2"],
        "condition_by_call": {"correct-1": "correct", "wrong-1": "wrong",
                              "wrong-2": "wrong", "correct-2": "correct"},
        "expected_op": {"correct": "target_reference", "wrong": "expand_search"},
        "model": "gpt-5.6-luna", "reasoning_effort": "low",
        "common_prompt": (
            "Open the company finances window in this OpenTTD game. Determine whether this "
            "single verified hover receipt identifies the requested control, or whether nearby "
            "toolbar search must expand."),
        "gate": (
            "both correct-anchor calls return a strictly bound target_reference and both retained "
            "wrong-anchor calls return a receipt-bound expand_search; no call is retried"),
        "sources": {name: sha(HERE / name) for name in SOURCES},
        "fixed_evidence": evidence,
        "failure_policy": "retain all four first calls; no retry, repair or exclusion",
        "scope": (
            "four fixed archived-evidence decisions across one correct translated anchor and one "
            "retained confidently-wrong anchor; same Luna-low model, no subagents; no live input, "
            "dynamic latency, expansion efficacy, broad reliability or human-tempo claim"),
    }
    (OUT / "preregistration.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
