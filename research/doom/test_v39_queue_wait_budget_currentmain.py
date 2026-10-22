"""Current-main wait-budget boundary tests; no game, model, or process launch."""
import ast
from pathlib import Path
import queue
import unittest

CONTROLLER_PATH = Path(__file__).with_name("map01_overlap_controller_v39.py")


class Clock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now


class Events:
    def __init__(self, clock, rows=()):
        self.clock = clock
        self.rows = list(rows)
        self.timeouts = []

    def get(self, timeout):
        self.timeouts.append(timeout)
        if self.rows and self.rows[0][0] <= self.clock.now + timeout:
            at, row = self.rows.pop(0)
            self.clock.now = max(self.clock.now, at)
            return row
        self.clock.now += timeout
        raise queue.Empty()


def extracted_wait(rows=()):
    source = ast.parse(CONTROLLER_PATH.read_bytes())
    main = next(node for node in source.body
                if isinstance(node, ast.FunctionDef) and node.name == "main")
    waits = [node for node in ast.walk(main)
             if isinstance(node, ast.FunctionDef) and node.name == "wait"]
    if len(waits) != 1:
        raise AssertionError(f"expected one current-main nested wait, found {len(waits)}")

    wrapper = ast.parse(
        "def factory(incoming, process, time, queue):\n"
        "    latest = None\n"
        "    def get_latest():\n"
        "        return latest\n"
        "    return wait, get_latest\n").body[0]
    wrapper.body.insert(1, waits[0])
    clock = Clock()
    events = Events(clock, rows)
    process = type("Process", (), {"poll": lambda self: None})()
    namespace = {"queue": queue, "time": clock}
    module = ast.fix_missing_locations(ast.Module(body=[wrapper], type_ignores=[]))
    exec(compile(module, CONTROLLER_PATH, "exec"), namespace)
    wait, latest = namespace["factory"](events, process, clock, queue)
    return wait, latest, clock, events


class CurrentMainWaitBudgetTests(unittest.TestCase):
    def test_short_remaining_budget_is_not_rounded_up_to_floor(self):
        wait, _, clock, events = extracted_wait()
        with self.assertRaises(TimeoutError):
            wait(lambda row: False, timeout=0.05)
        self.assertEqual(events.timeouts, [0.05])
        self.assertAlmostEqual(clock.now, 0.05)

    def test_poll_interval_remains_capped_at_250ms(self):
        wait, _, clock, events = extracted_wait()
        with self.assertRaises(TimeoutError):
            wait(lambda row: False, timeout=0.5)
        self.assertEqual(events.timeouts, [0.25, 0.25])
        self.assertAlmostEqual(clock.now, 0.5)

    def test_event_before_deadline_is_returned(self):
        event = {"event": "ready"}
        wait, _, clock, events = extracted_wait([(0.02, event)])
        self.assertIs(wait(lambda row: row["event"] == "ready", timeout=0.05), event)
        self.assertEqual(events.timeouts, [0.05])
        self.assertAlmostEqual(clock.now, 0.02)

    def test_dequeued_observation_is_retained_before_deadline_return(self):
        observation = {"event": "observation", "sequence": 7}
        wait, latest, clock, events = extracted_wait([(0.02, observation)])
        with self.assertRaises(TimeoutError):
            wait(lambda row: False, timeout=0.05)
        self.assertIs(latest(), observation)
        self.assertAlmostEqual(clock.now, 0.05)
        self.assertEqual(len(events.timeouts), 2)
        self.assertAlmostEqual(events.timeouts[0], 0.05)
        self.assertAlmostEqual(events.timeouts[1], 0.03)


if __name__ == "__main__":
    unittest.main()
