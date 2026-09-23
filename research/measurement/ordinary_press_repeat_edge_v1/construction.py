from __future__ import annotations
from dataclasses import dataclass
import hashlib,json,random,sys,time

BASE='4b106a9b549fc3499d39ef2c7e3367d95a6c736c'
V10_BLOB='341b3c01649943ddaad5f28431a792c4889cc36e'
SEED=100120260917001
N=100_000

@dataclass(frozen=True)
class Lease:
    lease_id:str
    deadline:int

class FakeDownCore:
    """Information-flow model of exact v10 ordinary down branch after guards pass."""
    def __init__(self, *, already_held:bool, same_lease:bool=True, key_available:bool=True, sync_ok:bool=True):
        self.already_held=already_held; self.same_lease=same_lease
        self.key_available=key_available; self.sync_ok=sync_ok
        self.press_count=0; self.sync_count=0

    def call_down(self,key:str,lease:Lease,admitted_ns:int,ack_ns:int):
        if not isinstance(key,str) or not key: raise ValueError('malformed key')
        if not self.key_available: raise ValueError('key unavailable on input owner')
        if self.already_held and not self.same_lease:
            raise ValueError('another intent owns input')
        if type(admitted_ns) is not int or type(ack_ns) is not int or admitted_ns<0 or ack_ns<admitted_ns:
            raise ValueError('invalid clock')
        hidden_new_hold = not self.already_held
        self.press_count += 1
        if not self.sync_ok: raise RuntimeError('sync failed')
        self.sync_count += 1
        return {
            'event':'input_admission','key':key,'admitted_ns':admitted_ns,
            'input_ack_ns':ack_ns,'valid_until_ns':lease.deadline,
        }, hidden_new_hold

def matched(key,lease,a,b):
    first=FakeDownCore(already_held=False)
    repeat=FakeDownCore(already_held=True,same_lease=True)
    r1,h1=first.call_down(key,lease,a,b)
    r2,h2=repeat.call_down(key,lease,a,b)
    assert h1 is True and h2 is False
    assert r1==r2
    assert first.press_count==repeat.press_count==1
    assert first.sync_count==repeat.sync_count==1
    return r1

def controls():
    lease=Lease('L',1000); passed=0
    matched('F8',lease,10,20); passed+=2
    cases=[
      (FakeDownCore(already_held=True,same_lease=False),'F8',10,20,ValueError),
      (FakeDownCore(already_held=False,key_available=False),'F8',10,20,ValueError),
      (FakeDownCore(already_held=False,sync_ok=False),'F8',10,20,RuntimeError),
      (FakeDownCore(already_held=False),'F8',20,10,ValueError),
      (FakeDownCore(already_held=False),'',10,20,ValueError),
    ]
    for core,key,a,b,exc in cases:
        try: core.call_down(key,lease,a,b)
        except exc: passed+=1
        else: raise AssertionError((core,key,a,b,'accepted'))
    receipt,_=FakeDownCore(already_held=False).call_down('F8',lease,10,20)
    forbidden={'already_held','pre_key_down','new_hold','physical_down','actuation_id'}
    assert forbidden.isdisjoint(receipt); passed+=1
    return passed

def main():
    t0=time.perf_counter(); fixed=controls()
    rng=random.Random(SEED); dig=hashlib.sha256(); mism=0; witness_mism=0
    for i in range(N):
        key=rng.choice(['F8','W','A','SPACE','ENTER'])
        deadline=rng.randrange(1_000_000,10_000_000_000)
        a=rng.randrange(0,deadline)
        b=a+rng.randrange(0,100_000)
        lease=Lease(f'L{rng.randrange(1,1_000_000)}',deadline)
        first=FakeDownCore(already_held=False)
        repeat=FakeDownCore(already_held=True,same_lease=True)
        r1,h1=first.call_down(key,lease,a,b)
        r2,h2=repeat.call_down(key,lease,a,b)
        if h1==h2: witness_mism+=1
        if r1!=r2: mism+=1
        if first.press_count!=1 or repeat.press_count!=1 or first.sync_count!=1 or repeat.sync_count!=1:
            raise AssertionError('press/sync count')
        dig.update(json.dumps([r1,h1,h2],sort_keys=True,separators=(',',':')).encode())
    assert mism==0 and witness_mism==0
    out={
      'task':'ORDINARY-PRESS-REPEAT-EDGE-DISCRIMINATOR-20260917-001',
      'base':BASE,'v10_git_blob':V10_BLOB,
      'decision':'PASS_REPEATED_PRESS_ADMISSION_ALIAS_SCOPED',
      'seed':SEED,'matched_pairs':N,'hidden_witness_different':N,
      'public_receipt_identical':N,'public_mismatches':mism,'hidden_witness_failures':witness_mism,
      'press_sync_pairs':N,'fixed_controls_passed':fixed,'live_actions':0,'formal':False,
      'digest':dig.hexdigest(),'python':sys.version.split()[0], 'wall_s':time.perf_counter()-t0,
    }
    print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__': main()
