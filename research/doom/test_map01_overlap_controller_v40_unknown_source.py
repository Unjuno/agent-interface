import ast
import importlib
import io
import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
PINNED_RESEARCH = (HERE / "v16_visual_controller_59_4d74_20261004" /
                   "source" / "research")
sys.path[:0] = [
    str(HERE),
    str(PINNED_RESEARCH / "doom"),
    str(PINNED_RESEARCH / "live_control"),
    str(PINNED_RESEARCH / "observation_gating"),
]
try:
    controller = importlib.import_module("map01_overlap_controller_v40")
except ModuleNotFoundError:
    controller = None


class Reader:
    def __init__(self, signal):
        self.signal = signal

    def read(self, _observation):
        return self.signal


class Map01V40UnknownSourceTests(unittest.TestCase):
    def require_candidate(self):
        self.assertIsNotNone(
            controller,
            "versioned V40 candidate must define fail-closed unknown-source handling",
        )

    def test_unknown_health_returns_nonadmitted_receipt_without_throwing(self):
        self.require_candidate()
        signal = {"status": "unknown", "reason": "invalid_right_aligned_number",
                  "sequence": 35, "capture_ns": 1234}
        try:
            monitor, receipt = controller.build_cover_monitor(
                Reader(signal), {"sequence": 35}, None, 2)
        except RuntimeError as error:
            self.fail(f"unknown source must be a typed stop, not an exception: {error}")
        self.assertIsNone(monitor)
        self.assertEqual(receipt["status"], "rejected_source_signal_unknown")
        self.assertEqual(receipt["source_signal"], signal)
        self.assertIs(receipt["grants_input_authority"], False)

    def test_mismatched_signal_sequences_are_rejected_before_planning(self):
        self.require_candidate()
        health = {"status": "observed", "value": 97, "sequence": 35,
                  "capture_ns": 1000}
        ammo = {"status": "observed", "value": 47, "sequence": 34,
                "capture_ns": 900}
        receipt = controller.source_signal_rejection(health, ammo)
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["status"], "rejected_source_signal_mismatch")
        self.assertFalse(receipt["grants_input_authority"])
        self.assertFalse(receipt["starts_model_call"])

    def test_same_exact_health_and_ammo_source_is_eligible(self):
        self.require_candidate()
        binding = {"focus": 1, "surface": 1, "geometry": [0, 0, 1280, 800]}
        health = {"status": "observed", "value": 97, "sequence": 35,
                  "capture_ns": 1000, "binding": binding}
        ammo = {"status": "observed", "value": 47, "sequence": 35,
                "capture_ns": 1000, "binding": binding}
        self.assertIsNone(controller.source_signal_rejection(health, ammo))

    def test_terminal_release_receipt_requires_verified_empty_state(self):
        self.require_candidate()
        checker = getattr(controller, "terminal_release_verified", None)
        self.assertTrue(callable(checker), "V40 must expose the release predicate it records")
        good = {"status": "cancelled", "release": {
            "verified": True, "keys_down": [], "buttons_down": []}}
        unverified = {"status": "cancelled", "release": {
            "verified": False, "keys_down": [], "buttons_down": []}}
        nonempty = {"status": "cancelled", "release": {
            "verified": True, "keys_down": ["d"], "buttons_down": []}}
        self.assertTrue(checker(good))
        self.assertFalse(checker(unverified))
        self.assertFalse(checker(nonempty))

    def test_source_gates_precede_cover_and_planner_admission(self):
        self.require_candidate()
        source = (HERE / "map01_overlap_controller_v40.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        loop = next(node for node in ast.walk(tree)
                    if isinstance(node, ast.For) and isinstance(node.target, ast.Name)
                    and node.target.id == "index" and isinstance(node.iter, ast.Call)
                    and isinstance(node.iter.func, ast.Name)
                    and node.iter.func.id == "range")
        calls = []
        for node in ast.walk(loop):
            if not isinstance(node, ast.Call):
                continue
            name = node.func.id if isinstance(node.func, ast.Name) else None
            if name in {"source_signal_rejection", "submit_cover", "begin_model_turn"}:
                calls.append((node.lineno, name))
        positions = {name: sorted(line for line, called in calls if called == name)
                     for name in {"source_signal_rejection", "submit_cover", "begin_model_turn"}}
        self.assertGreaterEqual(len(positions["source_signal_rejection"]), 2)
        first_gate, second_gate = positions["source_signal_rejection"][:2]
        self.assertLess(first_gate, positions["submit_cover"][0])
        self.assertLess(positions["submit_cover"][0], second_gate)
        self.assertLess(second_gate, positions["begin_model_turn"][0])

    def test_queued_invalidation_preempts_initial_cover_acceptance(self):
        self.require_candidate()
        source = (HERE / "map01_overlap_controller_v40.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        main = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == "main")
        loop = next(node for node in ast.walk(main)
                    if isinstance(node, ast.For) and isinstance(node.target, ast.Name)
                    and node.target.id == "index")
        planner_start = min(node.lineno for node in ast.walk(loop)
                            if isinstance(node, ast.Call) and
                            isinstance(node.func, ast.Name) and
                            node.func.id == "begin_model_turn")
        invalidation_branch = next(node for node in ast.walk(loop)
            if isinstance(node, ast.If) and any(
                isinstance(part, ast.Subscript) and
                isinstance(part.value, ast.Name) and
                part.value.id == "cover_acceptance" and
                isinstance(part.slice, ast.Constant) and part.slice.value == "event"
                for part in ast.walk(node.test)) and
            any(isinstance(part, ast.Constant) and
                part.value == "policy_invalidation" for part in ast.walk(node.test)))
        branch_calls = [node for node in ast.walk(invalidation_branch)
                        if isinstance(node, ast.Call) and
                        isinstance(node.func, ast.Name)]
        self.assertTrue(any(node.func.id == "cancel_unplanned_invalidated_cover"
                            for node in branch_calls))
        self.assertTrue(any(isinstance(node, ast.Continue)
                            for node in ast.walk(invalidation_branch)))
        self.assertLess(invalidation_branch.lineno, planner_start)

        class Process:
            def __init__(self):
                self.stdin = io.StringIO()

            @staticmethod
            def poll():
                return None

        class Monitor:
            event_types = {"observation"}

            def __init__(self):
                self.seen = []

            def observe(self, row):
                self.seen.append(row)
                return {"status": "hard_change", "sequence": row["sequence"]}

        incoming = queue.Queue()
        observation = {"event": "observation", "sequence": 99}
        accepted = {"event": "accepted", "id": "cover-0"}
        terminal = {"event": "terminal", "id": "cover-0", "status": "cancelled",
                    "release": {"verified": True, "keys_down": [], "buttons_down": []}}
        incoming.put(observation)
        incoming.put(accepted)
        incoming.put(terminal)
        monitor = Monitor()
        latest = []
        process = Process()

        def wait(predicate, timeout=40, observation_monitor=None):
            return controller.wait_for_event(
                incoming, process, predicate, timeout,
                observation_monitor=observation_monitor,
                on_observation=latest.append,
            )

        result = controller.wait_for_cover_acceptance(
            wait, "cover-0", monitor)
        self.assertEqual(result["event"], "policy_invalidation")
        self.assertEqual(result["invalidation"]["sequence"], 99)
        self.assertEqual(monitor.seen, [observation])
        self.assertEqual(latest, [observation])
        released = controller.cancel_unplanned_invalidated_cover(
            process, wait, "cover-0")
        self.assertEqual(released, terminal)
        self.assertEqual(json.loads(process.stdin.getvalue()),
                         {"op": "cancel", "id": "cover-0"})
        self.assertTrue(controller.terminal_release_verified(released))
        self.assertTrue(incoming.empty())

    def test_queued_renewal_invalidation_interrupts_and_releases_cover(self):
        self.require_candidate()

        class Process:
            def __init__(self):
                self.stdin = io.StringIO()

            @staticmethod
            def poll():
                return None

        class Monitor:
            event_types = {"observation"}

            def observe(self, row):
                return {"status": "hard_change", "sequence": row["sequence"]}

        class Planner:
            def __init__(self):
                self.interrupted = []

            def interrupt(self, handle):
                self.interrupted.append(handle)
                return {"turn_id": handle, "interrupted": True}

        incoming = queue.Queue()
        observation = {"event": "observation", "sequence": 101}
        accepted = {"event": "accepted", "id": "cover-0-renew-1"}
        terminal = {"event": "terminal", "id": "cover-0-renew-1",
                    "status": "cancelled", "release": {
                        "verified": True, "keys_down": [], "buttons_down": []}}
        for event in (observation, accepted, terminal):
            incoming.put(event)
        process = Process()
        planner = Planner()
        handle = "turn-4"
        latest = []

        def wait(predicate, timeout=40, observation_monitor=None):
            return controller.wait_for_event(
                incoming, process, predicate, timeout,
                observation_monitor=observation_monitor,
                on_observation=latest.append,
            )

        boundary = controller.wait_for_cover_acceptance(
            wait, "cover-0-renew-1", Monitor())
        self.assertEqual(boundary["event"], "policy_invalidation")
        self.assertEqual(boundary["invalidation"]["sequence"], 101)
        planner_interrupt, released = controller.cancel_invalidated_cover(
            planner, handle, process, wait, "cover-0-renew-1")
        self.assertEqual(planner.interrupted, [handle])
        self.assertEqual(planner_interrupt, {"turn_id": handle, "interrupted": True})
        self.assertEqual(released, terminal)
        self.assertEqual(json.loads(process.stdin.getvalue()),
                         {"op": "cancel", "id": "cover-0-renew-1"})
        self.assertEqual(latest, [observation])
        self.assertTrue(controller.terminal_release_verified(released))
        self.assertTrue(incoming.empty())

    def test_unknown_source_after_finish_eof_still_collects_score(self):
        self.require_candidate()
        events = []
        incoming = queue.Queue()
        child_source = (
            "import json,sys\n"
            "for line in sys.stdin:\n"
            " pass\n"
            "print(json.dumps({'event':'post_control_score','after_eof':True}),flush=True)\n"
        )
        process = subprocess.Popen(
            [sys.executable, "-u", "-c", child_source],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, bufsize=1,
        )

        def read_events():
            for line in process.stdout:
                row = json.loads(line)
                events.append(row)
                incoming.put(row)

        reader_thread = threading.Thread(target=read_events, daemon=True)
        reader_thread.start()

        def wait_for_score(predicate, timeout=1):
            deadline = __import__("time").monotonic() + timeout
            while __import__("time").monotonic() < deadline:
                try:
                    row = incoming.get(timeout=.02)
                except queue.Empty:
                    continue
                if predicate(row):
                    return row
            raise TimeoutError("score event not received")

        with tempfile.TemporaryDirectory() as tmp:
            custody = controller.ControllerSessionCustody(
                process=process,
                wait_for_event=wait_for_score,
                events=events,
                reader_thread=reader_thread,
                output_dir=Path(tmp),
                finish_timeout=.01,
                process_timeout=2,
            )
            score = custody.finish(reason="eof_cleanup")
            self.assertEqual(score, {"event": "post_control_score", "after_eof": True})
            self.assertEqual(process.wait(timeout=2), 0)
            receipt = json.loads((Path(tmp) / "controller-cleanup.json").read_text())
            self.assertTrue(receipt["score_observed"])
        if process.stderr is not None:
            process.stderr.close()
        if process.stdout is not None:
            process.stdout.close()

    def test_uncaught_controller_error_runs_atexit_custody(self):
        self.require_candidate()
        child_source = (
            "import json,sys\n"
            "for line in sys.stdin:\n"
            " cmd=json.loads(line)\n"
            " if cmd.get('op') == 'finish':\n"
            "  print(json.dumps({'event':'post_control_score','from_atexit':True}),flush=True)\n"
            "  break\n"
        )
        parent_source = f"""
import atexit, json, queue, subprocess, sys, threading
from pathlib import Path
from map01_overlap_controller_v40 import ControllerSessionCustody
events=[]
incoming=queue.Queue()
process=subprocess.Popen([sys.executable,'-u','-c',{child_source!r}],stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
def read_events():
    for line in process.stdout:
        row=json.loads(line); events.append(row); incoming.put(row)
reader=threading.Thread(target=read_events,daemon=True); reader.start()
def wait_for_score(predicate,timeout=2):
    import time
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        try: row=incoming.get(timeout=.02)
        except queue.Empty: continue
        if predicate(row): return row
    raise TimeoutError('post-score missing')
custody=ControllerSessionCustody(process,wait_for_score,events,reader,Path(sys.argv[1]))
atexit.register(custody.finish)
raise RuntimeError('injected controller failure')
"""
        with tempfile.TemporaryDirectory() as tmp:
            completed = subprocess.run(
                [sys.executable, "-c", parent_source, tmp],
                cwd=HERE, capture_output=True, text=True, timeout=10,
            )
            self.assertNotEqual(completed.returncode, 0)
            receipt_path = Path(tmp) / "controller-cleanup.json"
            self.assertTrue(receipt_path.is_file())
            receipt = json.loads(receipt_path.read_text())
            self.assertTrue(receipt["finish_sent"])
            self.assertTrue(receipt["score_observed"])
            self.assertEqual(receipt["process_exit"], 0)
            raw = [json.loads(line) for line in
                   (Path(tmp) / "controller-events.jsonl").read_text().splitlines()]
            self.assertEqual(raw, [{"event": "post_control_score", "from_atexit": True}])

    def test_child_finish_is_idempotent_and_persists_score_and_events(self):
        self.require_candidate()
        self.assertTrue(
            callable(getattr(controller, "ControllerSessionCustody", None)),
            "controller must own exception-safe child-session cleanup",
        )
        events = []
        incoming = queue.Queue()
        child_source = (
            "import json,sys\n"
            "for line in sys.stdin:\n"
            " cmd=json.loads(line)\n"
            " if cmd.get('op') == 'finish':\n"
            "  print(json.dumps({'event':'post_control_score','test_score':7}),flush=True)\n"
            "  break\n"
        )
        process = subprocess.Popen(
            [sys.executable, "-u", "-c", child_source],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, bufsize=1,
        )

        def read_events():
            for line in process.stdout:
                row = json.loads(line)
                events.append(row)
                incoming.put(row)

        reader_thread = threading.Thread(target=read_events, daemon=True)
        reader_thread.start()

        def wait_for_score(predicate, timeout=2):
            deadline = __import__("time").monotonic() + timeout
            while __import__("time").monotonic() < deadline:
                try:
                    row = incoming.get(timeout=.05)
                except queue.Empty:
                    if process.poll() is not None:
                        break
                    continue
                if predicate(row):
                    return row
            raise TimeoutError("score event not received")

        with tempfile.TemporaryDirectory() as tmp:
            custody = controller.ControllerSessionCustody(
                process=process,
                wait_for_event=wait_for_score,
                events=events,
                reader_thread=reader_thread,
                output_dir=Path(tmp),
            )
            first = custody.finish(reason="test_exception_cleanup")
            second = custody.finish(reason="duplicate_close")
            self.assertEqual(first, {"event": "post_control_score", "test_score": 7})
            self.assertEqual(second, first)
            self.assertEqual(process.wait(timeout=2), 0)
            receipt = json.loads((Path(tmp) / "controller-cleanup.json").read_text())
            self.assertTrue(receipt["finish_sent"])
            self.assertTrue(receipt["score_observed"])
            self.assertEqual(receipt["process_exit"], 0)
            raw = [json.loads(line) for line in
                   (Path(tmp) / "controller-events.jsonl").read_text().splitlines()]
            self.assertEqual(raw, [{"event": "post_control_score", "test_score": 7}])
        if process.stderr is not None:
            process.stderr.close()
        if process.stdout is not None:
            process.stdout.close()

    def test_finish_write_backpressure_is_bounded_and_retires_owned_child(self):
        self.require_candidate()
        process = subprocess.Popen(
            [sys.executable, "-u", "-c", "import time; time.sleep(10)"],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, text=True, bufsize=1,
        )
        lock = threading.Lock()
        counts = {"started": 0, "completed": 0}

        def fill_pipe_until_blocked():
            payload = b"x" * 4096
            while True:
                with lock:
                    counts["started"] += 1
                try:
                    os.write(process.stdin.fileno(), payload)
                except (BrokenPipeError, OSError, ValueError):
                    return
                with lock:
                    counts["completed"] += 1

        filler = threading.Thread(target=fill_pipe_until_blocked, daemon=True)
        finisher_done = threading.Event()
        finisher_errors = []
        try:
            filler.start()
            deadline = time.monotonic() + 2
            pipe_blocked = False
            while time.monotonic() < deadline:
                with lock:
                    first_completed = counts["completed"]
                    blocked = counts["started"] > counts["completed"]
                if first_completed > 0 and blocked:
                    time.sleep(.1)
                    with lock:
                        pipe_blocked = (counts["started"] > counts["completed"] and
                                        counts["completed"] == first_completed)
                    if pipe_blocked:
                        break
                time.sleep(.01)
            self.assertTrue(pipe_blocked, "could not establish a full non-reading child pipe")

            def wait_for_score(_predicate, timeout=40):
                time.sleep(timeout)
                raise TimeoutError("no score from non-reading child")

            with tempfile.TemporaryDirectory() as tmp:
                custody = controller.ControllerSessionCustody(
                    process=process, wait_for_event=wait_for_score, events=[],
                    reader_thread=None, output_dir=Path(tmp),
                    finish_timeout=.05, process_timeout=.2,
                )

                def finish():
                    try:
                        custody.finish(reason="pipe_backpressure_test")
                    except BaseException as error:
                        finisher_errors.append(repr(error))
                    finally:
                        finisher_done.set()

                finisher = threading.Thread(target=finish, daemon=True)
                finisher.start()
                returned_within_bound = finisher_done.wait(.35)
                if not returned_within_bound and process.poll() is None:
                    process.terminate()
                finisher.join(timeout=2)
                filler.join(timeout=2)
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=2)
                if finisher.is_alive():
                    self.fail("finish remained blocked after terminating its child")
                self.assertTrue(
                    returned_within_bound,
                    "finish_timeout must bound delivery to a non-reading child",
                )
                self.assertFalse(finisher_errors)
                receipt = json.loads(
                    (Path(tmp) / "controller-cleanup.json").read_text())
                self.assertFalse(receipt["finish_sent"])
                self.assertTrue(receipt["finish_send_timeout"])
                self.assertTrue(receipt["child_termination_requested"])
                self.assertIn("finish_send_timeout", {
                    error.get("step") for error in receipt["errors"]})
                self.assertFalse(receipt["score_observed"])
                self.assertIsNotNone(receipt["process_exit"])
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
            if process.stdin is not None and not process.stdin.closed:
                process.stdin.close()

    def test_late_finish_writer_success_does_not_claim_delivery(self):
        self.require_candidate()

        class Stdin:
            def __init__(self):
                self.closed = False
                self.started = threading.Event()
                self.release = threading.Event()
                self.written = []

            def write(self, value):
                self.started.set()
                if not self.release.wait(2):
                    raise TimeoutError("test writer was not released")
                self.written.append(value)
                return len(value)

            @staticmethod
            def flush():
                return None

            def close(self):
                self.closed = True

        class Process:
            def __init__(self):
                self.stdin = Stdin()
                self.exit_code = None

            def poll(self):
                return self.exit_code

            def terminate(self):
                self.exit_code = -15
                self.stdin.release.set()

            def kill(self):
                self.exit_code = -9
                self.stdin.release.set()

            def wait(self, timeout=None):
                self.stdin.release.set()
                return self.exit_code

        process = Process()

        def wait_for_score(_predicate, timeout=40):
            time.sleep(timeout)
            raise TimeoutError("no score after finish delivery timeout")

        with tempfile.TemporaryDirectory() as tmp:
            custody = controller.ControllerSessionCustody(
                process=process, wait_for_event=wait_for_score, events=[],
                reader_thread=None, output_dir=Path(tmp),
                finish_timeout=.01, process_timeout=.05,
            )
            custody.finish(reason="late_writer_success_test")
            receipt = json.loads(
                (Path(tmp) / "controller-cleanup.json").read_text())
            self.assertTrue(process.stdin.started.is_set())
            self.assertEqual(process.stdin.written, ['{"op":"finish"}\n'])
            self.assertFalse(receipt["finish_sent"])
            self.assertTrue(receipt["finish_send_timeout"])
            self.assertTrue(receipt["finish_write_completed_after_timeout"])
            self.assertTrue(receipt["child_termination_requested"])
            self.assertFalse(receipt["score_observed"])
            self.assertEqual(receipt["process_exit"], -15)


if __name__ == "__main__":
    unittest.main()
