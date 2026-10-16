#!/usr/bin/env python3
import copy, json, tempfile, unittest
from pathlib import Path
import audit

class TestAuditMutations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=Path(__file__).resolve().parent;cls.plan=json.loads((cls.root/'prereg.json').read_text()) if (cls.root/'prereg.json').exists() else None
    def synthetic(self):
        p=self.plan; import base64,hashlib
        recs=[]
        for case in p['schedule']:
            pix=(b'\x32\x32\xdc\x00'*case['count'])+(b'\x10\x10\x10\x00'*(1024-case['count']))
            dg=hashlib.sha256(pix).hexdigest(); rows=[]
            for i in range(32):
                due=10_000_000+i*2_000_000; off=i*2_000_000
                rows.append({'due_ns':due,'python_before_ns':due+10,'c_enter_ns':due+20,'x_before_ns':due+30,'x_after_ns':due+130,'c_exit_ns':due+140,'python_return_ns':due+(5_000_140 if case['arm']=='gil5ms' else 1_000_140),'bytes_ready_ns':due+(5_000_150 if case['arm']=='gil5ms' else 1_000_150),'x_thread_cpu_ns':50,'pixel_digest':dg})
            rows_sha256=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            recs.append({'case':case,'rows':rows,'rows_sha256':rows_sha256,'pixels':{dg:base64.b64encode(pix).decode()},'switch_interval':0.005 if case['arm']=='gil5ms' else 0.001,'observer_affinity':[p['cpus']['observer']],'load':{'before':{'ticks':1,'affinity':[p['cpus']['competitor']],'alive':True},'after':{'ticks':2,'affinity':[p['cpus']['competitor']],'alive':True},'cleaned':True}})
        raw={'task':p['task'],'mode':'formal','base':p['base'],'sources':p['sources'],'binary_sha256':p['binary_sha256'],'records':recs,'errors':[],'server':{'reaped':True}}
        raw['summary']=audit.validate({**raw,'summary':{}},p,self.root)['derived'];return raw
    def test_mutations_rejected(self):
        raw=self.synthetic(); self.assertTrue(audit.validate(raw,self.plan,self.root)['pass'])
        muts=[]
        x=copy.deepcopy(raw);x['records'][0]['rows'][0]['python_return_ns']-=100;muts.append(x)
        x=copy.deepcopy(raw);x['records'][0]['switch_interval']=0.002;muts.append(x)
        x=copy.deepcopy(raw);x['records'][0]['load']['after']['affinity']=[self.plan['cpus']['observer']];muts.append(x)
        x=copy.deepcopy(raw);x['records'][0]['pixels'][next(iter(x['records'][0]['pixels']))]='AAAA';muts.append(x)
        x=copy.deepcopy(raw);x['summary']['decision']='BOGUS';muts.append(x)
        for m in muts:self.assertFalse(audit.validate(m,self.plan,self.root)['pass'])
if __name__=='__main__':unittest.main()
