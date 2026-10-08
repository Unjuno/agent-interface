import copy
import json
from pathlib import Path
import tempfile
import unittest
from test_cell import valid
import audit
PLAN=json.loads(Path("plan.json").read_text())

def bundle(root):
    for ci,spec in enumerate(PLAN["cases"]):
        c=valid();c.update({k:spec[k] for k in ("id","pair","arm")})
        shift=ci*3_000_000_000
        c['start_ns']+=shift;c['end_ns']+=shift
        for row in c['rows']:
            for key in ('due_ns','start_ns','sleep_start_ns','return_ns'):row[key]+=shift
            for key in ('cpu_start_ns','cpu_end_ns'):row[key]+=ci*2000
            for snap in (row['pre'],row['post']):
                snap['begin_ns']+=shift;snap['end_ns']+=shift;snap['process_cpu_ns']+=ci*2000
                for key in ('usage_usec','nr_periods'):snap['cpu'][key]+=ci*2000
                snap['cpu_raw']=''.join(f'{k} {v}\\n' for k,v in snap['cpu'].items()).replace('\\n','\n')
        for n in range(spec["burners"]):
            pid=10+n
            c["children"].append({"pid":pid,"ready":{"type":"ready","pid":pid,"ppid":123,"case":spec["id"],"allocation":PLAN["allocation"],"time_ns":999999999+shift},"finish":{"type":"finish","pid":pid,"reason":"parent-stop","time_ns":1999999999+shift,"iterations":1,"cpu_ns":1},"exit_code":0,"forced":False,"stderr":""})
        (root/(spec["id"]+".json")).write_text(json.dumps(c))
    limits={"cpu.max":"100000 100000","memory.max":"536870912","memory.swap.max":"0","pids.max":"64"}
    (root/"runtime.json").write_text(json.dumps({"limits":limits,"uid":501,"pid":123,"source_sha256":{}}))
    d={"status":"HOLD_NOT_SUPPORTED","pooled_ns":0.0,"paired_ns":[0.0]*6,"qualifying_pairs":0,"all_loaded_pressure":False}
    (root/"result.json").write_text(json.dumps({"allocation":PLAN["allocation"],"status":"COMPLETE","cells":12,"error":None,"decision":d,"source_unchanged":True}))

class AuditTests(unittest.TestCase):
    def test_saved_consumer_and_independent_arithmetic(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);bundle(p)
            self.assertEqual(audit.evaluate(p,PLAN,{})["status"],"HOLD_NOT_SUPPORTED")
    def test_saved_missing_cell_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);bundle(p);(p/"p0_quiet.json").unlink()
            with self.assertRaises(ValueError):audit.evaluate(p,PLAN,{})
    def test_saved_extra_file_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);bundle(p);(p/"extra.json").write_text("{}")
            with self.assertRaises(ValueError):audit.evaluate(p,PLAN,{})
    def test_symlink_required_file_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'raw';p.mkdir();bundle(p);f=p/'runtime.json';outside=p.parent/'outside.json';outside.write_bytes(f.read_bytes());f.unlink();f.symlink_to(outside)
            with self.assertRaises(ValueError):audit.evaluate(p,PLAN,{})
    def test_duplicate_json_key_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);bundle(p);f=p/'runtime.json';s=f.read_text();f.write_text('{"uid":0,'+s[1:])
            with self.assertRaises(ValueError):audit.evaluate(p,PLAN,{})
    def test_auditor_actual_limits_rejected(self):
        limits={'cpu.max':'200000 100000','memory.max':'536870912','memory.swap.max':'0','pids.max':'64'}
        with self.assertRaises(ValueError):audit.audit_runtime(lambda k:limits[k],501)
    def test_auditor_actual_uid_rejected(self):
        limits={'cpu.max':'100000 100000','memory.max':'536870912','memory.swap.max':'0','pids.max':'64'}
        with self.assertRaises(ValueError):audit.audit_runtime(lambda k:limits[k],0)
    def test_source_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);bundle(p)
            with self.assertRaises(ValueError):audit.evaluate(p,PLAN,{"a":"sha"})
    def test_crosscell_cpu_regression_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);bundle(p);f=p/'p0_loaded.json';c=json.loads(f.read_text())
            for r in c['rows']:
                r['cpu_start_ns']-=2000;r['cpu_end_ns']-=2000
                for s in (r['pre'],r['post']):
                    s['process_cpu_ns']-=2000
                    for key in ('usage_usec','nr_periods'):s['cpu'][key]-=2000
                    s['cpu_raw']=''.join(f'{k} {v}\n' for k,v in s['cpu'].items())
            f.write_text(json.dumps(c))
            with self.assertRaises(ValueError):audit.evaluate(p,PLAN,{})
    def test_self_reported_support_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);bundle(p);f=p/"result.json";v=json.loads(f.read_text());v["decision"]["status"]="SUPPORT_IMPOSED_LOAD_ONLY";f.write_text(json.dumps(v))
            with self.assertRaises(ValueError):audit.evaluate(p,PLAN,{})
if __name__=="__main__":unittest.main()
