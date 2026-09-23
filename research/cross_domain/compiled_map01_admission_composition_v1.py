#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json, time
from pathlib import Path

EXPECTED_RUNTIME_BLOB='0c02db714127c8e0f770f9d4ac03699749899d2b'
EXPECTED_VALIDITY_BLOB='31bd30bd9baf6b7d56494cc3a18b2c6c70ffbc5e'

def githash(path):
    b=Path(path).read_bytes();return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def load(name,path,expected):
    actual=githash(path)
    if actual!=expected:raise RuntimeError((name,actual,expected))
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
cgi=None
av=None

BIND={'focus':11,'surface':22,'geometry':[0,0,640,480]}
RETREAT=[{'action':'retreat_fire','extent':1}]
STRAFE=[{'action':'strafe_left','extent':1}]

def contract(action, fire):
    signals={'health':{'status':'observed','value':73}}
    preds=[{'signal_id':'health','operator':'minimum','value':30},{'signal_id':'health','operator':'max_decrease_from_source','value':6}]
    if fire:
        signals['ammo']={'status':'observed','value':45};preds.append({'signal_id':'ammo','operator':'minimum','value':1})
    return {'format':av.CONTRACT_FORMAT,'action_fingerprint':av.action_fingerprint(action),'source':{'sequence':10,'capture_ns':1_000_000_000,'binding':BIND,'signals':signals},'max_current_age_ms':1000,'predicates':preds}
CONTRACTS={}
PAYLOADS={'retreat_fire':RETREAT,'strafe_left':STRAFE}

def setup(runtime_path, validity_path):
    global cgi, av, CONTRACTS
    cgi=load('cgi',runtime_path,EXPECTED_RUNTIME_BLOB)
    av=load('av',validity_path,EXPECTED_VALIDITY_BLOB)
    CONTRACTS={'retreat_fire':contract(RETREAT,True),'strafe_left':contract(STRAFE,False)}

def br(when,outcome,action=None,next_state=None,reason=None):return {'when':when,'outcome':outcome,'action':action,'next_state':next_state,'reason':reason}
INTERFACE={'format':'compiled-gui-interface-v1','interface_id':'map01-composition','session_scope':'offline','surface':'map01','predicates':['surface_present','phase'],'symbols':{'surface':{'kind':'target_reference','target_reference':'map01_surface','identity_predicate':'surface_present','dependencies':['surface_present']}},'actions':{
 'retreat':{'target_symbol':'surface','operation':'retreat_fire','expected_effect':{'surface_present':True,'phase':'STRAFE'}},
 'strafe':{'target_symbol':'surface','operation':'strafe_left','expected_effect':{'surface_present':True,'phase':'DONE'}}},'method':{'name':'bounded-combat-sequence','version':'1','initial_state':'retreat_state','max_transitions':3,'max_runtime_ms':1000,'states':{
  'retreat_state':{'branches':[br({'surface_present':False},'yield',reason='association_changed'),br({'surface_present':True,'phase':'RETREAT'},'action','retreat','strafe_state')]},
  'strafe_state':{'branches':[br({'surface_present':False},'yield',reason='association_changed'),br({'surface_present':True,'phase':'STRAFE'},'action','strafe','done')]},
  'done':{'branches':[br({'surface_present':True,'phase':'DONE'},'complete'),br({'surface_present':False},'yield',reason='association_changed')]}}}}

