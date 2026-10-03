"""Hand-derived saved records, never Xlib or a scientific cell."""
import copy
import unittest
from auditor import audit

def fixture():
    plan={"cells":[],"stall_after_request_ns":400_000_000,"checkpoint_after_request_ns":150_000_000,"f9_hold_ms":40}
    rows=[]
    for repeat in (1,2,3):
        for blocked in (False,True):
            for policy in ("cleanup_only","before_positive_gate"):
                cell={"id":f"r{repeat}-{policy}-{int(blocked)}","repeat":repeat,"blocked":blocked,"policy":policy}
                plan["cells"].append(cell); denied=blocked and policy=="before_positive_gate"
                png={"path":"/out/image.png","sha256":"b"*64,"bytes":100,"width":280,"height":180,
                     "source_raw_sha256":"a"*64,"timing_ns":{"started":81_000_000,"converted":82_000_000,
                     "encoded":85_000_000,"written":502_000_000 if blocked else 93_000_000,"hashed":503_000_000 if blocked else 94_000_000}}
                source={"sha256":"a"*64,"capture_started_ns":79_000_000,"capture_ended_ns":80_000_000,"operation_index":2}
                release={"verified":True,"keys_down":[],"buttons_down":[]}
                program={"schema":"agent-interface/program-v1","program_id":cell["id"],
                    "source":{"observation_seq":1,"binding_revision":0},
                    "authority":{"lease_id":"owned-7010","expires_at_ns":2_000_000_000},
                    "terminal":{"release_all_required":True},"ops":[{"op":"focus","target":"owned"},
                    {"op":"key_state","key":"F8","down":True},
                    {"op":"observe","frame":"window_client","x":0,"y":0,"w":280,"h":180},
                    {"op":"key_state","key":"F9","down":True},{"op":"wait_update","timeout_ms":40},{"op":"release_all"}]}
                def sample(at,tag,bits):
                    key=bytearray(32); key[9]=bits
                    return {"at_ns":at,"query_started_ns":at-10000,"tag":tag,"keymap":key.hex(),"buttons":0}
                samples=[sample(90_000_000,"writer_entry",4),sample(250_000_000,"checkpoint",0),sample(550_000_000,"terminal",0)]
                if not denied: samples.append(sample(505_000_000 if blocked else 110_000_000,"periodic",8 if blocked else 12))
                if blocked: samples.append(sample(106_000_000,"periodic",0))
                samples.sort(key=lambda s:s["at_ns"])
                events=[{"kind":"press","keycode":74,"at_ns":80_000_000}]
                if blocked: events.append({"kind":"release","keycode":74,"at_ns":105_000_000})
                if not denied:
                    events.append({"kind":"press","keycode":75,"at_ns":505_000_000 if blocked else 96_000_000})
                    if not blocked: events.append({"kind":"release","keycode":74,"at_ns":140_000_000})
                    events.append({"kind":"release","keycode":75,"at_ns":545_000_000 if blocked else 142_000_000})
                inputs=[{"key":"F8","down":True,"started_ns":75_000_000,"checked_ns":75_100_000,"returned_ns":78_000_000,
                         "revoked_at_check":False,"native_called":True,"refused":False},
                        {"key":"F9","down":True,"started_ns":504_000_000 if blocked else 95_000_000,
                         "checked_ns":504_100_000 if blocked else 95_100_000,"returned_ns":504_500_000 if blocked else 95_500_000,
                         "revoked_at_check":blocked,"native_called":not denied,"refused":denied}]
                calls=[{"thread":"program","started_ns":546_000_000 if blocked else 135_000_000,
                        "returned_ns":548_000_000 if blocked else 143_000_000,"result":release,"emissions_before":2 if denied else 3 if blocked else 2,
                        "emissions_after":2 if denied else 4}]
                if blocked: calls.insert(0,{"thread":"cleanup-only","started_ns":102_000_000,"returned_ns":105_000_000,
                                          "result":release,"emissions_before":1,"emissions_after":2})
                execution={"completed_ops":[0,1,2] if denied else [0,1,2,3,4,5],"program_emissions":2 if denied else 4,
                           "observations":[{**source,"artifact":png}],"releases":[release]}
                if denied: execution.update(failed_op=3,error="RESEARCH_ONLY_REVOKED_POSITIVE_INPUT")
                row={**cell,"error":None,"auto_repeat_disabled":True,"xvfb_exit":0,"keycodes":{"F8":74,"F9":75},
                     "times":{"write_enter":91_000_000,"write_resume":500_000_000 if blocked else 92_000_000,
                              "write_return":501_000_000 if blocked else 93_000_000,"program_return":549_000_000 if blocked else 144_000_000,
                              "checkpoint_anchor":100_000_000,"checkpoint":250_000_000},
                     "checkpoint":{"sample_at_ns":250_000_000,"down":False,"writer_pending":blocked,"program_pending":blocked},
                     "samples":samples,"app_events":events,"terminal":{"keymap":bytes(32).hex(),"buttons":0},
                     "program_input":program,"program":{"status":"execution_failed" if denied else "completed","admission":"accepted",
                     "recovery_required":False,"execution":execution},"source_capture":source,
                     "png":{**png,"file":"image.png","header":"89504e470d0a1a0a"},
                     "png_write_payload":{"bytes":100,"sha256":"b"*64,"header":"89504e470d0a1a0a"},
                     "write_stack":["capture","write","write"],"release_calls":calls,"positive_input_calls":inputs,
                     "revoked":blocked}
                if blocked:
                    row["times"].update(cancel_request=100_000_000,revoked_set=101_000_000,resume_signal=499_900_000)
                    row["cleanup_response"]=release
                inputs[0].update(emissions_before=0,emissions_after=1)
                inputs[1].update(emissions_before=2 if blocked else 1,emissions_after=2 if denied else 3 if blocked else 2)
                rows.append(row)
    return rows,plan

