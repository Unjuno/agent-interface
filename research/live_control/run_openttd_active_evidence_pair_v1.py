"""Run a frozen pair for model-proposed OpenTTD targets and active evidence."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from append_checkpoint_v1 import load
from durable_submit_v4 import initialize, run
from evidence_target_contract_v1 import validate as validate_evidence
from openttd_contact_sheet_v1 import build as build_contact_sheet
from openttd_finance_oracle_v1 import score as score_finance
from openttd_hover_receipt_v1 import verify as verify_hover
from received_continuation_v1 import start
from received_exchange_v2 import request_once
from uncertain_target_contract_v1 import validate as validate_uncertain


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-active-evidence-pair-01"
LINUX_ROOT = "/home/taka/agent-interface-bench-feasibility"
WINDOWS_PYTHON = Path(
    "/mnt/c/Users/junny/AppData/Local/Programs/Python/Python312/python.exe")
NODE = r"C:\Program Files\nodejs\node.exe"
CLI = r"C:\Users\junny\AppData\Roaming\npm\node_modules\@openai\codex\bin\codex.js"
WORKSPACE = OUT / "empty-workspace"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n",
                         encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def first(records, event):
    return next(row for row in records if row.get("event") == event)


def windows_path(path):
    return subprocess.run(["wslpath", "-w", str(Path(path).resolve())],
                          capture_output=True, text=True, check=True).stdout.strip()


def parse_model(output):
    events = [json.loads(line) for line in
              (output / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    messages = [row["item"]["text"] for row in events
                if row.get("type") == "item.completed"
                and row.get("item", {}).get("type") == "agent_message"]
    turns = [row for row in events if row.get("type") == "turn.completed"]
    if len(messages) != 1 or len(turns) != 1:
        raise ValueError("one agent message and one completed turn required")
    process = json.loads((output / "process.json").read_text(encoding="utf-8"))
    return {"typed": json.loads(messages[0]), "usage": turns[0]["usage"],
            "runner_ms": (process["exited_ns"] - process["started_ns"]) / 1e6}


def model_call(root, name, prompt, image, instructions, schema):
    prompt_path = root / f"{name}-prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8", newline="\n")
    output = root / name
    command = [str(WINDOWS_PYTHON), windows_path(HERE / "target_handle_model_runner_v2.py"),
               NODE, CLI, windows_path(prompt_path), windows_path(WORKSPACE),
               windows_path(output), "coordinate", windows_path(image),
               windows_path(HERE / instructions), windows_path(HERE / schema)]
    started = time.perf_counter_ns()
    completed = subprocess.run(command, capture_output=True, timeout=90)
    ended = time.perf_counter_ns()
    (root / f"{name}-runner-stdout.txt").write_bytes(completed.stdout)
    (root / f"{name}-runner-stderr.txt").write_bytes(completed.stderr)
    if completed.returncode != 0:
        raise RuntimeError(f"{name} model call failed; no retry")
    result = parse_model(output)
    result["parent_elapsed_ms"] = (ended - started) / 1e6
    dump(root / f"{name}-result.json", result)
    return result


def run_case(index, name, association_fault, seed):
    root = OUT / f"{index}-{name}-seed{seed}"
    root.mkdir()
    error_stream = (root / "stderr.txt").open("w", encoding="utf-8", newline="\n")
    process = subprocess.Popen([
        sys.executable, "-u", str(HERE / "pointer_socket_entry_v19.py"),
        "openttd-hover-target-v1", "serve", "--", "--root", LINUX_ROOT,
        "--out", str(root / "runtime"), "--controller", "scripted"],
        stdout=subprocess.PIPE, stderr=error_stream, text=True)
    temporary = tempfile.TemporaryDirectory(prefix="agent-interface-active-evidence-")
    journal = Path(temporary.name) / "journal.jsonl"
    calls = []
    decision_start_ns = None
    try:
        endpoint = json.loads(process.stdout.readline())
        dump(root / "endpoint.json", endpoint)
        initial = request_once(endpoint["socket"], start(endpoint["socket"]),
                               {"events": ["observation"], "timeout": 30})
        initialize(journal, initial["continuation"])

        def call(spec):
            begin = time.perf_counter_ns()
            result = run(journal, spec)
            calls.append({"begin_ns": begin, "end_ns": time.perf_counter_ns(),
                          "result": result})
            dump(root / "calls.json", calls)
            shutil.copy2(journal, root / "journal.jsonl")
            assert result["state"]["pending"] is None
            return result

        def submit(steps, timeout=8, lifetime_ns=10_000_000_000):
            clock = call({"command": {"op": "clock"}, "timeout": 3})[
                "state"]["last_resolution"]["clock"]
            return call({"command": {"op": "submit",
                "expected_sequence": clock["sequence"],
                "valid_until_ns": clock["runtime_ns"] + lifetime_ns,
                "steps": steps}, "timeout": timeout})

        zoom = submit([{"op": "chord", "modifier": "Control_L", "key": "2"},
                       {"op": "observe"}], timeout=5)
        settled = submit([{"op": "settle", "quiet_ms": 100, "timeout_ms": 1200},
                          {"op": "observe"}], timeout=5)
        source = settled["state"]["continuation"]["observation"]
        source_path = root / "runtime" / Path(source["image"]).name
        decision_start_ns = time.perf_counter_ns()

        candidate_model = model_call(
            root, "model-candidates",
            "Open the company finances window in this OpenTTD game. Identify the toolbar target, "
            "or request active hover evidence if the icons are ambiguous.",
            source_path, "uncertain_target_reference_responder_v1.txt",
            "uncertain_target_contract_schema_v1.json")
        candidate = validate_uncertain(candidate_model["typed"], 1152, 768)
        points = candidate["points"]

        hover_steps = []
        for x, y in points:
            hover_steps.extend([{"op": "pointer_move", "x": x, "y": y},
                                {"op": "dwell_observe", "delay_ms": 800},
                                {"op": "observe"}])
        hover_start_ns = time.perf_counter_ns()
        hovered = submit(hover_steps, timeout=10, lifetime_ns=20_000_000_000)
        hover_return_ns = time.perf_counter_ns()

        readiness = None
        readiness_error = None
        verification_points = list(reversed(points)) if association_fault else points
        try:
            readiness = verify_hover(hovered["reply"]["records"], hover_steps,
                                     verification_points, root / "runtime")
        except ValueError as error:
            readiness_error = str(error)

        presentation = evidence_model = evidence = None
        rehover = rehover_readiness = clear = clicked = final_observation = oracle = None
        if readiness is not None:
            presentation = build_contact_sheet(
                source_path, {"result": hovered}, {"steps": hover_steps}, root / "runtime",
                root / "hover-presentation.png")
            evidence_model = model_call(
                root, "model-evidence-selection",
                "Open the company finances window in this OpenTTD game. The full source frame is "
                "followed by three numbered, runtime-verified hover strips. Select the receipt "
                "whose visible tooltip identifies the requested control.",
                presentation, "evidence_target_reference_responder_v1.txt",
                "evidence_target_contract_schema_v1.json")
            evidence = validate_evidence(evidence_model["typed"], readiness)

            x, y = evidence["point"]
            rehover_steps = [{"op": "pointer_move", "x": x, "y": y},
                             {"op": "dwell_observe", "delay_ms": 800},
                             {"op": "observe"}]
            rehover = submit(rehover_steps, timeout=5)
            rehover_readiness = verify_hover(rehover["reply"]["records"], rehover_steps,
                                             [[x, y]], root / "runtime")
            if (rehover_readiness["receipts"][0]["tooltip"]
                    != evidence["receipt"]["tooltip"]):
                raise ValueError("selected semantic evidence changed before input")

            clear = submit([{"op": "pointer_move", "x": 1000, "y": 180},
                            {"op": "dwell_observe", "delay_ms": 800},
                            {"op": "observe"}], timeout=5)
            clicked = submit([{"op": "pointer_click", "x": x, "y": y,
                               "button": 1, "duration_ms": 40},
                              {"op": "pointer_move", "x": 1000, "y": 180},
                              {"op": "dwell_observe", "delay_ms": 300},
                              {"op": "observe"}], timeout=5)
            observations = [row for row in clicked["reply"]["records"]
                            if row.get("event") == "observation"]
            final_observation = observations[-1]
            oracle = score_finance(root / "runtime" / Path(final_observation["image"]).name)
        else:
            oracle = score_finance(source_path)

        state = load(journal)["continuation"]
        finish = request_once(endpoint["socket"], state, {
            "events": ["independent_evaluation"], "timeout": 25,
            "command": {"op": "finish"}, "request_id": f"finish-{name}"})
        evaluation_return_ns = time.perf_counter_ns()
        code = process.wait(timeout=10)
        result = {
            "index": index, "name": name, "association_fault": association_fault,
            "seed": seed, "zoom_terminal": first(zoom["reply"]["records"], "terminal"),
            "source": source, "candidate_model": candidate_model,
            "candidate_decision": candidate,
            "forced_active_evidence": True,
            "hover_steps": hover_steps,
            "hover_terminal": first(hovered["reply"]["records"], "terminal"),
            "hover_pointer_admissions": [row for row in hovered["reply"]["records"]
                                         if row.get("event") == "pointer_admission"],
            "verification_points": verification_points,
            "hover_readiness": readiness, "hover_readiness_error": readiness_error,
            "presentation": None if presentation is None else str(presentation),
            "evidence_model": evidence_model, "evidence_binding": evidence,
            "rehover_readiness": rehover_readiness,
            "rehover_terminal": None if rehover is None else
                first(rehover["reply"]["records"], "terminal"),
            "clear_terminal": None if clear is None else
                first(clear["reply"]["records"], "terminal"),
            "click_terminal": None if clicked is None else
                first(clicked["reply"]["records"], "terminal"),
            "target_pointer_admissions": [] if clicked is None else
                [row for row in clicked["reply"]["records"]
                 if row.get("event") == "pointer_admission"],
            "final_observation": final_observation,
            "independent_finance_oracle": oracle,
            "driver_independent_evaluation": first(finish["reply"]["records"],
                                                   "independent_evaluation"),
            "bridge_exit_code": code, "durable_calls": len(calls),
            "timing_ms": {
                "hover_submit_to_return": (hover_return_ns - hover_start_ns) / 1e6,
                "decision_start_to_evaluation_return":
                    (evaluation_return_ns - decision_start_ns) / 1e6},
        }
        dump(root / "result.json", result)
        return result
    finally:
        if journal.exists():
            shutil.copy2(journal, root / "journal.jsonl")
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
        error_stream.close()
        temporary.cleanup()


def main():
    plan = json.loads((OUT / "preregistration.json").read_text(encoding="utf-8"))
    for name, digest in plan["sources"].items():
        path = HERE.parent / name if name.startswith("openttd_task/") else HERE / name
        assert sha(path) == digest, name
    cases = [run_case(index, **allocation)
             for index, allocation in enumerate(plan["execution_order"], 1)]
    by_name = {row["name"]: row for row in cases}
    fault = by_name["association-fault"]
    stable = by_name["stable"]
    gate = {
        "same_single_model_route": all(
            row["candidate_model"]["usage"]["input_tokens"] > 0 for row in cases),
        "candidate_points_model_authored": all(
            len(row["candidate_decision"]["points"]) == 3 for row in cases),
        "association_fault_refused_before_semantic_model_and_target_input": (
            fault["hover_readiness"] is None
            and fault["hover_readiness_error"] is not None
            and fault["evidence_model"] is None
            and fault["target_pointer_admissions"] == []
            and fault["independent_finance_oracle"]["success"] is False),
        "stable_evidence_bound_rehovered_and_independently_succeeded": (
            stable["hover_readiness"] is not None
            and stable["evidence_binding"]["status"] == "EVIDENCE_BOUND"
            and stable["rehover_readiness"]["status"] == "READY"
            and stable["click_terminal"]["status"] == "completed"
            and stable["click_terminal"]["release"]["verified"] is True
            and stable["independent_finance_oracle"]["success"] is True),
    }
    gate["passed"] = all(gate.values())
    report = {
        "cases": cases, "promotion_gate": gate,
        "reported_input_tokens": {
            row["name"]: {
                "candidate": row["candidate_model"]["usage"]["input_tokens"],
                "evidence": None if row["evidence_model"] is None else
                    row["evidence_model"]["usage"]["input_tokens"]}
            for row in cases},
        "decision": ("RETAIN_MODEL_PROPOSED_ACTIVE_EVIDENCE_CANDIDATE"
                     if gate["passed"] else "HOLD_AND_PRESERVE_ACTIVE_EVIDENCE_PAIR"),
        "scope": plan["scope"],
    }
    dump(OUT / "report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