class Episode:
    def __init__(self, scenario):
        self.scenario=scenario;self.phase='RETREAT';self.health=73;self.ammo=45;self.seq=10;self.actions=[];self.validity=[];self.last_snapshot=None
        if scenario=='no_ammo':self.ammo=0
    def observe(self,_req):
        self.seq+=1
        binding=dict(BIND);binding['geometry']=list(BIND['geometry'])
        if self.scenario=='binding_change':binding['geometry']=[1,0,640,480]
        signals={'health':{'status':'observed','value':self.health},'ammo':{'status':'observed','value':self.ammo}}
        if self.scenario=='unknown_health':signals['health']={'status':'unknown','value':None}
        capture=time.perf_counter_ns()
        self.last_snapshot={'format':av.SNAPSHOT_FORMAT,'sequence':self.seq,'capture_ns':capture,'binding':binding,'signals':signals}
        pred={'surface_present':True,'phase':self.phase};dig=hashlib.sha256(json.dumps([self.seq,pred],sort_keys=True).encode()).hexdigest()
        return {'sequence':self.seq,'captured_ns':capture,'surface':'map01','predicates':pred,'evidence_ref':f'e{self.seq}','evidence_digest':dig}
    def admit(self,req):
        op=req['operation'];snap=self.last_snapshot;now=snap['capture_ns']+(2_000_000_000 if self.scenario=='stale' else 10_000_000)
        result=av.evaluate_action_validity(PAYLOADS[op],CONTRACTS[op],snap,now);self.validity.append(result['status'])
        ok=result['action_may_proceed_to_executor_admission']
        return {'eligible':ok,'status':'revalidated' if ok else result['reason'],'authorization':f'auth-{self.seq}' if ok else None,'expected_sequence':self.seq,'valid_until_ns':time.perf_counter_ns()+100_000_000}
    def execute(self,req):
        self.actions.append(req['operation'])
        if req['operation']=='retreat_fire':
            self.phase='STRAFE'
            if self.scenario=='damage':self.health=65
            else:self.health=70
        else:self.phase='DONE'
        n=len(self.actions);return {'status':'completed','action_id':f'a{n}','effect_ref':f'f{n}','release':{'verified':True,'keys_down':[],'buttons_down':[]}}
    def verify(self,req):return {'status':'succeeded','evidence_ref':req['observation']['evidence_ref']}
    def adapters(self):return {'observe':self.observe,'admit':self.admit,'execute':self.execute,'verify_effect':self.verify,'cancelled':lambda:False}

def once(scenario):
    ep=Episode(scenario);r=cgi.run(INTERFACE,ep.adapters());return ep,r

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--runtime',type=Path,required=True)
    parser.add_argument('--action-validity',type=Path,required=True)
    parser.add_argument('--episodes',type=int,default=2000)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    setup(args.runtime,args.action_validity)
    cgi.validate(INTERFACE)
    specs={
      'healthy':('TASK_SUCCEEDED','method_complete',2,['VALID_CURRENT','VALID_CURRENT']),
      'damage':('SAFE_YIELD','authority_unavailable',1,['VALID_CURRENT','REJECTED_PREDICATE']),
      'no_ammo':('SAFE_YIELD','authority_unavailable',0,['REJECTED_PREDICATE']),
      'binding_change':('SAFE_YIELD','authority_unavailable',0,['REJECTED_STATE_BINDING']),
      'stale':('SAFE_YIELD','authority_unavailable',0,['REJECTED_STALE']),
      'unknown_health':('SAFE_YIELD','authority_unavailable',0,['REJECTED_SIGNAL_UNKNOWN']),
    }
    N=args.episodes
    summary={'schema':'compiled-map01-admission-composition-v1','runtime_blob':EXPECTED_RUNTIME_BLOB,'action_validity_blob':EXPECTED_VALIDITY_BLOB,'episodes_per_case':N,'cases':{},'failures':[]}
    for name,expected in specs.items():
        passed=0
        for i in range(N):
            ep,r=once(name);actual=(r['outcome'],r['reason'],len(ep.actions),ep.validity)
            if actual==expected and r['frontier_model_resumptions']==0 and all(t['release_verified'] for t in r['transitions']):passed+=1
            else:summary['failures'].append([name,i,actual,expected,r])
        summary['cases'][name]={'passed':passed,'expected':list(expected)}
    summary['pass']=all(v['passed']==N for v in summary['cases'].values()) and not summary['failures']
    args.out.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,indent=2,sort_keys=True));return 0 if summary['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
