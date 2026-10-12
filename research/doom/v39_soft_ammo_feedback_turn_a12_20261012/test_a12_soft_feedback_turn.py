import ast
import importlib.util
import json
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTROLLER = ROOT / "map01_overlap_controller_v39.py"
BINDING = {"focus": 7, "surface": 9, "geometry": [0, 0, 1280, 720]}


class SignalReader:
    def __init__(self, signal_id):
        self.signal_id = signal_id

    def read(self, observation):
        return {"format": "observable-signal-v1", "status": "observed",
                "signal_id": self.signal_id, "value": observation[self.signal_id],
                "sequence": observation["sequence"],
                "capture_ns": observation["capture_ns"],
                "binding": observation["pointer_binding"]}


class PlannerClient:
    def __init__(self):
        self.started_inputs = []

    def start_thread(self, **_kwargs):
        return {"thread": {"id": "a12-frozen-thread"}}

    def start_turn(self, _thread_id, inputs, **_kwargs):
        self.started_inputs.append(inputs)
        return {"turn": {"id": f"a12-turn-{len(self.started_inputs)}"}}


def load_sources():
    guard_spec = importlib.util.spec_from_file_location(
        "frozen_guard", ROOT / "observable_signal_guard_v2.py")
    guard_module = importlib.util.module_from_spec(guard_spec)
    guard_spec.loader.exec_module(guard_module)
    adapter_spec = importlib.util.spec_from_file_location(
        "frozen_adapter", ROOT / "persistent_planner_adapter_v2.py")
    adapter_module = importlib.util.module_from_spec(adapter_spec)
    adapter_spec.loader.exec_module(adapter_module)

    tree = ast.parse(CONTROLLER.read_text(encoding="utf-8"))
    top = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    chosen = [top[name] for name in (
        "guard_spec", "ammo_guard_spec", "_typed_json_equal",
        "_signal_pair_matches", "_signal_pair_content_matches",
        "DoomCoverSignalPairMonitor", "build_cover_monitor",
        "latest_soft_event_summary", "begin_model_turn")]
    namespace = {"json": json, "time": time,
                 "ObservableSignalGuard": guard_module.ObservableSignalGuard,
                 "ObservableSignalPolicyMonitor": guard_module.ObservableSignalPolicyMonitor,
                 "MAX_AUTHORED_HEALTH_LOSS": 20,
                 "win": lambda path: str(path)}
    exec(compile(ast.Module(body=chosen, type_ignores=[]), str(CONTROLLER), "exec"), namespace)
    return namespace, adapter_module.PersistentPlannerAdapter


def signal(name, value, sequence, capture_ns):
    return {"format": "observable-signal-v1", "status": "observed",
            "signal_id": name, "value": value, "sequence": sequence,
            "capture_ns": capture_ns, "binding": BINDING}


class SoftAmmoFeedbackTurnTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.functions, cls.Adapter = load_sources()

    def test_soft_ammo_event_reaches_next_adapter_input_without_authority(self):
        health_reader, ammo_reader = SignalReader("health"), SignalReader("ammo")
        source = {"event": "observation", "sequence": 10,
                  "capture_ns": 1_000_000_000, "pointer_binding": BINDING,
                  "health": 70, "ammo": 6}
        monitor, admission = self.functions["build_cover_monitor"](
            health_reader, source,
            {"signal_id": "health", "critical_health_minimum": 45,
             "maximum_health_loss": 8, "max_source_age_ms": 1000},
            "a12", ammo_reader=ammo_reader, requires_ammo=True)
        current = {"event": "typed_observation", "sequence": 11,
                   "capture_ns": 1_100_000_000, "pointer_binding": BINDING,
                   "signals": {"health": signal("health", 70, 11, 1_100_000_000),
                               "ammo": signal("ammo", 4, 11, 1_100_000_000)}}
        invalidation = monitor.observe(current)
        self.assertIsNone(invalidation)
        self.assertEqual(monitor.soft_event_count, 1)
        self.assertEqual(monitor.latest_soft_event["signal"]["value"], 4)

        decision = {"iteration": 2, "cover_policy_source_iteration": 1,
                    "cover_validity_soft_events": monitor.soft_event_count,
                    "cover_validity_latest_soft_event": monitor.latest_soft_event}
        summary = self.functions["latest_soft_event_summary"]([decision])
        self.assertEqual(summary["signal_id"], "ammo")
        self.assertEqual(summary["source_value"], 6)
        self.assertEqual(summary["current_value"], 4)
        self.assertEqual(summary["hard_minimum"], 1)
        self.assertEqual(summary["effect"], "prior_cover_preserved")
        self.assertFalse(summary["grants_input_authority"])

        client = PlannerClient()
        planner = self.Adapter(client, model="frozen-mock", effort="low", cwd=".",
                               base_instructions="inert prompt-boundary fixture")
        planner.start_session()
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            root = Path(directory)
            handle = self.functions["begin_model_turn"](
                planner, root, "synthetic-frame.png", [], 70, 4, summary,
                {"type": "object"})
            self.assertEqual(handle.turn_id, "a12-turn-1")
            inputs = client.started_inputs[0]
            prompt = inputs[0]["text"]
            self.assertIn("Current locally verified ammo: 4.", prompt)
            self.assertIn(json.dumps(summary, separators=(",", ":")), prompt)
            self.assertEqual(inputs[1], {"type": "localImage", "path": "synthetic-frame.png"})
            prompt_file = (root / "prompt.txt").read_text(encoding="utf-8")
            self.assertEqual(prompt_file, prompt)
            receipt = {"classification": "CONSTRUCTION_ONLY_FEEDBACK_PROPAGATION",
                       "cover_admission_status": admission["status"],
                       "cover_hard_ammo_floor": monitor.guards["ammo"].spec["hard_minimum"],
                       "cover_invalidated": invalidation is not None,
                       "soft_event_count": monitor.soft_event_count,
                       "summary": summary,
                       "next_turn_id": handle.turn_id,
                       "prompt_has_current_ammo": "Current locally verified ammo: 4." in prompt,
                       "prompt_has_summary": json.dumps(summary, separators=(",", ":")) in prompt,
                       "summary_grants_input_authority": summary["grants_input_authority"]}
            (ROOT / "results").mkdir(exist_ok=True)
            (ROOT / "results/feedback_receipt.json").write_text(
                json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print("A12_RESULT=" + json.dumps(receipt, sort_keys=True))

    def test_summary_rejects_soft_event_with_authority_claim(self):
        invalid = {"iteration": 2, "cover_policy_source_iteration": 1,
                   "cover_validity_soft_events": 1,
                   "cover_validity_latest_soft_event": {
                       "sequence": 11,
                       "signal": {"signal_id": "ammo", "value": 4, "sequence": 11},
                       "outcome": {"signal_id": "ammo", "status": "SOFT_CHANGED",
                                   "reason": "within_validity_envelope",
                                   "keep_existing_policy": True,
                                   "requires_new_decision": False,
                                   "grants_input_authority": True,
                                   "may_only_preserve_or_reduce_existing_authority": True,
                                   "source_value": 6, "current_value": 4,
                                   "hard_minimum": 1}}}
        with self.assertRaisesRegex(RuntimeError, "invalid prior soft-event evidence"):
            self.functions["latest_soft_event_summary"]([invalid])


if __name__ == "__main__":
    unittest.main(verbosity=2)
