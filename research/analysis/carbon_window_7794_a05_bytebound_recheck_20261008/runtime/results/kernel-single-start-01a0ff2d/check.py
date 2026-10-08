"""Bounded sequential lifecycle comparison; no backend or input operations.

Run from repository root. The oracle is a transition table over stage/command,
separate from RequestLifecycle's guard implementation. Source-ref mode exports
the specified Git blob in memory and never changes the checkout.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import sys
import types

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from runtime.kernel.contracts import (
    Action, ActionKind, AuthorityLease, ContractError, EffectOccurrence,
    EffectReceipt, EffectStatus, ExecutionReceipt, ExecutionRequest,
    Observation, ReleaseReceipt, TargetBinding,
)

SOURCE = "runtime/kernel/lifecycle.py"
EVENTS = ("begin-A", "begin-B", "bad-begin", "receipt-A", "receipt-B",
          "effect-A", "effect-B", "stop-unreleased", "stop-released")
H = "a" * 64
OBS = Observation(7, 100, "surface-a", H, 1280, 800, "rgb24")
BIND = TargetBinding("save", 7, "surface-a", H)
LEASE = AuthorityLease("lease", 7, "surface-a", 1000,
                       frozenset({ActionKind.POINTER}))
RELEASE = ReleaseReceipt(800, True)


def reference(state, event):
    """Hand-declared transitions; rejected events preserve the entire state."""
    stage, command = state
    if stage in {"stopped", "verified"}:
        return False, state
    if event.startswith("begin-"):
        if state == ("authorized", None):
            return True, ("authorized", event[-1])
    elif event.startswith("receipt-"):
        if state == ("authorized", event[-1]):
            return True, ("executed", command)
    elif event.startswith("effect-"):
        if state == ("executed", event[-1]):
            return True, ("verified", command)
    elif event == "stop-released":
        return True, ("stopped", command)
    elif event == "stop-unreleased" and stage == "executed":
        return True, ("stopped", command)
    return False, state


def apply_event(flow, event, step):
    command = event[-1]
    try:
        if event.startswith("begin-") or event == "bad-begin":
            bind = BIND if event != "bad-begin" else TargetBinding("other", 7, "surface-a", H)
            req = ExecutionRequest(command, H, bind, LEASE,
                                   (Action("click", ActionKind.POINTER, "click"),))
            flow.begin_execution(req, now_ns=300 + step)
        elif event.startswith("receipt-"):
            flow.record_execution(ExecutionReceipt(
                command, "backend", H, "lease", 7, "surface-a", 500, 700,
                1, EffectOccurrence.POSSIBLE, RELEASE))
        elif event.startswith("effect-"):
            flow.record_effect(EffectReceipt(command, H, 900, EffectStatus.VERIFIED, H))
        else:
            flow.stop("cancelled", release=RELEASE if event == "stop-released" else None)
        accepted = True
    except ContractError:
        accepted = False
    state = (flow.stage.value, flow.request.command_id if flow.request else None)
    return accepted, state


def check(source, max_length=4):
    name = "runtime.kernel._single_start_checked"
    module = types.ModuleType(name)
    sys.modules[name] = module
    exec(compile(source, SOURCE, "exec"), module.__dict__)
    totals = {"traces": 0, "transitions": 0, "mismatched_traces": 0}
    examples = []
    transcript = hashlib.sha256()
    for length in range(1, max_length + 1):
        for trace in itertools.product(EVENTS, repeat=length):
            flow = module.RequestLifecycle()
            flow.record_observation(OBS)
            flow.bind(BIND)
            flow.authorize(LEASE, now_ns=200)
            state = ("authorized", None)
            differs = False
            for step, event in enumerate(trace):
                wanted, state = reference(state, event)
                accepted, actual = apply_event(flow, event, step)
                row = [trace, step, event, wanted, state, accepted, actual]
                transcript.update(json.dumps(row, separators=(",", ":")).encode() + b"\n")
                totals["transitions"] += 1
                if (accepted, actual) != (wanted, state):
                    differs = True
                    if len(examples) < 8:
                        examples.append({"trace": trace, "step": step, "event": event,
                                         "expected": [wanted, state], "actual": [accepted, actual]})
            totals["traces"] += 1
            totals["mismatched_traces"] += int(differs)
    return {"schema": "kernel-single-start-comparison-v1", "max_length": max_length,
            "events": EVENTS, **totals, "comparison_transcript_sha256": transcript.hexdigest(),
            "examples": examples, "status": "PASS_SEQUENTIAL_MODEL" if not totals["mismatched_traces"] else "FAIL_SEQUENTIAL_MODEL"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-ref")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.source_ref:
        source = subprocess.check_output(["git", "show", args.source_ref + ":" + SOURCE], cwd=ROOT)
    else:
        source = (ROOT / SOURCE).read_bytes()
    result = check(source)
    result["source_ref"] = args.source_ref or "working-copy"
    result["source_sha256"] = hashlib.sha256(source).hexdigest()
    result["python_version"] = sys.version.split()[0]
    with Path(args.output).open("x", encoding="utf-8", newline="\n") as output:
        json.dump(result, output, indent=2, sort_keys=True)
        output.write("\n")
    print(json.dumps({k: result[k] for k in ("status", "traces", "transitions", "mismatched_traces")}))
    return int(result["mismatched_traces"] != 0)


if __name__ == "__main__":
    raise SystemExit(main())
