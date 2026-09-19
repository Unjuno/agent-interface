from __future__ import annotations
import hashlib, importlib.util, json, random, sys, types
from dataclasses import dataclass
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent.parent/'live_control'/'input_owner_v11.py'
PIN='842071284156d3ccc647f47135ee62a9e512cb56'
SEED=99020260917001
N=100000

# Test-only base preserves the relevant public v10 call ABI: release op returns None
# both when a transition was performed and when the key was already absent.
base=types.ModuleType('input_owner_v10')
class FakeBase:
    def __init__(self, mode='transition', owner_id='owner-fixed'):
        self.mode=mode; self.owner_id=owner_id; self.hidden=[]
    def call(self, operation, lease=None, key=None):
        if operation not in ('up','button_up'):
            self.hidden.append({'operation':operation,'transition':False,'delegated':True})
            return {'delegated_operation':operation,'key':key}
        if self.mode=='exception':
            self.hidden.append({'operation':operation,'transition':False,'exception':True})
            raise RuntimeError('base failure')
        performed=self.mode=='transition'
        self.hidden.append({'operation':operation,'transition':performed})
        return None
base.InputOwner=FakeBase
sys.modules['input_owner_v10']=base

spec=importlib.util.spec_from_file_location('exact_v11', SOURCE)
mod=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(mod)

@dataclass
class Lease:
    deadline:int
    intent_token:str|None

class Clock:
    def __init__(self,*vals):self.vals=list(vals)
    def __call__(self):
        if not self.vals:raise RuntimeError('clock exhausted')
        return self.vals.pop(0)

def source_check():
    b=SOURCE.read_bytes();
    return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()

def one_pair(owner_id, token, deadline, key, start, end, operation):
    lease=Lease(deadline,token)
    a=mod.InputOwner('transition',owner_id)
    mod.time.perf_counter_ns=Clock(start,end)
    ra=a.call(operation,lease,key)
    b=mod.InputOwner('noop',owner_id)
    mod.time.perf_counter_ns=Clock(start,end)
    rb=b.call(operation,lease,key)
    assert a.hidden[-1]['transition'] is True
    assert b.hidden[-1]['transition'] is False
    return ra,rb

def negative_controls():
    count=0
    x=mod.InputOwner('exception','o'); mod.time.perf_counter_ns=Clock(10)
    try:x.call('up',Lease(99,'i'),'F8')
    except RuntimeError as e:
        assert str(e)=='base failure'; count+=1
    else:raise AssertionError('exception swallowed')
    x=mod.InputOwner('transition','o'); mod.time.perf_counter_ns=Clock(1,2)
    got=x.call('down',Lease(99,'i'),'F8')
    assert got=={'delegated_operation':'down','key':'F8'}; count+=1
    x=mod.InputOwner('transition','o'); mod.time.perf_counter_ns=Clock(200,100)
    try:x.call('up',Lease(999,'i'),'F8')
    except RuntimeError as e:
        assert 'clock moved backwards' in str(e); count+=1
    else:raise AssertionError('clock reversal accepted')
    return count

def main():
    assert source_check()==PIN
    neg=negative_controls()
    rng=random.Random(SEED)
    mismatches=0; semantic_false_claims=0
    h=hashlib.sha256(); sample=None
    for i in range(N):
        start=rng.randrange(1,10**12); width=rng.randrange(0,1000000); end=start+width
        deadline=end+rng.randrange(0,1000000)
        token=rng.choice([None,f'intent-{rng.randrange(1000)}'])
        owner=f'owner-{rng.randrange(1000)}'; key=rng.choice(['F8','Left','Right','space'])
        operation=rng.choice(['up','button_up'])
        if operation=='button_up': key=rng.choice([1,2,3])
        ra,rb=one_pair(owner,token,deadline,key,start,end,operation)
        if ra!=rb:mismatches+=1
        if rb.get('release_transition_interval_ns')==[start,end] and rb.get('x11_release_and_sync_completed_before_return') is True:
            semantic_false_claims+=1
        if sample is None: sample={'transition':ra,'noop':rb}
        h.update(json.dumps([i,ra,rb],sort_keys=True,separators=(',',':')).encode())
    result={
      'decision':'PASS_NOOP_RELEASE_RPC_ALIAS_SCOPED' if mismatches==0 and semantic_false_claims==N else 'FAIL',
      'seed':SEED,'pairs':N,'receipt_mismatches':mismatches,
      'noop_receipts_with_transition_shaped_claims':semantic_false_claims,
      'negative_controls_passed':neg,'source_blob':source_check(),
      'digest_sha256':h.hexdigest(),'sample':sample,
    }
    (HERE/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
