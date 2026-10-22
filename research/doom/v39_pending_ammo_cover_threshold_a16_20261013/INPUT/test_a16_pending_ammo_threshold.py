import ast,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from action_validity_admission_v1 import SNAPSHOT_FORMAT,evaluate_action_validity
from doom_action_validity_contract_v1 import bindings_equal_exact,build_contract
from final_action_admission_v2 import decide_final_admission,record_action_validity
from persistent_planner_adapter_v2 import PersistentPlannerAdapter
BINDING={"focus":7,"surface":9,"geometry":[0,0,1280,720]}
ACTION={"commands":[{"action":"fire","extent":"short"}]}
AUTHORED={"critical_health_minimum":45,"maximum_health_loss":8,"minimum_ammo":5,"max_current_age_ms":500}
SCHEMA={"type":"object","required":["commands"],"additionalProperties":False,"properties":{"commands":{"type":"array","minItems":1,"items":{"type":"object"}}}}
class SignalReader:
    def __init__(self,name):self.name=name
    def read(self,obs):return {"format":"observable-signal-v1","status":"observed","signal_id":self.name,"value":obs[self.name],"sequence":obs["sequence"],"capture_ns":obs["capture_ns"],"binding":obs["pointer_binding"]}
def sig(name,value,seq,capture):return {"format":"observable-signal-v1","status":"observed","signal_id":name,"value":value,"sequence":seq,"capture_ns":capture,"binding":BINDING}
def load_controller():
    spec=importlib.util.spec_from_file_location("a16_guard",ROOT/"observable_signal_guard_v2.py");guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
    tree=ast.parse((ROOT/"map01_overlap_controller_v39.py").read_text(encoding="utf-8"));top={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    names=("guard_spec","ammo_guard_spec","_typed_json_equal","_signal_pair_matches","_signal_pair_content_matches","DoomCoverSignalPairMonitor","build_cover_monitor","latest_soft_event_summary","begin_model_turn","final_admission_from_planner_result","prepare_action_admission")
    ns={"json":json,"time":__import__("time"),"ObservableSignalGuard":guard.ObservableSignalGuard,"ObservableSignalPolicyMonitor":guard.ObservableSignalPolicyMonitor,"MAX_AUTHORED_HEALTH_LOSS":20,"build_action_contract":build_contract,"bindings_equal_exact":bindings_equal_exact,"SNAPSHOT_FORMAT":SNAPSHOT_FORMAT,"evaluate_action_validity":evaluate_action_validity,"record_action_validity":record_action_validity,"decide_final_admission":decide_final_admission,"win":lambda p:str(p)}
    exec(compile(ast.Module(body=[top[n] for n in names],type_ignores=[]),str(ROOT/"map01_overlap_controller_v39.py"),"exec"),ns)
    return ns
class DelayedClient:
    def __init__(self,state,monitor,new_ammo,events):self.state=state;self.monitor=monitor;self.new_ammo=new_ammo;self.events=events;self.planner=None;self.handle=None
    def start_thread(self,**kw):return {"thread":{"id":"a16-thread"}}
    def start_turn(self,thread_id,inputs,**kw):self.events.append("turn_started");return {"turn":{"id":"a16-turn"}}
    def wait_turn_completed(self,thread_id,turn_id,timeout=120):
        obs={"event":"typed_observation","sequence":11,"capture_ns":1_200_000_000,"pointer_binding":BINDING,"signals":{"health":sig("health",70,11,1_200_000_000),"ammo":sig("ammo",self.new_ammo,11,1_200_000_000)}}
        self.state["observation"]={"event":"observation","sequence":11,"capture_ns":1_200_000_000,"pointer_binding":BINDING,"health":70,"ammo":self.new_ammo}
        self.events.append("typed_observation")
        invalidation=self.monitor.observe(obs)
        self.state["monitor_result"]=invalidation
        if invalidation is not None:
            self.events.append("monitor_invalidation")
            self.planner.interrupt(self.handle,before_transport=lambda:self.events.append("pre_interrupt_callback"))
        else:self.events.append("monitor_preserved_pending_turn")
        return {"turn":{"status":"completed","items":[{"type":"agentMessage","text":json.dumps(ACTION)}]}}
    def latest_turn_usage(self,thread_id,turn_id):return {"input_tokens":0,"output_tokens":0}
    def interrupt_turn(self,thread_id,turn_id):self.events.append("interrupt_request");return {"ack":"ok"}
class PendingAmmoThresholdTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.f=load_controller()
 def run_case(self,ammo):
    f=self.f;source={"event":"observation","sequence":10,"capture_ns":1_000_000_000,"pointer_binding":BINDING,"health":70,"ammo":6};hr=SignalReader("health");ar=SignalReader("ammo")
    monitor,_=f["build_cover_monitor"](hr,source,{"signal_id":"health","critical_health_minimum":45,"maximum_health_loss":8,"max_source_age_ms":1000},"a16",ammo_reader=ar,requires_ammo=True)
    state={"observation":source};events=[];client=DelayedClient(state,monitor,ammo,events);planner=PersistentPlannerAdapter(client,model="frozen-mock",effort="low",cwd=".",base_instructions="A16 inert boundary fixture");client.planner=planner;planner.start_session()
    with tempfile.TemporaryDirectory(dir=ROOT) as td:
      handle=f["begin_model_turn"](planner,Path(td),"frame.png",[],70,6,{},SCHEMA);client.handle=handle;result=planner.await_turn(handle)
    output={"pending_source_ammo":6,"observed_ammo":ammo,"soft_event_count":monitor.soft_event_count,"monitor_invalidation":state["monitor_result"],"turn_answer_eligible":result.answer_eligible,"turn_error":result.error,"event_order":events,"final_admission":None,"executor_admission":None,"input_authority_admitted":False}
    if result.answer_eligible:
      terminal=1_500_000_000;receipt=f["final_admission_from_planner_result"](result,terminal,None,terminal+1);fresh=state["observation"]
      admitted=f["prepare_action_admission"](receipt,result.answer,AUTHORED,hr.read(source),ar.read(source),hr.read(fresh),ar.read(fresh),terminal+2)
      output.update({"final_admission":admitted["status"],"final_reason":admitted["action_validity"]["reason"],"executor_admission":admitted["executor_admission"],"input_authority_admitted":admitted["input_authority_admitted"]})
    return output
 def test_soft_ammo_change_keeps_turn_but_fresh_gate_rejects_action(self):
    r=self.run_case(4);self.assertIsNone(r["monitor_invalidation"]);self.assertEqual(r["soft_event_count"],1);self.assertTrue(r["turn_answer_eligible"]);self.assertEqual(r["final_admission"],"REJECTED_ACTION_NOT_CURRENT");self.assertEqual(r["final_reason"],"ammo_minimum_failed");self.assertEqual(r["event_order"][-1],"monitor_preserved_pending_turn");self.assertIsNone(r["executor_admission"]);self.assertFalse(r["input_authority_admitted"]);print("A16_SOFT="+json.dumps(r,sort_keys=True))
 def test_hard_ammo_change_interrupts_and_invalidates_late_answer(self):
    r=self.run_case(0);self.assertEqual(r["monitor_invalidation"]["event"],"paired_signal_invalidation");self.assertIn("ammo:below_hard_minimum",r["monitor_invalidation"]["reason"]);self.assertFalse(r["turn_answer_eligible"]);self.assertEqual(r["event_order"][-3:], ["monitor_invalidation","pre_interrupt_callback","interrupt_request"]);self.assertIsNone(r["final_admission"]);self.assertIsNone(r["executor_admission"]);self.assertFalse(r["input_authority_admitted"]);print("A16_HARD="+json.dumps(r,sort_keys=True))
if __name__=="__main__":unittest.main(verbosity=2)
