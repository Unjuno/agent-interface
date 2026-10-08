"""Finite, inert callback interleavings against exact retained runtime copies."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

SCHEDULES = ["never", "initial", "observe:1", "observe:2", "observe:3",
             "admit:1", "admit:2", "execute:1", "execute:2", "verify:1", "verify:2",
             "journal.observation_recorded:1", "journal.observation_recorded:2",
             "journal.branch_selected:1", "journal.branch_selected:2",
             "journal.branch_selected:3", "journal.effect_checked:1",
             "journal.action_terminal:1"]
TERMINALS = ["completed", "delivery_uncertain", "release_failed", "refused_no_input"]


def interface():
    branches = {}
    for phase, name in enumerate(("empty", "filled", "done")):
        branches[name] = {"branches": [{
            "when": {"phase": phase}, "outcome": "action" if phase < 2 else "complete",
            "action": ("enter", "save", None)[phase],
            "next_state": ("filled", "done", None)[phase], "reason": None}]}
    return {"format": "compiled-gui-interface-v1", "interface_id": "cancel-matrix",
            "session_scope": "inert", "surface": "form", "predicates": ["phase"],
            "symbols": {"field": {"kind": "target_reference", "target_reference": "field",
                                   "identity_predicate": "phase", "dependencies": ["phase"]}},
            "actions": {name: {"target_symbol": "field", "operation": name,
                                "expected_effect": {"phase": i + 1}}
                        for i, name in enumerate(("enter", "save"))},
            "method": {"name": "two-steps", "version": "1", "initial_state": "empty",
                       "max_transitions": 2, "max_runtime_ms": 10, "states": branches}}


class InertDriver:
    def __init__(self, schedule, terminal):
        self.schedule, self.terminal = schedule, terminal
        self.trace, self.counts, self.latched = [], {}, False
        if schedule == "initial":
            self.latch("initial")

    def log(self, event, **payload):
        self.trace.append({"order": len(self.trace), "event": event, **payload})

    def latch(self, trigger):
        self.latched = True
        self.log("cancel_latched", trigger=trigger)

    def entry(self, stage, **payload):
        count = self.counts.get(stage, 0) + 1
        self.counts[stage] = count
        self.log("callback_entry", stage=stage, occurrence=count, **payload)
        if self.schedule == f"{stage}:{count}":
            self.latch(self.schedule)
        return count

    def observe(self, request):
        n = self.entry("observe")
        row = {"sequence": n, "captured_ns": 0, "surface": "form",
               "predicates": {"phase": n - 1}, "evidence_ref": f"frame{n}",
               "evidence_digest": f"digest{n}"}
        self.log("observe_return", row=row)
        return row

    def admit(self, request):
        self.entry("admit")
        return {"eligible": True, "status": "revalidated", "authorization": "one-use",
                "expected_sequence": request["observation"]["sequence"],
                "valid_until_ns": 100_000_000}

    def execute(self, request):
        n = self.entry("execute", action=request["action"])
        status = {"release_failed": "completed", "refused_no_input": "refused"}.get(
            self.terminal, self.terminal)
        row = {"status": status, "action_id": f"action{n}", "effect_ref": f"effect{n}",
               "release": {"verified": self.terminal in {"completed", "delivery_uncertain"},
                           "keys_down": [], "buttons_down": []}}
        if self.terminal == "refused_no_input":
            row["input_dispatched"] = False
        self.log("execute_return", action=request["action"], row=row)
        return row

    def verify(self, request):
        self.entry("verify", action=request["action"])
        row = {"status": "succeeded", "evidence_ref": request["observation"]["evidence_ref"]}
        self.log("verify_return", action=request["action"], row=row)
        return row

    def cancelled(self):
        self.log("cancel_checked", value=self.latched)
        return self.latched

    def journal(self, event):
        self.entry("journal." + event["event"])
        self.log("journal", row=event)


def load(path):
    spec = importlib.util.spec_from_file_location("retained_compiled", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def generate(source, label):
    module = load(source)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    for schedule in SCHEDULES:
        for terminal in TERMINALS:
            driver = InertDriver(schedule, terminal)
            receipt, error = None, None
            try:
                receipt = module.run(interface(), {
                    "observe": driver.observe, "admit": driver.admit, "execute": driver.execute,
                    "verify_effect": driver.verify, "cancelled": driver.cancelled,
                    "journal": driver.journal}, clock=lambda: 0)
            except Exception as exc:
                error = {"type": type(exc).__name__, "message": str(exc)}
            yield {"source": label, "source_sha256": digest, "schedule": schedule,
                   "terminal": terminal, "trace": driver.trace, "receipt": receipt, "error": error}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=Path(__file__).parent / "sources")
    parser.add_argument("--labels", nargs="+", default=["main", "pr6863"])
    args = parser.parse_args()
    for label in args.labels:
        for row in generate(args.source_dir / (label + ".py"), label):
            print(json.dumps(row, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
