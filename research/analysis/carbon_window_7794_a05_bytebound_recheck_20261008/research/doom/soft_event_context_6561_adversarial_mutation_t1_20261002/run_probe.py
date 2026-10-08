"""One-shot candidate-side packet mutation generator for #6561 T1."""
from __future__ import annotations

import copy
import hashlib
import json
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "frozen"))
import candidate


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_packet() -> dict:
    binding, rows, _ = candidate.fixture()
    cases = []
    for case_id, state, count, event, sequence, _want, raw_events in rows:
        context = candidate.candidate_context(state, count, event, sequence, binding)
        cases.append({
            "case_id": case_id, "history_state": state,
            "current_sequence": sequence, "binding": binding,
            "raw_events": raw_events, "context": context,
            "prompt": candidate.render_prompt_context(context),
        })
    return {"cases": cases}


def make_mutation(base: dict, mutation: str) -> dict:
    packet = copy.deepcopy(base)
    case = next(row for row in packet["cases"] if row["case_id"] == "ONE_SOFT")
    event = case["raw_events"][-1]
    if mutation == "MUTATION_REBOUND_CASE_AND_EVENT_BINDING":
        rebound = {"session": "attacker-controlled-session"}
        case["binding"] = rebound
        event["signal"]["binding"] = copy.deepcopy(rebound)
    elif mutation == "MUTATION_GRANTS_INPUT_AUTHORITY_TRUE":
        event["outcome"]["grants_input_authority"] = True
    elif mutation == "MUTATION_REQUIRES_NEW_DECISION_TRUE":
        event["outcome"]["requires_new_decision"] = True
    elif mutation == "MUTATION_KEEP_EXISTING_POLICY_FALSE":
        event["outcome"]["keep_existing_policy"] = False
    else:
        raise ValueError(f"unknown mutation {mutation}")
    case["context"] = candidate.candidate_context(
        case["history_state"], len(case["raw_events"]), event,
        case["current_sequence"], case["binding"])
    case["prompt"] = candidate.render_prompt_context(case["context"])
    return packet


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: run_probe.py NEW_OUTPUT_DIRECTORY", file=sys.stderr)
        return 2
    output = Path(argv[1]).resolve()
    if output.exists():
        print("STOP_OUTPUT_ALREADY_EXISTS", file=sys.stderr)
        return 2
    output.mkdir(parents=True)
    candidate_path = ROOT / "frozen" / "candidate.py"
    auditor_path = ROOT / "frozen" / "auditor.py"
    repository = ROOT.parents[2]
    for line in (ROOT / "PRE_RUN_SHA256SUMS").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected_digest, relative = line.split(" ", 1)
        frozen_path = repository / relative.strip()
        actual_digest = sha(frozen_path).upper()
        if actual_digest != expected_digest:
            raise SystemExit(f"STOP_PREREG_HASH_MISMATCH {relative.strip()} {actual_digest}")
    spec = json.loads((ROOT / "T1_SPEC.json").read_text(encoding="utf-8"))
    expected = {candidate_path: spec["candidate_source"]["sha256"],
                auditor_path: spec["target_auditor_source"]["sha256"]}
    expected[ROOT / "frozen" / "signal_guard_v2.py"] = spec["contract_sources"][0]["sha256"]
    expected[ROOT / "frozen" / "v30_audit.json"] = spec["contract_sources"][1]["sha256"]
    for path, digest in expected.items():
        actual = sha(path).upper()
        if actual != digest:
            raise SystemExit(f"STOP_SOURCE_HASH_MISMATCH {path.name} {actual}")
    base = build_packet()
    mutations = [
        "MUTATION_REBOUND_CASE_AND_EVENT_BINDING",
        "MUTATION_GRANTS_INPUT_AUTHORITY_TRUE",
        "MUTATION_REQUIRES_NEW_DECISION_TRUE",
        "MUTATION_KEEP_EXISTING_POLICY_FALSE",
    ]
    runs = [{"case_id": "CONTROL_VALID_PACKET", "packet": base}]
    runs.extend({"case_id": name, "packet": make_mutation(base, name)} for name in mutations)
    raw_path = output / "raw_packets.json"
    raw_path.write_text(json.dumps({"runs": runs}, sort_keys=True, separators=(",", ":")) + "\n",
                        encoding="utf-8")
    results = []
    for index, run in enumerate(runs):
        with tempfile.TemporaryDirectory(prefix=f"6561-t1-{index}-") as temp:
            packet_path = Path(temp) / "packet.json"
            packet_path.write_text(json.dumps(run["packet"], sort_keys=True, separators=(",", ":")) + "\n",
                                   encoding="utf-8")
            proc = subprocess.run([sys.executable, "-B", str(auditor_path), str(packet_path)],
                                  capture_output=True, text=True, check=False)
        results.append({"case_id": run["case_id"], "exit_code": proc.returncode,
                        "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()})
    outcome_path = output / "target_auditor_outcomes.json"
    outcome_path.write_text(json.dumps({"runs": results}, indent=2) + "\n", encoding="utf-8")
    environment = {
        "python": sys.version,
        "platform": platform.platform(),
        "source_checkout": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT.parents[2],
            capture_output=True, text=True, check=True).stdout.strip(),
        "network_requested_by_probe": False,
        "container_or_wslc_requested": False,
    }
    (output / "environment.json").write_text(
        json.dumps(environment, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"cases": len(results), "control_exit": results[0]["exit_code"],
                      "mutated_auditor_exit_codes": [row["exit_code"] for row in results[1:]],
                      "outcome_file": outcome_path.name}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
