from __future__ import annotations
import ast, hashlib, importlib.util, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"
CONTROLLER = SOURCE / "map01_overlap_controller_v39.py"
GUARD = SOURCE / "observable_signal_guard_v2.py"

def load_experiment_functions():
    tree = ast.parse(CONTROLLER.read_text(encoding="utf-8"))
    chosen_names = ("guard_spec", "ammo_guard_spec", "_typed_json_equal",
                    "_signal_pair_matches", "_signal_pair_content_matches",
                    "DoomCoverSignalPairMonitor", "build_cover_monitor")
    top = {node.name: node for node in tree.body
           if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    spec = importlib.util.spec_from_file_location("frozen_guard", GUARD)
    guard_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard_module)
    namespace = {"time": __import__("time"),
                 "ObservableSignalGuard": guard_module.ObservableSignalGuard,
                 "ObservableSignalPolicyMonitor": guard_module.ObservableSignalPolicyMonitor,
                 "MAX_AUTHORED_HEALTH_LOSS": 20}
    exec(compile(ast.Module(body=[top[name] for name in chosen_names], type_ignores=[]),
                 str(CONTROLLER), "exec"), namespace)
    return namespace


def pending_loop_contract_present():
    tree = ast.parse(CONTROLLER.read_text(encoding="utf-8"))
    main = next(node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == "main")
    def is_future_pending(node):
        test = node.test
        return (isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not) and
                isinstance(test.operand, ast.Call) and
                isinstance(test.operand.func, ast.Attribute) and
                test.operand.func.attr == "done" and
                isinstance(test.operand.func.value, ast.Name) and
                test.operand.func.value.id == "future")
    loops = [node for node in ast.walk(main) if isinstance(node, ast.While) and is_future_pending(node)]
    if not loops:
        return False
    for loop in loops:
        observation_wait = any(
            isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and
            node.func.id == "wait" and any(keyword.arg == "observation_monitor" and
            isinstance(keyword.value, ast.Name) and keyword.value.id == "invalidation_monitor"
            for keyword in node.keywords)
            for node in ast.walk(loop))
        invalidation_branch = False
        for node in ast.walk(loop):
            if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
                continue
            test = node.test
            left = test.left
            matches = (isinstance(left, ast.Subscript) and isinstance(left.value, ast.Name) and
                       left.value.id == "boundary" and
                       isinstance(left.slice, ast.Constant) and left.slice.value == "event" and
                       len(test.comparators) == 1 and isinstance(test.comparators[0], ast.Constant) and
                       test.comparators[0].value == "policy_invalidation")
            calls_cancel = any(isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and
                               child.func.id == "cancel_invalidated_cover"
                               for child in ast.walk(node))
            if matches and calls_cancel:
                invalidation_branch = True
        if observation_wait and invalidation_branch:
            return True
    return False

BINDING = {"focus": 7, "surface": 9, "geometry": [0, 0, 1280, 720]}
class SignalReader:
    def __init__(self, signal_id): self.signal_id = signal_id
    def read(self, observation):
        return {"format":"observable-signal-v1", "status":"observed",
                "signal_id":self.signal_id, "value":observation[self.signal_id],
                "sequence":observation["sequence"], "capture_ns":observation["capture_ns"],
                "binding":observation["pointer_binding"]}

def signal(name, value, sequence, capture_ns):
    return {"format":"observable-signal-v1", "status":"observed", "signal_id":name,
            "value":value, "sequence":sequence, "capture_ns":capture_ns, "binding":BINDING}

def run_case(current_ammo, functions):
    health_reader, ammo_reader = SignalReader("health"), SignalReader("ammo")
    source = {"event":"observation", "sequence":10, "capture_ns":1_000_000_000,
              "pointer_binding":BINDING, "health":70, "ammo":6}
    authored = {"signal_id":"health", "critical_health_minimum":45,
                "maximum_health_loss":8, "max_source_age_ms":1000}
    monitor, admission = functions["build_cover_monitor"](
        health_reader, source, authored, "pending-soft", ammo_reader=ammo_reader,
        requires_ammo=True)
    current = {"event":"typed_observation", "sequence":11, "capture_ns":1_100_000_000,
               "pointer_binding":BINDING,
               "signals":{"health":signal("health",70,11,1_100_000_000),
                          "ammo":signal("ammo",current_ammo,11,1_100_000_000)}}
    invalidation = monitor.observe(current)
    return {"source_ammo":6, "current_ammo":current_ammo,
            "next_action_minimum_ammo":5,
            "cover_guard_hard_ammo_floor":monitor.guards["ammo"].spec["hard_minimum"],
            "cover_admission":admission["status"],
            "monitor_result":None if invalidation is None else invalidation["reason"],
            "soft_event_count":monitor.soft_event_count,
            "pending_turn_cancel_signal":invalidation is not None}

checks = []
def require(name, condition):
    checks.append({"name": name, "pass": bool(condition)})
    if not condition:
        raise RuntimeError("check failed: " + name)

functions = load_experiment_functions()
loop_contract = pending_loop_contract_present()
cases = [run_case(4,functions),run_case(0,functions)]
require("pending_loop_control_flow", loop_contract)
require("soft_case_admitted", cases[0]["cover_admission"] == "admitted")
require("soft_case_below_action_floor", cases[0]["current_ammo"] < cases[0]["next_action_minimum_ammo"])
require("cover_hard_floor_is_one", cases[0]["cover_guard_hard_ammo_floor"] == 1)
require("soft_change_queued_no_invalidation", cases[0]["monitor_result"] is None and cases[0]["soft_event_count"] == 1)
require("soft_change_does_not_cancel_pending", cases[0]["pending_turn_cancel_signal"] is False)
require("hard_change_emits_invalidation", cases[1]["monitor_result"] == "ammo:below_hard_minimum")
require("hard_change_triggers_cancel_condition", cases[1]["pending_turn_cancel_signal"] is True)
result = {"schema":"issue59-pending-soft-boundary-raw-v1",
          "source_commit":"f185a9059d485a4f8d5a65e9e7f6782897f67eae",
          "controller_sha256":hashlib.sha256(CONTROLLER.read_bytes()).hexdigest(),
          "guard_sha256":hashlib.sha256(GUARD.read_bytes()).hexdigest(),
          "pending_loop_contract_present":loop_contract,
          "cases":cases,
          "scope":"exact current-main monitor functions and pending-loop control-flow inspection; synthetic paired HUD only; no live model/game/OS input/physical release",
          "checks":checks,"passed":sum(item["pass"] for item in checks),"total":len(checks)}
(ROOT/"results"/"raw.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2,sort_keys=True))


