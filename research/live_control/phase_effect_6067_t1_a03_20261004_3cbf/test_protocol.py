import copy
import json
import hashlib
import unittest
from pathlib import Path
from protocol import cases_for, admit_stage
from protocol import REQUIRED_SOURCE,CONTROL_NAMES
F=json.loads(Path(__file__).with_name('fixture.json').read_text())
PINS={name:'1'*64 for name in REQUIRED_SOURCE}

class Protocol(unittest.TestCase):
    def test_readiness_exact_five_conditions_not_formal_cells(self):
        got=cases_for('readiness',F)
        self.assertEqual([s['kind'] for s in got],['dark','persistent','pulse','pulse','pulse'])
        self.assertEqual([s['width_ms'] for s in got[2:]],[10,20,30])
        self.assertEqual([s['phase'] for s in got[2:]],[0,0,0])
        self.assertTrue(all(s['offsets']==[0,0,0,0] for s in got))
        self.assertEqual([s['id'] for s in got],['r000','r001','r002','r003','r004'])
    def test_formal_preserves_complete_order_and_allocation(self):
        self.assertEqual(cases_for('formal',F),F['cases'])
        with self.assertRaises(ValueError):cases_for('construction',F)
    def test_formal_requires_independently_saved_readiness_hash(self):
        freeze={'mode':'formal','allocation':F['allocation'],'source_sha256':PINS}
        with self.assertRaises(ValueError):admit_stage(freeze,'formal',PINS,F)
        freeze['qualified_readiness']={'status':'PASS_READINESS_SCOPED','result_sha256':'2'*64,'allocation':'PHASE-EFFECT-6067-A03-READINESS-20261004-3CBF'}
        result={'status':'PASS_READINESS_SCOPED','allocation':freeze['qualified_readiness']['allocation'],
                'mode':'readiness','cells':5,'captures':40,'input_events':0,'model_calls':0,
                'source_sha256':PINS,'controls':[{'name':n,'rejected':True} for n in CONTROL_NAMES],
                'auditor_cgroups':{'cpu.max':'100000 100000','memory.max':'536870912','memory.swap.max':'0','pids.max':'64'},
                'rows':[
                    {'id':'r000','kind':'dark','schedule':'fixed','offsets':[0]*4,'stable_ids':[],
                     'boundary_hits':0,'unknown_frames':0,'captures_checked':8},
                    {'id':'r001','kind':'persistent','schedule':'fixed','offsets':[0]*4,'stable_ids':[1],
                     'boundary_hits':0,'unknown_frames':0,'captures_checked':8}]+[
                    {'id':f'r{i:03}','kind':'pulse','schedule':'fixed','offsets':[0]*4,'phase':0,
                     'width_ms':w,'stable_ids':list(range(1,9)),'boundary_hits':0,
                     'unknown_frames':0,'captures_checked':8} for i,w in enumerate((10,20,30),2)]}
        raw=json.dumps(result,sort_keys=True).encode()
        freeze['qualified_readiness']['result_sha256']=hashlib.sha256(raw).hexdigest()
        with self.assertRaises(ValueError):admit_stage(freeze,'formal',PINS,F)
        admit_stage(freeze,'formal',PINS,F,raw)
        with self.assertRaises(ValueError):admit_stage(freeze,'formal',PINS,F,raw+b' ')
        freeze['qualified_readiness']['status']='HOLD_NOT_REPRODUCED'
        with self.assertRaises(ValueError):admit_stage(freeze,'formal',PINS,F)
    def test_readiness_source_and_mode_mismatch_rejected(self):
        f={'mode':'readiness','allocation':'PHASE-EFFECT-6067-A03-READINESS-20261004-3CBF','source_sha256':PINS}
        admit_stage(f,'readiness',PINS,F)
        with self.assertRaises(ValueError):admit_stage(f,'readiness',{'a.py':'3'*64},F)
        with self.assertRaises(ValueError):admit_stage(f,'formal',{'a.py':'1'*64},F)
        with self.assertRaises(ValueError):admit_stage({**f,'source_sha256':{}},'readiness',{},F)
        extra={**PINS,'undeclared.py':'4'*64}
        with self.assertRaises(ValueError):admit_stage({**f,'source_sha256':extra},'readiness',extra,F)

if __name__=='__main__':unittest.main()
