"""Hand-derived oracle tests. No X server, native input or production dispatch."""
import copy
import json
import unittest
from pathlib import Path
from auditor import audit
PLAN=json.loads((Path(__file__).parent/"PLAN.json").read_text())
def sample(tag, at, f8=False, f9=False):
    b=bytearray(32)
    for down,code in ((f8,74),(f9,75)):
        if down: b[code//8]|=1<<(code%8)
    return {"tag":tag,"query_started_ns":at,"at_ns":at+100000,"keymap":b.hex(),"buttons":0}
def receipt(at): return {"keys_down":[],"buttons_down":[],"verified":True,"monotonic_ns":at}
def deck():
    rows=[]
    for i,c in enumerate(PLAN["cells"]):
        crash=c["context"]!="healthy"; b=c["context"]=="crash_bystander"; ref=c["policy"]=="prearmed_scope"
        pid=100+i*2; sid=pid+1; code=74; owner_ready=20000000; kill=70000000 if crash else None
        cap={"cell_id":c["id"],"owner_pid":pid,"owner_nonce":c["id"]+"-owner","display":":130",
             "display_pid":800+i,"display_start_ticks":500+i,"window_id":900+i,"keys":{"F8":74},"registered_ns":5000000}
        calls=[{"kind":"press","code":74,"started_ns":15000000,"returned_ns":16000000}]
        if not crash: calls.append({"kind":"release","code":74,"started_ns":330000000,"returned_ns":331000000})
        hdown=crash; hstart=80000000 if crash else 360000000; hfinish=hstart+2000000
        restored=crash and ref; hcalls=[{"kind":"release","code":74,"started_ns":hstart+200000,"returned_ns":hstart+300000}] if restored else []
        result=receipt(hfinish-100000)
        hbefore=sample("supervisor_before",hstart-100000,hdown,b)
        hafter=sample("supervisor_after",hfinish,crash and not ref,b)
        events=[]
        if b: events.append({"kind":"press","code":75,"at_ns":1000000})
        events.append({"kind":"press","code":74,"at_ns":17000000})
        events.append({"kind":"release","code":74,"at_ns":(85000000 if restored else 250000000) if crash else 333000000})
        if b: events.append({"kind":"release","code":75,"at_ns":260000000})
        events.sort(key=lambda x:x["at_ns"])
        rows.append({**c,"error":None,"auto_repeat_disabled":True,
          "capability":cap,"display_generation":{"pid":cap["display_pid"],"start_ticks":cap["display_start_ticks"],"window_id":cap["window_id"]},
          "keycodes":{"F8":74,"F9":75},"times":{"task_go":7000000,"owner_ready":owner_ready,"kill_sent":kill,"checkpoint_anchor":kill if crash else owner_ready,
          "checkpoint":220100000,"recovery_started":240000000 if crash else 380000000},
          "owner":{"pid":pid,"nonce":cap["owner_nonce"],"program_input":{"schema":"agent-interface/program-v1","program_id":c["id"],
             "source":{"observation_seq":1,"binding_revision":0},"authority":{"lease_id":"owned-7041","expires_at_ns":2000000000},
             "terminal":{"release_all_required":True},"ops":[{"op":"focus","target":"owned"},{"op":"key_state","key":"F8","down":True},{"op":"wait_update","timeout_ms":300},{"op":"release_all"}]},
             "ready":{"at_ns":owner_ready,"held":{"F8":74},"emissions":1,"stack":["dispatch","execute","wait_gate"]},
             "native_calls":calls,"returncode":-9 if crash else 0,"completed":None if crash else {"status":"completed","admission":"accepted","execution":{"completed_ops":[0,1,2,3],"program_emissions":2,"releases":[receipt(331000000)]}} },
          "supervisor":{"pid":sid,"returncode":0,"registered":{"at_ns":6000000,"held":{},"emissions":0,"capability":cap},
             "result":{"eof_ns":73000000 if crash else 350000000,"dead_ns":74000000 if crash else 351000000,
               "death_state":"Z","before":hbefore,"after":hafter,"scope":cap["keys"] if restored else {},
               "release_started_ns":hstart,"release_returned_ns":hfinish,"receipt":result,"emissions":len(hcalls),"native_calls":hcalls}},
          "checkpoint_owner_alive":not crash,"checkpoint_supervisor_pending":not crash,
          "samples":[sample("held",21000000,True,b),sample("pre_kill",65000000,True,b)] if crash else [sample("held",21000000,True)],
          "app_events":events,"fixture_recovery":{"receipt":receipt(250000000 if crash else 390000000),"emissions":1 if crash and not ref else 0},
          "bystander_calls":[{"kind":"press","code":75},{"kind":"release","code":75}] if b else [],
          "xvfb_exit":-15})
        row=rows[-1]
        cap["owner_start_ticks"]=1000+i
        row["supervisor"]["result"]["death_start_ticks"]=cap["owner_start_ticks"]
        hr=row["supervisor"]["result"]
        hr["death_observations"]={"started_ns":hr["eof_ns"],"at_ns":hr["dead_ns"],"state":"Z","start_ticks":cap["owner_start_ticks"],"samples":[{"query_started_ns":hr["eof_ns"],"at_ns":hr["dead_ns"],"state":"Z","start_ticks":cap["owner_start_ticks"]}]}
        row["owner"]["ready"]["program_input"]=copy.deepcopy(row["owner"]["program_input"])
        row["final_emergency"]={"receipt":receipt(510000000),"emissions":0}
        if not crash:
            row["owner"]["completed"]["execution"]["waits"]=[{"operation_index":2,"requested_ms":300,"completed":True,"started_ns":19000000,"ended_ns":320000000}]
        if restored: row["samples"].append(sample("periodic",90000000,False,b))
        row["samples"].extend([sample("checkpoint",220000000,crash and not ref or not crash,b),
                              sample("after_supervisor",230000000 if crash else 370000000,crash and not ref,b),
                              sample("terminal",500000000)])
    return rows
class OracleTests(unittest.TestCase):
    def rejected(self, mutate):
        rows=deck(); mutate(rows)
        try: audit(rows,PLAN)
        except ValueError: return
        self.fail("invalid trace accepted")
    def test_empty_scope_is_not_dead_owner_release(self):
        self.assertEqual(audit(deck(),PLAN)["status"],"FAIL_EMPTY_SCOPE_AS_OWNER_RELEASE_EVIDENCE")
    def test_duplicate_cell_rejected(self): self.rejected(lambda r:r.__setitem__(-1,copy.deepcopy(r[0])))
    def test_ready_program_join_rejected(self): self.rejected(lambda r:r[0]["owner"]["ready"]["program_input"].__setitem__("program_id","foreign"))
    def test_wrong_dead_pid_generation_rejected(self): self.rejected(lambda r:r[0]["supervisor"]["result"].__setitem__("death_start_ticks",999))
    def test_live_generation_observation_rejected(self): self.rejected(lambda r:r[0]["supervisor"]["result"]["death_observations"]["samples"][0].__setitem__("start_ticks",999))
    def test_live_final_death_sample_rejected(self): self.rejected(lambda r:r[0]["supervisor"]["result"]["death_observations"]["samples"][-1].__setitem__("state","R"))
    def test_short_healthy_wait_rejected(self): self.rejected(lambda r:r[0]["owner"]["completed"]["execution"]["waits"][0].__setitem__("ended_ns",25000000))
    def test_final_emergency_intervention_rejected(self): self.rejected(lambda r:r[0]["final_emergency"].__setitem__("emissions",1))
    def test_wrong_prearmed_owner_rejected(self): self.rejected(lambda r:r[0]["capability"].__setitem__("owner_pid",999))
    def test_registration_after_press_rejected(self): self.rejected(lambda r:r[0]["supervisor"]["registered"].__setitem__("at_ns",40000000))
    def test_pre_exit_cleanup_rejected(self): self.rejected(lambda r:r[0]["supervisor"]["result"].__setitem__("dead_ns",1000000))
    def test_truncated_query_rejected(self): self.rejected(lambda r:r[0]["samples"][0].__setitem__("keymap","00"))
    def test_early_checkpoint_start_rejected(self): self.rejected(lambda r:r[1]["samples"][-3].__setitem__("query_started_ns",1))
    def test_foreign_supervisor_release_flags_scientific_fail(self):
        rows=deck(); rows[3]["supervisor"]["result"]["native_calls"][0]["code"]=75
        self.assertEqual(audit(rows,PLAN)["status"],"FAIL_REFERENCE_COLLATERAL_OR_AUTHORITY")
    def test_helper_emission_mismatch_rejected(self): self.rejected(lambda r:r[0]["supervisor"]["result"].__setitem__("emissions",2))
    def test_wrong_source_program_rejected(self): self.rejected(lambda r:r[0]["owner"]["program_input"]["ops"][1].__setitem__("key","F9"))
    def test_missing_owner_death_rejected(self): self.rejected(lambda r:r[2]["owner"].__setitem__("returncode",0))
    def test_missing_app_release_rejected(self): self.rejected(lambda r:r[0]["app_events"].pop())
    def test_non_neutral_terminal_rejected(self): self.rejected(lambda r:r[0]["samples"].__setitem__(-1,sample("terminal",500000000,True)))
    def test_postmeasure_recovery_is_not_baseline_success(self):
        rows=deck(); self.assertEqual(audit(rows,PLAN)["baseline_crash_still_down"],6)
if __name__=="__main__": unittest.main()
