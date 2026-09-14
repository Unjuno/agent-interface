"""Exercise local visual barriers through the existing bounded Executor."""
import json
import threading
import time
from pathlib import Path

from PIL import Image

from executor_v3 import Executor
from local_visual_barrier_program_v1 import prepare, run
from probe_persistent_effect_receipt_v1 import effect, root


HERE = Path(__file__).resolve().parent


def opened(path):
    with Image.open(path) as image:
        return image.convert("RGB")


def barrier_spec(memory, identifier="effect"):
    return {
        "op": "local_visual_barrier",
        "barrier_id": identifier,
        "source_sequence": memory["before_sequence"],
        "box": memory["crop_box"],
        "metric": "persistent_rgb_change",
        "rgb_threshold": 20,
        "minimum_changed_pixels": 1000,
        "required_samples": 2,
        "sample_interval_ms": 20,
        "timeout_ms": 500,
        "on_unmet": "needs_decision",
    }


class Cancel:
    def __init__(self):
        self.event = threading.Event()

    def is_set(self):
        return self.event.is_set()

    def wait(self, seconds):
        return self.event.wait(seconds)


class Backend:
    def __init__(self, source, samples, memory, bindings, emit):
        self.sequence = memory["before_sequence"]
        self.source = source
        self.samples = list(samples)
        self.bindings = list(bindings)
        self.emit = emit
        self.executed = []
        self.barriers = {}
        self.lease = None

    def validate(self, steps):
        rewritten, barriers = prepare(steps, self.source, self.sequence, "openttd-window")
        if any(not isinstance(step, dict) or step.get("op") not in ("pointer_drag", "pointer_click", "observe")
               for step in rewritten):
            raise ValueError("unsupported fake operation")
        self.barriers = barriers

    def execute(self, step, cancel, identifier, index):
        if step["op"] != "local_visual_barrier":
            self.executed.append(step["op"])
            return
        barrier = self.barriers.pop(step["barrier_id"], None)
        if barrier is None:
            from executor_v3 import DecisionRequired
            raise DecisionRequired("local visual barrier identity unavailable")

        def capture():
            image = self.samples.pop(0)
            binding = self.bindings.pop(0)
            return image, binding, time.perf_counter_ns()

        run(step, barrier, capture, cancel, lambda outcome: self.emit({
            "event": "local_visual_barrier", "id": identifier, "step": index, **outcome,
        }))

    def release_all(self):
        return {"verified": True, "keys_down": []}


def execute_case(source, samples, memory, bindings):
    events = []
    backend = Backend(source, samples, memory, bindings, events.append)
    engine = Executor(backend, events.append)
    steps = [
        {"op": "pointer_drag"}, barrier_spec(memory), {"op": "pointer_click"},
    ]
    engine.submit("program", steps, memory["before_sequence"], time.perf_counter_ns() + 2_000_000_000)
    engine.active[2].join()
    terminal = next(event for event in events if event.get("event") == "terminal")
    return backend, events, terminal


def refused(call):
    try:
        call()
    except (TypeError, ValueError):
        return True
    return False


def main():
    _, memory, latest = effect(root(11), 5, 6)
    directory = root(11) / "runtime"
    source = opened(directory / memory["before_image"])
    after = opened(directory / memory["after_image"])
    later = opened(directory / latest)
    met_backend, met_events, met_terminal = execute_case(
        source, [after, later], memory, ["openttd-window"] * 2)
    assert met_backend.executed == ["pointer_drag", "pointer_click"]
    assert met_terminal["status"] == "completed" and met_terminal["steps_completed"] == 3
    met = next(event for event in met_events if event.get("event") == "local_visual_barrier")
    assert met["reason"] == "met" and met["grants_input_authority"] is False

    unmet_backend, unmet_events, unmet_terminal = execute_case(
        source, [source.copy(), source.copy()], memory, ["openttd-window"] * 2)
    assert unmet_backend.executed == ["pointer_drag"]
    assert unmet_terminal["status"] == "needs_decision" and unmet_terminal["steps_completed"] == 1
    unmet = next(event for event in unmet_events if event.get("event") == "local_visual_barrier")
    assert unmet["reason"] == "unmet"

    changed_backend, changed_events, changed_terminal = execute_case(
        source, [after, later], memory, ["openttd-window", "other-window"])
    assert changed_backend.executed == ["pointer_drag"]
    assert changed_terminal["status"] == "needs_decision"
    changed = next(event for event in changed_events if event.get("event") == "local_visual_barrier")
    assert changed["reason"] == "binding_changed"

    base = barrier_spec(memory)
    controls = {
        "barrier_first": refused(lambda: prepare([base, {"op": "pointer_click"}], source,
                                                 memory["before_sequence"], "openttd-window")),
        "barrier_last": refused(lambda: prepare([{"op": "pointer_drag"}, base], source,
                                                memory["before_sequence"], "openttd-window")),
        "no_preceding_mutation": refused(lambda: prepare(
            [{"op": "observe"}, base, {"op": "pointer_click"}], source,
            memory["before_sequence"], "openttd-window")),
        "no_later_mutation": refused(lambda: prepare(
            [{"op": "pointer_drag"}, base, {"op": "observe"}], source,
            memory["before_sequence"], "openttd-window")),
        "duplicate_id": refused(lambda: prepare(
            [{"op": "pointer_drag"}, base, {"op": "pointer_click"}, base,
             {"op": "pointer_click"}], source, memory["before_sequence"], "openttd-window")),
        "combined_timeout": refused(lambda: prepare(
            [{"op": "pointer_drag"}, {**base, "timeout_ms": 2000},
             {"op": "pointer_click"}, {**base, "barrier_id": "second", "timeout_ms": 2000},
             {"op": "pointer_click"}], source, memory["before_sequence"], "openttd-window")),
    }
    assert all(controls.values())
    report = {
        "passed": True,
        "met": {"executed": met_backend.executed, "terminal": met_terminal, "outcome": met},
        "unmet": {"executed": unmet_backend.executed, "terminal": unmet_terminal, "outcome": unmet},
        "binding_changed": {"executed": changed_backend.executed,
                            "terminal": changed_terminal, "outcome": changed},
        "pre_input_controls": controls,
        "decision": "ADVANCE_TO_X11_BACKEND_INTEGRATION;_NO_LIVE_BENCHMARK_USE",
        "scope": "existing Executor with a fake backend over archived selected OpenTTD frames; no X11 capture, semantic correctness, speed, token or generalization claim",
    }
    destination = HERE / "results/local-visual-barrier-program-v1-probe.json"
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
