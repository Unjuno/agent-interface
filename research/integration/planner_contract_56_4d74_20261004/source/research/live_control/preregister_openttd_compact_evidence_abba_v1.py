"""Freeze a fixed-evidence full-versus-compact ABBA comparison."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-compact-evidence-abba-01"
PRIOR = HERE / "results/openttd-active-evidence-pair-02/2-stable-seed991004"
SOURCES = [
    "preregister_openttd_compact_evidence_abba_v1.py",
    "run_openttd_compact_evidence_abba_v1.py",
    "openttd_compact_hover_sheet_v1.py",
    "evidence_target_reference_responder_v2.txt",
    "evidence_target_contract_schema_v2.json",
    "evidence_target_contract_v1.py",
    "run_openttd_active_evidence_pair_v1.py",
    "target_handle_model_runner_v2.py",
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "empty-workspace").mkdir()
    stable = json.loads((PRIOR / "result.json").read_text(encoding="utf-8"))
    runtime = PRIOR / "runtime"
    evidence_files = [
        PRIOR / "hover-presentation.png",
        PRIOR / "result.json",
        runtime / "events.jsonl",
    ]
    for receipt in stable["hover_readiness"]["receipts"]:
        observation = next(
            json.loads(line) for line in (runtime / "events.jsonl").read_text(
                encoding="utf-8").splitlines()
            if json.loads(line).get("event") == "observation"
            and json.loads(line).get("sequence") == receipt["dwell_sequence"])
        evidence_files.append(runtime / Path(observation["image"]).name)
    plan = {
        "status": "preregistered_before_four_fresh_model_calls",
        "study": "openttd-compact-evidence-abba-01",
        "execution_order": ["full-1", "compact-1", "compact-2", "full-2"],
        "condition_by_call": {
            "full-1": "full", "compact-1": "compact",
            "compact-2": "compact", "full-2": "full"},
        "model": "gpt-5.6-luna", "reasoning_effort": "low",
        "task": "open the company finances window",
        "common_prompt": (
            "Open the company finances window in this OpenTTD game. Select the numbered, "
            "runtime-verified persistent hover receipt whose visible tooltip identifies the "
            "requested control."),
        "comparison": (
            "same prompt, instructions, schema, model, effort, verified receipt set and correct "
            "point; only the image presentation differs"),
        "full_condition": "existing 1152px source frame followed by five full toolbar strips",
        "compact_condition": (
            "640px sheet containing exact verified tooltip crops, printed receipt/point bindings, "
            "and no full source or non-tooltip pixels"),
        "gate": (
            "all four strict evidence bindings select receipt 5 at [485,51], both compact calls "
            "are correct, both full calls are correct, and compact mean reported input tokens is "
            "lower than full mean"),
        "failure_policy": "retain all four first calls; no retry, repair or exclusion",
        "sources": {name: sha(HERE / name) for name in SOURCES},
        "fixed_evidence": {str(path.relative_to(HERE)): sha(path)
                           for path in dict.fromkeys(evidence_files)},
        "scope": (
            "fixed archived evidence from one OpenTTD task; reported Codex token accounting only; "
            "no served-model identity, monetary cost, latency causality, broad GUI, dynamic-control "
            "or human-tempo claim; one model uses Agent Interface evidence without subagents"),
    }
    (OUT / "preregistration.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
