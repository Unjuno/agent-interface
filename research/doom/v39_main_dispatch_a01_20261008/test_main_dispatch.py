"""Offline control-flow integration experiment for V39's observation dispatch.

Executes exact current-main helper functions and queue-consumer closures from
controller main(), with an inert queue and synthetic typed/full observations.
No game, model, App Server, GUI or OS input is started.
"""
import ast
import hashlib
import json
import queue
import threading
import time
import unittest
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CONTROLLER_PATH = REPO / "research/doom/map01_overlap_controller_v39.py"
SOURCE_PATH = REPO / "research/doom/doom_source_refresh_v1.py"
GUARD_PATH = REPO / "research/live_control/observable_signal_guard_v2.py"
SOURCE_REFRESH_PATH = REPO / "research/doom/doom_source_refresh_v1.py"
ADAPTER_PATH = REPO / "research/live_control/persistent_planner_adapter_v2.py"


def load_functions():
    tree = ast.parse(CONTROLLER_PATH.read_text(encoding="utf-8"))
    top = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    main = top["main"]
    nested = {n.name: n for n in ast.walk(main) if isinstance(n, ast.FunctionDef)}
    helpers = [top[n] for n in (
        "_typed_json_equal", "_signal_pair_matches", "_signal_pair_content_matches",
        "DoomCoverSignalPairMonitor", "cancel_invalidated_cover",
        "drain_pending_observation_events", "temporal_sheet")]
    module = ast.Module(body=helpers, type_ignores=[])
    ns = {"json": json, "time": time, "queue": queue, "Image": Image}
    exec(compile(module, str(CONTROLLER_PATH), "exec"), ns)
    # Extract main()'s real event-routing closure verbatim; only globals/locals
    # are supplied by this harness. Main's WSL/model/game startup is excluded.
    exact_wait = ast.unparse(nested["wait"])
    import textwrap
    wrapper = ("def make_waiter(incoming, process):\n"
               "    latest = None\n"
               + textwrap.indent(exact_wait, "    ") + "\n"
               "    return wait, lambda: latest\n")
    exec(compile(wrapper, str(CONTROLLER_PATH) + "#wait-harness", "exec"), ns)
    return ns


class Reader:
    def __init__(self, signal_id): self.signal_id = signal_id
    def read(self, observation):
        row = observation["signals"][self.signal_id]
        return dict(row)


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.ns = load_functions()
        self.health = Reader("health")
        self.ammo = Reader("ammo")
        self.binding = {"focus": 1, "surface": 2, "geometry": [0, 0, 642, 502]}
        self.monitor = self.ns["DoomCoverSignalPairMonitor"]

    def event(self, kind, seq, health, ammo, capture):
        signals = {}
        for key, value in (("health", health), ("ammo", ammo)):
            signals[key] = {"status":"observed", "signal_id":key, "value":value,
                            "sequence":seq, "capture_ns":capture, "binding":self.binding}
        row = {"event":kind, "id":f"obs-{seq}", "step":seq, "sequence":seq,
               "capture_ns":capture, "pointer_binding":self.binding,
               "signals":signals, "frame_rgb_sha256":"a"*64}
        if kind == "observation": row.update(exact=True, image="synthetic.png")
        return row

    def make_monitor(self):
        # Build real production guards with minimal schema-identical signal reader.
        GuardType = load_guard()
        rows = {}
        for name, value in (("health",70),("ammo",8)):
            source={"status":"observed","signal_id":name,"value":value,
                    "sequence":10,"capture_ns":1000,"binding":self.binding}
            spec={"op":"observable_signal_guard","guard_id":name,"source_sequence":10,
                  "signal_id":name,"source_value":value,"hard_minimum":65 if name=="health" else 1,
                  "max_source_age_ms":30000,"on_soft_change":"preserve_existing_policy",
                  "on_hard_change":"needs_decision","on_unknown":"needs_decision"}
            rows[name]=GuardType(spec,source,self.binding)
        return self.monitor(rows,self.health,self.ammo)

    def test_main_wait_cancel_path_consumes_full_pair_and_refreshes_source(self):
        import importlib.util
        monitor=self.make_monitor()
        incoming=queue.Queue()
        process=type("P",(),{"poll":lambda self:None})()
        wait,get_latest=self.ns["make_waiter"](incoming,process)
        typed=self.event("typed_observation",11,60,8,2000)
        full=self.event("observation",11,60,8,2000)
        terminal={"event":"terminal","id":"cover-0","status":"cancelled",
                  "release":{"verified":True,"keys_down":[],"buttons_down":[]}}
        incoming.put(typed)
        boundary=wait(lambda r:r.get("event")=="terminal",timeout=1,observation_monitor=monitor)
        self.assertEqual(boundary["event"],"policy_invalidation")
        self.assertEqual(boundary["invalidation"]["reason"],"health:below_hard_minimum")
        incoming.put(full); incoming.put(terminal)
        events=[]
        class Stdin:
            def write(self,_value): events.append("cancel_write")
            def flush(self): events.append("cancel_flush")
        class ProcessWithInput: stdin=Stdin()
        class Planner:
            def interrupt(self,_handle,before_transport):
                before_transport(); events.append("interrupt_request")
                self.answer={"status":"completed","answer_eligible":False,"answer":None}
                return {"outcome":"acknowledged","cancellation_requested":True}
        planner=Planner()
        interrupt,closed=self.ns["cancel_invalidated_cover"](
            planner,object(),ProcessWithInput(),
            lambda predicate: wait(predicate,timeout=1),"cover-0")
        self.assertIs(closed,terminal)
        self.assertEqual(events,["cancel_write","cancel_flush","interrupt_request"])
        self.assertEqual(planner.answer,{"status":"completed","answer_eligible":False,"answer":None})
        self.assertEqual(get_latest(),full)
        spec=importlib.util.spec_from_file_location("source_refresh",SOURCE_REFRESH_PATH)
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        fresh,receipt=module.refresh_source(get_latest(),self.health,self.ammo,
            lambda _command:None,lambda _predicate,**_kwargs:None,"refresh-0")
        self.assertIs(fresh,full)
        self.assertEqual(receipt["status"],"already_observed")
        self.assertEqual(fresh["signals"]["health"]["value"],60)
        self.assertEqual(fresh["signals"]["ammo"]["value"],8)


def load_guard():
    import importlib.util
    spec=importlib.util.spec_from_file_location("guard_v2",GUARD_PATH)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod.ObservableSignalGuard


if __name__ == "__main__": unittest.main()
