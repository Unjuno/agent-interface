import importlib.util, json, os, sys, types
from pathlib import Path
ROOT=Path(r'C:\Users\user\Documents\Codex\2026-10-03\new-chat\work\issue59-v15-scorer-20261005')
DOOM=ROOT/'research'/'doom'
EVENTS=[]
class FakeOwner:
    def __init__(self, display): self.owner_id='owner-A01'; self.records=[]; self.owned=[]; self.n=0
    def close(self): EVENTS.append({'event':'owner_close'})
    def call(self, op, lease=None, key=None):
        EVENTS.append({'event':'owner_call','op':op,'key':key})
        if op=='down': self.owned.append(key); return {'event':'input_admission','key':key,'owner_id':self.owner_id}
        if op=='up':
            self.n+=1; start=self.n*100; self.owned.remove(key)
            receipt={'event':'owner_explicit_keyup','operation':'up','key':key,'keycode':{'a':38,'space':65}[key],'owner_id':self.owner_id,'intent_token':lease.intent_token,'valid_until_ns':lease.deadline,'owner_keyrelease_started_ns':start,'owner_sync_returned_ns':start+2,'cancel_requested_after_sync':False,'server_sync_completed':True,'physical_verification_authoritative':False}
            self.records.append(receipt)
            return {'event':'input_release_transition','operation':'up','key':key,'owner_id':self.owner_id,'intent_token':lease.intent_token,'valid_until_ns':lease.deadline,'release_call_started_ns':start-2,'release_call_returned_ns':start+4,'ordinary_release_candidate':True,'owner_thread_keyup_verified':True,'owner_thread_keyup_receipt':dict(receipt)}
        if op=='input_state':
            return {'owner_id':self.owner_id,'sample_started_ns':self.n*100+10,'sample_finished_ns':self.n*100+11,'owned_keycodes':[]}
        raise AssertionError(op)
class Base:
    def __init__(self,session,out,emit,signal_readers):
        self.owner=FakeOwner(session.name); self.held=set(); self.emit=emit
        self._input_event_context=None; self.lease=types.SimpleNamespace(intent_token='lease-A01',deadline=999)
    def execute(self,step,cancel,identifier,index):
        self._input_event_context=(identifier,index)
        for k in step['keys']: self.raw(k,True)
        for i,k in enumerate(step['keys']):
            if i==1 and os.getenv('ISSUE59_INSERT_INTERKEY_QUERY')=='1': self.owner.call('input_state')
            self.raw(k,False)
        self._input_event_context=None
    def release_all(self): EVENTS.append({'event':'release_all'}); return {'verified':True}
base=types.ModuleType('doom_typed_release_backend_v2'); base.Backend=Base; base.suite=object()
ownermod=types.ModuleType('input_transition_owner_v4'); owner_mod_class=FakeOwner; owner_mod_cls=owner_mod_class; ownermod.InputOwner=owner_mod_cls
sys.modules['doom_typed_release_backend_v2']=base; sys.modules['input_transition_owner_v4']=ownermod
path=DOOM/'doom_owner_thread_release_batch_backend_v1.py'
spec=importlib.util.spec_from_file_location('tested_release_batch_backend',path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
emitted=[]; b=mod.Backend(types.SimpleNamespace(name='fake-display'),None,emitted.append,{})
b.execute({'keys':['a','space']},None,'program-A01',7)
release_rows=[r for r in emitted if r.get('event')=='input_release_transition']
summary={'schema':'issue59-release-order-a01-v1','source_head':'8a9e76d56be60fdaf96fa87ccbc9c7defd29e20d','scope':'deterministic fake owner; actual release-batch wrapper loaded from pinned source; base executor/InputOwner seams stubbed; no X11, game, or physical input','events':EVENTS,'rows':release_rows,'checks':{'two_explicit_ups':['a','space']==[r.get('key') for r in release_rows],'one_post_batch_sample':sum(e.get('event')=='owner_call' and e.get('op')=='input_state' for e in EVENTS)==1,'no_input_state_between_keyups':True,'identity_bound_receipts':['a','space']==[r.get('owner_thread_keyup_receipt',{}).get('key') for r in release_rows],'terminal_empty_sample':all(r.get('owned_keycodes_after_batch')==[] for r in release_rows),'physical_verification_reported_false':all(r.get('physical_verification_authoritative') is False for r in release_rows)}}
# Derive rather than assume inter-key ordering check.
up_positions=[i for i,e in enumerate(EVENTS) if e.get('event')=='owner_call' and e.get('op')=='up']
sample_positions=[i for i,e in enumerate(EVENTS) if e.get('event')=='owner_call' and e.get('op')=='input_state']
summary['checks']['no_input_state_between_keyups']=len(up_positions)==2 and len(sample_positions)==1 and up_positions[0] < up_positions[1] < sample_positions[0]
summary['checks']['all']=all(summary['checks'].values())
print(json.dumps(summary,sort_keys=True,indent=2))
if not summary['checks']['all']: raise SystemExit(1)



