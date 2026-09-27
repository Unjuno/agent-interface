import importlib.util
import queue
import sys
import types
from pathlib import Path

HERE=Path(__file__).resolve().parent

class FakeProcess:
    def __init__(self):
        self.stderr=types.SimpleNamespace(read=lambda:'')
    def poll(self): return None


def load_with_fakes():
    base=types.ModuleType('map01_recovery_cover_matched_v2_runner')
    class SessionError(RuntimeError): pass
    class JsonSession:
        def __init__(self, command):
            self.queue=queue.Queue(); self.process=FakeProcess()
    base.JsonSession=JsonSession;base.SessionError=SessionError
    base.ALLOCATION_ID='old';base.EXPECTED_WORKFLOW_PATH='old';base.fallback_input_bounds=None;base.main=lambda:None
    measure=types.ModuleType('map01_recovery_cover_mechanism_v4_measurement'); measure.fallback_input_bounds=lambda *a: {'valid':True}
    sys.modules['map01_recovery_cover_matched_v2_runner']=base
    sys.modules['map01_recovery_cover_mechanism_v4_measurement']=measure
    spec=importlib.util.spec_from_file_location('v5',HERE/'map01_recovery_cover_mechanism_v5_runner.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod,base


def test_configure_identity():
    mod,base=load_with_fakes(); got=mod.configure()
    assert got is base
    assert base.ALLOCATION_ID=='map01-recovery-cover-mechanism-live-v5-01'
    assert base.EXPECTED_WORKFLOW_PATH=='.github/workflows/map01-recovery-cover-mechanism-live-v5-01.yml'


def test_wait_preserves_terminal_across_release_wait():
    mod,base=load_with_fakes();mod.configure();s=base.JsonSession([])
    s.queue.put({'event':'terminal','id':'p','status':'cancelled'})
    s.queue.put({'event':'input_released','id':'other'})
    try:
        s.wait(lambda r:r.get('event')=='input_released' and r.get('id')=='p', timeout=.03)
    except TimeoutError:
        pass
    else: raise AssertionError('negative wait unexpectedly matched')
    row=s.wait(lambda r:r.get('event')=='terminal' and r.get('id')=='p', timeout=.03)
    assert row['status']=='cancelled'


def test_wait_preserves_cancel_requested_then_terminal():
    mod,base=load_with_fakes();mod.configure();s=base.JsonSession([])
    rows=[
        {'event':'observation'},
        {'event':'cancel_requested','id':'p'},
        {'event':'terminal','id':'p'},
    ]
    for r in rows:s.queue.put(r)
    c=s.wait(lambda r:r.get('event')=='cancel_requested' and r.get('id')=='p',timeout=.03)
    assert c['event']=='cancel_requested'
    t=s.wait(lambda r:r.get('event')=='terminal' and r.get('id')=='p',timeout=.03)
    assert t['event']=='terminal'


def test_wait_preserves_ordered_unmatched_events():
    mod,base=load_with_fakes();mod.configure();s=base.JsonSession([])
    for i in range(5):s.queue.put({'event':'noise','i':i})
    s.queue.put({'event':'target'})
    assert s.wait(lambda r:r.get('event')=='target',timeout=.03)['event']=='target'
    got=[s.wait(lambda r,i=i:r.get('event')=='noise' and r.get('i')==i,timeout=.03)['i'] for i in range(5)]
    assert got==list(range(5))

if __name__=='__main__':
    tests=sorted((n,f) for n,f in globals().items() if n.startswith('test_'))
    for n,f in tests:f();print('PASS',n)
    print('PASS total',len(tests))
