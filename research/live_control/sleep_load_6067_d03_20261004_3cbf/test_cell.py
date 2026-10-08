import copy
import json
from pathlib import Path
import unittest
from core import validate_cell
PLAN=json.loads(Path("plan.json").read_text())

def snapshot(t,cpu):
    raw=f"usage_usec {cpu}\nnr_periods {cpu}\nnr_throttled 0\nthrottled_usec 0\n"
    return {"begin_ns":t,"end_ns":t+1,"cpu_raw":raw,"cpu":{"usage_usec":cpu,"nr_periods":cpu,"nr_throttled":0,"throttled_usec":0},"process_cpu_ns":cpu,"schedstat":{"available":False,"raw":None,"error":"missing"},"schedstats_enabled":{"available":False,"raw":None,"error":"missing"}}

def valid():
    c={"id":"p0_quiet","pair":0,"arm":"quiet","pid":123,"status":"COMPLETE","start_ns":1000000000,"end_ns":2000000000,"children":[],"rows":[]}
    for i in range(16):
        due=c["start_ns"]+200000000+i*40000000
        c["rows"].append({"index":i,"pid":123,"due_ns":due,"start_ns":due-10000,"sleep_start_ns":due-9990,"requested_ns":9990,"return_ns":due+100,"cpu_start_ns":i*100+10,"cpu_end_ns":i*100+20,"pre":snapshot(due-11000,i*100),"post":snapshot(due+101,i*100+30)})
    return c

class CellTests(unittest.TestCase):
    def check(self,c):return validate_cell(c,PLAN["cases"][0],PLAN)
    def test_accept_complete(self):self.assertEqual(self.check(valid())["delays"],[100]*16)
    def reject(self,fn):
        c=valid();fn(c)
        with self.assertRaises(ValueError):self.check(c)
    def test_drop_row(self):self.reject(lambda c:c["rows"].pop())
    def test_bool_timestamp(self):self.reject(lambda c:c["rows"][0].update(return_ns=True))
    def test_request_not_absolute(self):self.reject(lambda c:c["rows"][0].update(requested_ns=100))
    def test_wrong_deadline(self):self.reject(lambda c:c["rows"][0].update(due_ns=100))
    def test_backwards_clock(self):self.reject(lambda c:c["rows"][0].update(sleep_start_ns=3000000000))
    def test_foreign_pid(self):self.reject(lambda c:c["rows"][0].update(pid=456))
    def test_cpu_regression_between_rows(self):self.reject(lambda c:c["rows"][1].update(pre=snapshot(123,0)))
    def test_raw_counter_mismatch(self):self.reject(lambda c:c["rows"][0]["pre"]["cpu"].update(usage_usec=99))
    def test_foreign_arm(self):self.reject(lambda c:c.update(arm="loaded"))
    def test_unexpected_child(self):self.reject(lambda c:c["children"].append({"pid":5}))
    def test_missing_optional_status(self):self.reject(lambda c:c["rows"][0]["pre"].pop("schedstat"))
    def test_partial_status(self):self.reject(lambda c:c.update(status="STOP"))
    def test_float_counter_rejected(self):self.reject(lambda c:c['rows'][0]['pre']['cpu'].update(usage_usec=0.0))
    def test_float_pair_rejected(self):self.reject(lambda c:c.update(pair=0.0))
    def test_only_process_cpu_regression_rejected(self):
        def mutate(c):
            r=c['rows'][1];r['pre']['process_cpu_ns']=25;r['cpu_start_ns']=26;r['cpu_end_ns']=27;r['post']['process_cpu_ns']=28
        self.reject(mutate)
    def loaded(self):
        c=valid();s=PLAN['cases'][1];c.update({k:s[k] for k in ('id','pair','arm')})
        for pid in (10,11):c['children'].append({'pid':pid,'ready':{'type':'ready','pid':pid,'ppid':123,'case':s['id'],'allocation':PLAN['allocation'],'time_ns':999999999},'finish':{'type':'finish','pid':pid,'reason':'parent-stop','time_ns':1999999999,'iterations':1,'cpu_ns':1},'exit_code':0,'forced':False,'stderr':''})
        return c,s
    def test_complete_loaded(self):
        c,s=self.loaded();self.assertEqual(validate_cell(c,s,PLAN)['delays'],[100]*16)
    def test_child_finishes_after_cell_rejected(self):
        c,s=self.loaded();c['children'][0]['finish']['time_ns']=2000000001
        with self.assertRaises(ValueError):validate_cell(c,s,PLAN)
    def test_child_float_identity_rejected(self):
        c,s=self.loaded();c['children'][0]['ready']['pid']=10.0
        with self.assertRaises(ValueError):validate_cell(c,s,PLAN)
if __name__=="__main__":unittest.main()