class RevocationOracleTests(unittest.TestCase):
    def test_preserves_cleanup_only_counterexample(self):
        rows,plan=fixture()
        self.assertEqual(audit(rows,plan)["status"],"FAIL_CLEANUP_ONLY_COMPOSITION_LATE_INPUT_SCOPED")
    def test_duplicate_rejected(self):
        rows,plan=fixture(); rows[1]=copy.deepcopy(rows[0])
        with self.assertRaises(ValueError): audit(rows,plan)
    def test_observation_summary_substitution_rejected(self):
        rows,plan=fixture(); rows[0]["source_capture"]["sha256"]="c"*64
        with self.assertRaises(ValueError): audit(rows,plan)
    def test_missing_cleanup_call_rejected(self):
        rows,plan=fixture(); rows[2]["release_calls"].pop(0)
        with self.assertRaises(ValueError): audit(rows,plan)
    def test_impossible_query_bracket_rejected(self):
        rows,plan=fixture(); rows[0]["samples"][0]["query_started_ns"]+=10**9
        with self.assertRaises(ValueError): audit(rows,plan)
    def test_unverified_release_rejected(self):
        rows,plan=fixture(); rows[0]["release_calls"][0]["result"]["verified"]=False
        with self.assertRaises(ValueError): audit(rows,plan)
    def test_short_fault_rejected(self):
        rows,plan=fixture(); rows[2]["times"]["write_resume"]=110_000_000
        with self.assertRaises(ValueError): audit(rows,plan)
    def test_muted_healthy_program_rejected(self):
        rows,plan=fixture(); rows[0]["app_events"].pop(1)
        with self.assertRaises(ValueError): audit(rows,plan)
    def test_reference_native_call_rejected(self):
        rows,plan=fixture(); rows[3]["positive_input_calls"][1]["native_called"]=True
        with self.assertRaises(ValueError): audit(rows,plan)
    def test_false_terminal_rejected(self):
        rows,plan=fixture(); rows[0]["terminal"]["buttons"]=256
        with self.assertRaises(ValueError): audit(rows,plan)
    def test_early_checkpoint_rejected(self):
        rows,plan=fixture(); rows[2]["times"]["checkpoint"]=110_000_000
        with self.assertRaises(ValueError): audit(rows,plan)
    def test_false_completed_reference_rejected(self):
        rows,plan=fixture(); rows[3]["program"]["status"]="completed"
        with self.assertRaises(ValueError): audit(rows,plan)
    def test_missing_program_release_join_rejected(self):
        rows,plan=fixture(); rows[2]["release_calls"].pop(1)
        with self.assertRaises(ValueError): audit(rows,plan)
    def test_broken_owner_emission_chain_rejected(self):
        rows,plan=fixture(); rows[2]["positive_input_calls"][1]["emissions_before"]=7
        with self.assertRaises(ValueError): audit(rows,plan)

if __name__=="__main__": unittest.main()
