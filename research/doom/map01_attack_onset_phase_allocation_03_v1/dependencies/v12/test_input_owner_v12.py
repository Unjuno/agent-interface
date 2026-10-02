import importlib.util, sys, time, threading, types, unittest
from pathlib import Path
from Xlib import X

ROOT=Path(__file__).parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod

class Focus:
    def __init__(self,i): self.id=i
class Pointer:
    mask=0; root_x=0; root_y=0
class Root:
    def query_pointer(self): return Pointer()
class Screen:
    def __init__(self): self.root=Root()
class FakeDisplay:
    def __init__(self, config=None):
        c=config or {}; self.physical=set(c.get('physical',()))
        self.query_i=0; self.query_fail_on=set(c.get('query_fail_on',()))
        self.sync_i=0; self.sync_fail_on=set(c.get('sync_fail_on',()))
        self.inject_i=0; self.inject_fail_on=set(c.get('inject_fail_on',()))
        self.injections=[]; self.closed=False; self.root=Root()
    def get_input_focus(self): return types.SimpleNamespace(focus=Focus(42))
    def keysym_to_keycode(self, sym): return 74 if sym else 0
    def query_keymap(self):
        self.query_i += 1
        if self.query_i in self.query_fail_on: raise RuntimeError('sample failure')
        out=bytearray(32)
        for code in self.physical: out[code//8] |= (1 << (code%8))
        return out
    def sync(self):
        self.sync_i += 1
        if self.sync_i in self.sync_fail_on: raise RuntimeError('sync failure')
    def screen(self): return Screen()
    def close(self): self.closed=True

class DisplayModule:
    def __init__(self, config=None): self.config=config or {}; self.instances=[]
    def Display(self,name):
        d=FakeDisplay(self.config); self.instances.append(d); return d

class XTestModule:
    def fake_input(self,d,event_type,code=None,**kwargs):
        d.inject_i += 1
        if d.inject_i in d.inject_fail_on: raise RuntimeError('inject failure')
        d.injections.append((event_type,code))
        if event_type==X.KeyPress: d.physical.add(code)
        elif event_type==X.KeyRelease: d.physical.discard(code)

class Lease:
    def __init__(self, intent='intentA', focus=42, valid=True, cancelled=False, deadline=None):
        self.expected_focus=focus; self.focus_invalid=False
        self.deadline=deadline if deadline is not None else time.perf_counter_ns()+10_000_000_000
        self.cancel=threading.Event(); self.valid=valid
        if cancelled: self.cancel.set()
        if intent is not None: self.intent_token=intent
    def check(self):
        if not self.valid: raise RuntimeError('lease invalid')

class Harness:
    def __init__(self,module,config=None):
        self.mod=module; self.dm=DisplayModule(config); self.mod.display=self.dm; self.mod.xtest=XTestModule()
        self.owner=self.mod.InputOwner(':fake'); self.d=self.dm.instances[0]
    def close(self):
        try: self.owner.close()
        except Exception: pass

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0,str(ROOT))
        cls.v10=load('input_owner_v10_under_test',ROOT/'input_owner_v10.py')
        cls.v12=load('input_owner_v12_under_test',ROOT/'input_owner_v12.py')

    def matched(self,config=None):
        return Harness(self.v10,config),Harness(self.v12,config)

    def test_clean_down_up_and_composable_identity(self):
        a,b=self.matched(); deadline=time.perf_counter_ns()+10_000_000_000; la=Lease(deadline=deadline); lb=Lease(deadline=deadline)
        try:
            r10=a.owner.call('down',la,'F8'); r12=b.owner.call('down',lb,'F8')
            for k in ('event','key','valid_until_ns'): self.assertEqual(r10[k],r12[k])
            m=r12['physical_key_measurement']; self.assertEqual(m['classification'],'CONFIRMED_PHYSICAL_DOWN')
            self.assertEqual(m['identity_status'],'MINTED'); aid=m['actuation_id']; self.assertTrue(aid)
            self.assertIsNotNone(m['bracket']['physical_down_interval']); self.assertEqual(m['adapter_edge']['actuation_id'],aid)
            self.assertIsNone(a.owner.call('up',la,'F8'))
            u=b.owner.call('up',lb,'F8')['physical_key_measurement']
            self.assertEqual(u['classification'],'CONFIRMED_PHYSICAL_UP'); self.assertEqual(u['identity_status'],'RETIRED')
            self.assertEqual(u['actuation_id'],aid); self.assertEqual(u['adapter_edge']['actuation_id'],aid)
            self.assertEqual(a.d.injections,b.d.injections); self.assertEqual(a.d.physical,b.d.physical)
        finally: a.close(); b.close()

    def test_repeated_down_reuses_id_without_new_interval(self):
        h=Harness(self.v12); l=Lease()
        try:
            one=h.owner.call('down',l,'F8')['physical_key_measurement']; two=h.owner.call('down',l,'F8')['physical_key_measurement']
            self.assertEqual(one['identity_status'],'MINTED'); self.assertEqual(two['identity_status'],'ACTIVE_REUSED')
            self.assertEqual(one['actuation_id'],two['actuation_id']); self.assertEqual(two['classification'],'OWNER_ALREADY_HELD')
            self.assertIsNone(two['bracket']['physical_down_interval']); self.assertEqual(two['adapter_edge']['actuation_id'],one['actuation_id'])
        finally: h.close()

    def test_sequential_holds_advance_generation(self):
        h=Harness(self.v12); l=Lease()
        try:
            a=h.owner.call('down',l,'F8')['physical_key_measurement']['actuation_id']
            h.owner.call('up',l,'F8')
            b=h.owner.call('down',l,'F8')['physical_key_measurement']['actuation_id']
            self.assertNotEqual(a,b); self.assertIn(':g1:',a); self.assertIn(':g2:',b)
        finally: h.close()

    def test_noop_up_already_up_no_identity(self):
        a,b=self.matched(); deadline=time.perf_counter_ns()+10_000_000_000; la=Lease(deadline=deadline); lb=Lease(deadline=deadline)
        try:
            self.assertIsNone(a.owner.call('up',la,'F8'))
            m=b.owner.call('up',lb,'F8')['physical_key_measurement']
            self.assertEqual(m['classification'],'NOOP_ALREADY_UP'); self.assertIsNone(m['actuation_id']); self.assertIsNone(m['adapter_edge'])
            self.assertEqual(a.d.injections,b.d.injections)
        finally:a.close();b.close()

    def test_preexisting_physical_down_does_not_mint(self):
        h=Harness(self.v12,{'physical':{74}}); l=Lease()
        try:
            m=h.owner.call('down',l,'F8')['physical_key_measurement']
            self.assertEqual(m['classification'],'PREEXISTING_PHYSICAL_DOWN'); self.assertEqual(m['identity_status'],'UNCONFIRMED_DOWN_NO_ID')
            self.assertIsNone(m['actuation_id']); self.assertIsNone(m['adapter_edge'])
        finally:h.close()

    def test_foreign_up_rejects_before_sampling(self):
        h=Harness(self.v12); a=Lease('A'); b=Lease('B')
        try:
            h.owner.call('down',a,'F8'); q=h.d.query_i
            with self.assertRaisesRegex(ValueError,'another intent|key belongs'):
                h.owner.call('up',b,'F8')
            self.assertEqual(h.d.query_i,q)
        finally:h.close()

    def test_sample_failure_does_not_change_down_control(self):
        a=Harness(self.v10); b=Harness(self.v12,{'query_fail_on':{1}}); deadline=time.perf_counter_ns()+10_000_000_000; la=Lease(deadline=deadline); lb=Lease(deadline=deadline)
        try:
            r10=a.owner.call('down',la,'F8'); r12=b.owner.call('down',lb,'F8')
            self.assertEqual(r10['event'],r12['event']); self.assertEqual(a.d.injections,b.d.injections); self.assertEqual(a.d.physical,b.d.physical)
            m=r12['physical_key_measurement']; self.assertEqual(m['classification'],'PHYSICAL_SAMPLE_UNAVAILABLE'); self.assertIsNone(m['actuation_id']); self.assertIsNone(m['adapter_edge'])
        finally:a.close();b.close()

    def test_missing_intent_does_not_reject_but_blocks_lineage(self):
        h=Harness(self.v12); l=Lease(intent=None)
        try:
            r=h.owner.call('down',l,'F8'); m=r['physical_key_measurement']
            self.assertEqual(m['classification'],'CONFIRMED_PHYSICAL_DOWN'); self.assertEqual(m['identity_status'],'LINEAGE_UNAVAILABLE')
            self.assertIsNone(m['bracket']); self.assertIsNone(m['actuation_id']); self.assertIsNone(m['adapter_edge'])
        finally:h.close()

    def test_sync_failure_matches_control_error_and_no_receipt(self):
        a=Harness(self.v10,{'sync_fail_on':{1}}); b=Harness(self.v12,{'sync_fail_on':{1}}); deadline=time.perf_counter_ns()+10_000_000_000; la=Lease(deadline=deadline); lb=Lease(deadline=deadline)
        try:
            with self.assertRaisesRegex(RuntimeError,'sync failure'): a.owner.call('down',la,'F8')
            with self.assertRaisesRegex(RuntimeError,'sync failure'): b.owner.call('down',lb,'F8')
            self.assertEqual(a.d.injections,b.d.injections); self.assertEqual(a.d.physical,b.d.physical)
        finally:a.close();b.close()

    def test_verified_cleanup_terminates_identity_without_edge_receipt(self):
        h=Harness(self.v12); l=Lease()
        try:
            aid1=h.owner.call('down',l,'F8')['physical_key_measurement']['actuation_id']
            rec=h.owner.call('release',l)
            self.assertEqual(rec['event'],'owner_release'); self.assertTrue(rec['verified']); self.assertNotIn('physical_up_interval',rec)
            aid2=h.owner.call('down',l,'F8')['physical_key_measurement']['actuation_id']
            self.assertNotEqual(aid1,aid2); self.assertIn(':g2:',aid2)
        finally:h.close()

if __name__=='__main__': unittest.main(verbosity=2)
