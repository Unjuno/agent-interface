from __future__ import annotations
import importlib.util, pathlib, unittest
P=pathlib.Path(__file__).with_name('analyze_partial.py')
spec=importlib.util.spec_from_file_location('m',P); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def submit(id, keys, dur=300):
    return {'event':'command','command':{'op':'submit','id':id,'steps':[{'op':'hold','keys':keys,'duration_ms':dur}]}}
def start(id='x',t=100): return {'event':'step_started','id':id,'step':0,'operation':'hold','issued_ns':t}
def adm(key,a,k): return {'event':'input_admission','key':key,'admitted_ns':a,'input_ack_ns':k}
def term(id='x',status='cancelled',v=300,reason='cancelled'):
    return {'event':'terminal','id':id,'status':status,'release':{'verified':True,'keys_down':[],'verified_ns':v,'reason':'release'},'interruption':{'record':{'verified':True,'keys_down':[],'verified_ns':v,'reason':reason}},'steps_completed':0}

class T(unittest.TestCase):
    def one(self,e): return m.reconstruct_holds(e)[0]
    def test_zero_admission(self):
        r=self.one([submit('x',['a']),start(),term(v=250)])
        self.assertEqual(r['classification'],'zero_admission_interrupted'); self.assertEqual((r['physical_any_key_occupancy_lower_ms'],r['physical_any_key_occupancy_upper_ms']),(0.0,0.0))
    def test_partial_admission_exact_428(self):
        e=[submit('cover-4',['Down','space']),start('cover-4',55539809187659),
           {'event':'command','command':{'op':'cancel','id':'cover-4'},'received_ns':55539824423539},
           adm('Down',55539824242850,55539824580162),
           {'event':'cancel_requested','id':'cover-4','requested_ns':55539834799571},
           term('cover-4',v=55539837451978)]
        r=self.one(e); self.assertEqual(r['classification'],'partial_admission_interrupted'); self.assertEqual(r['admitted_keys'],['Down']); self.assertEqual(r['physical_any_key_occupancy_lower_ms'],0.0); self.assertEqual(r['physical_any_key_occupancy_upper_ms'],13.209)
        self.assertFalse(r['full_keyset_established'])
    def test_full_admission_no_marker(self):
        r=self.one([submit('x',['a','b']),start(t=100_000_000),adm('a',120_000_000,125_000_000),adm('b',130_000_000,135_000_000),term(v=180_000_000)])
        self.assertEqual(r['classification'],'full_admission_no_marker_interrupted'); self.assertEqual(r['physical_any_key_occupancy_upper_ms'],60.0); self.assertFalse(r['full_keyset_established'])
    def test_after_keys_held_inherited_cancel(self):
        e=[submit('x',['a']),start(),adm('a',120,125),{'event':'keys_held','id':'x','step':0,'keys':['a'],'input_ack_ns':130},
           {'event':'observation','id':'x','step':0,'capture_ns':140}, {'event':'command','command':{'op':'cancel','id':'x'},'received_ns':150},term(v=170)]
        r=self.one(e); self.assertEqual(r['classification'],'keys_held_interrupted'); self.assertEqual(r['confirmed_any_key_held_until_ns'],140); self.assertTrue(r['full_keyset_established'])
    def test_completed_inherited(self):
        e=[submit('x',['a']),start(),adm('a',120,125),{'event':'keys_held','id':'x','step':0,'keys':['a'],'input_ack_ns':130},
           {'event':'observation','id':'x','step':0,'capture_ns':140}, {'event':'observation','id':'x','step':0,'capture_ns':180},
           {'event':'step_completed','id':'x','step':0,'completed_ns':190},term('x','completed',200,'release')]
        r=self.one(e); self.assertEqual(r['classification'],'ordinary_completed_bounded'); self.assertEqual(r['confirmed_any_key_held_until_ns'],140); self.assertEqual(r['released_by_ns'],180)
    def test_missing_verified_release_rejects(self):
        e=[submit('x',['a']),start(),adm('a',120,125),{'event':'terminal','id':'x','status':'cancelled','release':{},'interruption':None}]
        with self.assertRaisesRegex(AssertionError,'no verified empty release'): m.reconstruct_holds(e)
    def test_nonprefix_admission_rejects(self):
        with self.assertRaisesRegex(AssertionError,'not a requested-key prefix'): self.one([submit('x',['a','b']),start(),adm('b',120,125),term(v=180)])
if __name__=='__main__': unittest.main()
