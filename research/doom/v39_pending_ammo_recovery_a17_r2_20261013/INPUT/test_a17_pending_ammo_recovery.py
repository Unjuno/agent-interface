import ast
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from action_validity_admission_v1 import SNAPSHOT_FORMAT, evaluate_action_validity
from doom_action_validity_contract_v1 import bindings_equal_exact, build_contract
from final_action_admission_v2 import decide_final_admission, record_action_validity
from persistent_planner_adapter_v2 import PersistentPlannerAdapter

BINDING={"focus":7,"surface":9,"geometry":[0,0,1280,720]}
ACTION={"commands":[{"action":"fire","extent":"short"}]}
AUTHORED={"critical_health_minimum":45,"maximum_health_loss":8,"minimum_ammo":6,"max_current_age_ms":500}
SCHEMA={"type":"object","required":["commands"],"additionalProperties":False,"properties":{"commands":{"type":"array","minItems":1,"items":{"type":"object"}}}}

class SignalReader:
    def __init__(self,name): self.name=name
    def read(self,obs):
        return {"format":"observable-signal-v1","status":"observed","signal_id":self.name,
                "value":obs[self.name],"sequence":obs["sequence"],"capture_ns":obs["capture_ns"],"binding":obs["pointer_binding"]}

class DeterministicClient:
    def __init__(self,state,mutate): self.state=state; self.mutate=mutate; self.inputs=[]
    def start_thread(self,**kwargs): return {"thread":{"id":"a17-thread"}}
    def start_turn(self,thread_id,inputs,**kwargs): self.inputs.append(inputs); return {"turn":{"id":"a17-turn"}}
    def wait_turn_completed(self,thread_id,turn_id,timeout=120):
        self.state["observation"]={"event":"typed_observation","sequence":11,"capture_ns":1_200_000_000,
            "pointer_binding":BINDING,"health":70,"ammo":(6 if self.mutate else 4)}
        return {"turn":{"status":"completed","items":[{"type":"agentMessage","text":json.dumps(ACTION)}]}}
    def latest_turn_usage(self,thread_id,turn_id): return {"input_tokens":0,"output_tokens":0}

def load_controller():
    guard_spec=importlib.util.spec_from_file_location("a14_guard",ROOT/"observable_signal_guard_v2.py")
    guard=importlib.util.module_from_spec(guard_spec); guard_spec.loader.exec_module(guard_spec.loader and guard)
    adapter_spec=importlib.util.spec_from_file_location("a14_adapter",ROOT/"persistent_planner_adapter_v2.py")
    adapter=importlib.util.module_from_spec(adapter_spec); adapter_spec.loader.exec_module(adapter)
    tree=ast.parse((ROOT/"map01_overlap_controller_v39.py").read_text(encoding="utf-8"))
    top={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    chosen=[top[name] for name in ("final_admission_from_planner_result","prepare_action_admission","begin_model_turn")]
    ns={"decide_final_admission":decide_final_admission,"build_action_contract":build_contract,
        "bindings_equal_exact":bindings_equal_exact,"SNAPSHOT_FORMAT":SNAPSHOT_FORMAT,
        "evaluate_action_validity":evaluate_action_validity,"record_action_validity":record_action_validity,
        "win":lambda path:str(path),"json":json}
    exec(compile(ast.Module(body=chosen,type_ignores=[]),str(ROOT/"map01_overlap_controller_v39.py"),"exec"),ns)
    return ns,adapter.PersistentPlannerAdapter

class PendingAmmoStalenessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.controller,cls.Adapter=load_controller()

    def run_case(self,mutate):
        state={"observation":{"event":"observation","sequence":10,"capture_ns":1_000_000_000,
            "pointer_binding":BINDING,"health":70,"ammo":4}}
        client=DeterministicClient(state,mutate)
        planner=self.Adapter(client,model="frozen-mock",effort="low",cwd=".",base_instructions="A17 inert fixture")
        planner.start_session()
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            handle=self.controller["begin_model_turn"](planner,Path(td),"frame.png",[],70,4,{},SCHEMA)
            self.assertIn("Current locally verified ammo: 4.",client.inputs[0][0]["text"])
            result=planner.await_turn(handle)
        self.assertTrue(result.answer_eligible,result.error)
        terminal=1_500_000_000
        receipt=self.controller["final_admission_from_planner_result"](result,terminal,None,terminal+1)
        original={"sequence":10,"capture_ns":1_000_000_000,"pointer_binding":BINDING,"health":70,"ammo":4}
        health=SignalReader("health"); ammo=SignalReader("ammo")
        fresh=state["observation"]
        admitted=self.controller["prepare_action_admission"](receipt,result.answer,AUTHORED,
            health.read(original),ammo.read(original),health.read(fresh),ammo.read(fresh),terminal+2)
        return {"prompt_ammo":4,"current_ammo_after_pending_turn":fresh["ammo"],
            "current_sequence":fresh["sequence"],"answer_eligible":result.answer_eligible,
            "status":admitted["status"],"reason":admitted["action_validity"]["reason"],
            "executor_admission":admitted["executor_admission"],
            "input_authority_admitted":admitted["input_authority_admitted"]}

    def test_pending_turn_uses_recovered_current_ammo_for_returned_action(self):
        result=self.run_case(True)
        self.assertEqual(result["status"],"READY_FOR_FRESH_EXECUTOR_ADMISSION")
        self.assertEqual(result["reason"],"all_authored_observable_predicates_hold")
        self.assertIsNone(result["executor_admission"])
        self.assertFalse(result["input_authority_admitted"])
        print("A17_RECOVERED_RESULT="+json.dumps(result,sort_keys=True))

    def test_no_ammo_recovery_rejects_at_current_value(self):
        result=self.run_case(False)
        self.assertEqual(result["status"],"REJECTED_ACTION_NOT_CURRENT")
        self.assertEqual(result["reason"],"ammo_minimum_failed")
        self.assertIsNone(result["executor_admission"])
        self.assertFalse(result["input_authority_admitted"])
        print("A17_LOW_AMMO_CONTROL="+json.dumps(result,sort_keys=True))

if __name__=="__main__": unittest.main(verbosity=2)

