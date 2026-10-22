import ast
import importlib.util
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTROLLER = ROOT / "map01_overlap_controller_v39.py"
sys.path.insert(0, str(ROOT))
from action_validity_admission_v1 import SNAPSHOT_FORMAT, evaluate_action_validity
from doom_action_validity_contract_v1 import bindings_equal_exact, build_contract
from final_action_admission_v2 import decide_final_admission

BINDING = {"focus": 7, "surface": 9, "geometry": [0, 0, 1280, 720]}
COMMANDS = [{"action": "fire", "extent": "short"}]
AUTHORED = {"critical_health_minimum": 45, "maximum_health_loss": 8,
            "minimum_ammo": 5, "max_current_age_ms": 500}


class SignalReader:
    def __init__(self, signal_id): self.signal_id = signal_id
    def read(self, observation):
        return {"format": "observable-signal-v1", "status": "observed",
                "signal_id": self.signal_id, "value": observation[self.signal_id],
                "sequence": observation["sequence"], "capture_ns": observation["capture_ns"],
                "binding": observation["pointer_binding"]}


class PlannerClient:
    def __init__(self): self.started_inputs = []
    def start_thread(self, **_kwargs): return {"thread": {"id": "a13-thread"}}
    def start_turn(self, _thread_id, inputs, **_kwargs):
        self.started_inputs.append(inputs)
        return {"turn": {"id": "a13-turn"}}


def signal(name, value, sequence, capture_ns):
    return {"format": "observable-signal-v1", "status": "observed",
            "signal_id": name, "value": value, "sequence": sequence,
            "capture_ns": capture_ns, "binding": BINDING}


def load_sources():
    guard_spec = importlib.util.spec_from_file_location("a13_guard", ROOT / "observable_signal_guard_v2.py")
    guard_module = importlib.util.module_from_spec(guard_spec); guard_spec.loader.exec_module(guard_module)
    adapter_spec = importlib.util.spec_from_file_location("a13_adapter", ROOT / "persistent_planner_adapter_v2.py")
    adapter_module = importlib.util.module_from_spec(adapter_spec); adapter_spec.loader.exec_module(adapter_module)
    tree = ast.parse(CONTROLLER.read_text(encoding="utf-8"))
    top = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    chosen = [top[name] for name in (
        "guard_spec", "ammo_guard_spec", "_typed_json_equal", "_signal_pair_matches",
        "_signal_pair_content_matches", "DoomCoverSignalPairMonitor", "build_cover_monitor",
        "latest_soft_event_summary", "begin_model_turn", "prepare_action_admission")]
    from final_action_admission_v2 import record_action_validity
    namespace = {"json": json, "time": time,
                 "ObservableSignalGuard": guard_module.ObservableSignalGuard,
                 "ObservableSignalPolicyMonitor": guard_module.ObservableSignalPolicyMonitor,
                 "MAX_AUTHORED_HEALTH_LOSS": 20,
                 "build_action_contract": build_contract,
                 "bindings_equal_exact": bindings_equal_exact,
                 "SNAPSHOT_FORMAT": SNAPSHOT_FORMAT,
                 "evaluate_action_validity": evaluate_action_validity,
                 "record_action_validity": record_action_validity,
                 "win": lambda path: str(path)}
    exec(compile(ast.Module(body=chosen, type_ignores=[]), str(CONTROLLER), "exec"), namespace)
    return namespace, adapter_module.PersistentPlannerAdapter


class FeedbackActionGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.functions, cls.Adapter = load_sources()

    def test_soft_ammo_feedback_reaches_prompt_and_fresh_action_gate_rejects_fire(self):
        f = self.functions
        health_reader, ammo_reader = SignalReader("health"), SignalReader("ammo")
        source = {"event": "observation", "sequence": 10,
                  "capture_ns": 1_000_000_000, "pointer_binding": BINDING,
                  "health": 70, "ammo": 6}
        monitor, _admission = f["build_cover_monitor"](
            health_reader, source,
            {"signal_id": "health", "critical_health_minimum": 45,
             "maximum_health_loss": 8, "max_source_age_ms": 1000},
            "a13", ammo_reader=ammo_reader, requires_ammo=True)
        typed = {"event": "typed_observation", "sequence": 11,
                 "capture_ns": 1_100_000_000, "pointer_binding": BINDING,
                 "signals": {"health": signal("health", 70, 11, 1_100_000_000),
                             "ammo": signal("ammo", 4, 11, 1_100_000_000)}}
        self.assertIsNone(monitor.observe(typed))
        decision = {"iteration": 2, "cover_policy_source_iteration": 1,
                    "cover_validity_soft_events": monitor.soft_event_count,
                    "cover_validity_latest_soft_event": monitor.latest_soft_event}
        summary = f["latest_soft_event_summary"]([decision])

        client = PlannerClient()
        planner = self.Adapter(client, model="frozen-mock", effort="low", cwd=".",
                               base_instructions="inert feedback-to-admission fixture")
        planner.start_session()
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            handle = f["begin_model_turn"](planner, Path(directory), "frame.png", [],
                                             70, 4, summary, {"type": "object"})
            prompt = client.started_inputs[0][0]["text"]
            compact = json.dumps(summary, separators=(",", ":"))
            self.assertIn("Current locally verified ammo: 4.", prompt)
            self.assertIn(compact, prompt)

            # This is a deliberately synthetic planner candidate, not a model result.
            candidate = {"commands": COMMANDS}
            terminal_receipt = decide_final_admission(
                {"turn_id": handle.turn_id, "status": "completed",
                 "answer_eligible": True, "terminal_observed_ns": 1_150_000_000},
                None, 1_160_000_000)
            source_health, source_ammo = health_reader.read(source), ammo_reader.read(source)
            current_observation = {"event": "observation", "sequence": 11,
                                   "capture_ns": 1_100_000_000,
                                   "pointer_binding": BINDING, "health": 70, "ammo": 4}
            rejected = f["prepare_action_admission"](
                terminal_receipt, candidate, AUTHORED, source_health, source_ammo,
                health_reader.read(current_observation), ammo_reader.read(current_observation),
                1_200_000_000)
            self.assertEqual(rejected["status"], "REJECTED_ACTION_NOT_CURRENT")
            self.assertEqual(rejected["action_validity"]["reason"], "ammo_minimum_failed")
            self.assertIsNone(rejected["executor_admission"])
            self.assertFalse(rejected["input_authority_admitted"])
            result = {"classification": "CONSTRUCTION_ONLY_FEEDBACK_TO_FRESH_ADMISSION",
                      "soft_event_summary": summary,
                      "prompt_has_current_ammo_4": "Current locally verified ammo: 4." in prompt,
                      "prompt_has_exact_summary": compact in prompt,
                      "synthetic_candidate": candidate,
                      "final_admission_status": rejected["status"],
                      "final_admission_reason": rejected["action_validity"]["reason"],
                      "input_authority_admitted": rejected["input_authority_admitted"],
                      "executor_admission": rejected["executor_admission"]}
            (ROOT / "results").mkdir(exist_ok=True)
            (ROOT / "results/result.json").write_text(
                json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print("A13_RESULT=" + json.dumps(result, sort_keys=True))

    def test_matching_ammo_positive_control_reaches_executor_ready_but_not_admitted(self):
        f = self.functions
        health_reader, ammo_reader = SignalReader("health"), SignalReader("ammo")
        source = {"event": "observation", "sequence": 10,
                  "capture_ns": 1_000_000_000, "pointer_binding": BINDING,
                  "health": 70, "ammo": 6}
        receipt = decide_final_admission(
            {"turn_id": "a13-control", "status": "completed", "answer_eligible": True,
             "terminal_observed_ns": 1_100_000_000}, None, 1_150_000_000)
        current = {"event": "observation", "sequence": 11,
                   "capture_ns": 1_200_000_000, "pointer_binding": BINDING,
                   "health": 70, "ammo": 6}
        result = f["prepare_action_admission"](
            receipt, {"commands": COMMANDS}, AUTHORED,
            health_reader.read(source), ammo_reader.read(source),
            health_reader.read(current), ammo_reader.read(current), 1_300_000_000)
        self.assertEqual(result["status"], "READY_FOR_FRESH_EXECUTOR_ADMISSION")
        self.assertIsNone(result["executor_admission"])
        self.assertFalse(result["input_authority_admitted"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
