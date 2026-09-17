#!/usr/bin/env python3
import argparse, hashlib, importlib.util, json, random, sys
from pathlib import Path

TASK='USEFUL-CONTROL-INTERVAL-CONTRACT-FORMAL-20260917-002'; SEED=94120260917002; N=20000
EXPECTED_SHA='9783b3b6b24bcb93b4cf608db2bbd3f65740a1b0f5372c783f6c0367b680fc8b'
ROOT=Path(__file__).resolve().parent

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load():
    p=ROOT/'interval_contract.py'
    if sha(p)!=EXPECTED_SHA: raise RuntimeError('candidate_sha')
    spec=importlib.util.spec_from_file_location('audit_candidate',p); m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m); return m

def next_case(r, idx):
    ws=r.randrange(0,95); we=r.randrange(ws+1,97); aa=[]
    for j in range(r.randrange(0,6)):
        d=r.randrange(0,96); lo=r.randrange(d,97); hi=r.randrange(lo,97); au=[]
        for _ in range(r.randrange(0,5)):
            s=r.randrange(0,96); au.append((s,r.randrange(s+1,97)))
        aa.append({'id':f'c{idx}-a{j}','down':d,'lo':lo,'hi':hi,'auth':au})
    ee=[]
    for k in range(r.randrange(0,5)):
        mode=r.randrange(0,3)
        aid=aa[r.randrange(len(aa))]['id'] if mode==0 and aa else (f'unknown-{idx}-{k}' if mode==1 else None)
        ee.append({'t':r.randrange(0,96),'id':aid,'scored':bool(r.getrandbits(1)),'useful':bool(r.getrandbits(1))})
    return {'wait':(ws,we),'acts':aa,'events':ee}

def discrete(case):
    ws,we=case['wait']; L=set();U=set();AL=set();AU=set(); per={}; known={a['id'] for a in case['acts']}
    for a in case['acts']:
        l={t for t in range(ws,we) if a['down']<=t<a['lo']}; u={t for t in range(ws,we) if a['down']<=t<a['hi']}
        al={t for t in l if any(s<=t<e for s,e in a['auth'])}; au={t for t in u if any(s<=t<e for s,e in a['auth'])}
        L.update(l);U.update(u);AL.update(al);AU.update(au);per[a['id']]={'lower_ns':len(l),'upper_ns':len(u),'authority_lower_ns':len(al),'authority_upper_ns':len(au)}
    ef={'useful_bound':0,'useful_unbound':0,'nonuseful_bound':0,'unscored':0}
    for e in case['events']:
        if not e['scored']: ef['unscored']+=1
        elif e['id'] in known: ef['useful_bound' if e['useful'] else 'nonuseful_bound']+=1
        elif e['useful']: ef['useful_unbound']+=1
    return {'wait_ns':we-ws,'physical_occupancy_lower_ns':len(L),'physical_occupancy_upper_ns':len(U),'authorized_occupancy_lower_ns':len(AL),'authorized_occupancy_upper_ns':len(AU),'per_actuation':per,'effects':ef}

def cand(m,c):
    w=m.Interval(*c['wait']); aa=[m.Actuation(a['down'],m.ReleaseReceipt(a['lo'],a['hi'],False),[m.Interval(*x) for x in a['auth']],a['id']) for a in c['acts']]; ee=[m.EffectEvent(e['t'],e['id'],e['scored'],e['useful']) for e in c['events']]; return m.analyze(w,aa,ee)
def controls(m):
    out={}
    def rej(k,f):
        try:f();out[k]=False
        except ValueError:out[k]=True
    rej('duplicate_actuation_id_reject',lambda:m.analyze(m.Interval(0,20),[m.Actuation(1,m.ReleaseReceipt(3,4,False),[],'dup'),m.Actuation(2,m.ReleaseReceipt(4,5,False),[],'dup')],[]))
    rej('post_key_down_reject',lambda:m.Actuation(1,m.ReleaseReceipt(2,3,True),[],'a'))
    rej('release_before_down_reject',lambda:m.Actuation(5,m.ReleaseReceipt(4,6,False),[],'a'))
    z=m.analyze(m.Interval(0,30),[m.Actuation(10,m.ReleaseReceipt(20,20,False),[],'a'),m.Actuation(15,m.ReleaseReceipt(25,25,False),[],'b')],[]);out['overlap_union_not_sum']=z['physical_occupancy_lower_ns']==15 and z['physical_occupancy_upper_ns']==15
    z=m.analyze(m.Interval(0,40),[m.Actuation(10,m.ReleaseReceipt(20,30,False),[m.Interval(0,9),m.Interval(31,40)],'a')],[]);out['authority_outside_physical_no_increase']=z['authorized_occupancy_lower_ns']==0 and z['authorized_occupancy_upper_ns']==0
    w=m.Interval(0,20);a=[m.Actuation(1,m.ReleaseReceipt(2,2,False),[],'known')]
    out['useful_bound_role']=m.analyze(w,a,[m.EffectEvent(3,'known',True,True)])['effects']=={'useful_bound':1,'useful_unbound':0,'nonuseful_bound':0,'unscored':0}
    out['useful_unbound_role']=m.analyze(w,a,[m.EffectEvent(3,'other',True,True)])['effects']=={'useful_bound':0,'useful_unbound':1,'nonuseful_bound':0,'unscored':0}
    out['nonuseful_bound_role']=m.analyze(w,a,[m.EffectEvent(3,'known',True,False)])['effects']=={'useful_bound':0,'useful_unbound':0,'nonuseful_bound':1,'unscored':0}
    out['unscored_role']=m.analyze(w,a,[m.EffectEvent(3,'known',False,True)])['effects']=={'useful_bound':0,'useful_unbound':0,'nonuseful_bound':0,'unscored':1}
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--result',default='FORMAL_RESULT.json');a=ap.parse_args();rp=Path(a.result);r=json.loads(rp.read_text());m=load();g=random.Random(SEED);h=hashlib.sha256();mis=0;inv=0
    for i in range(N):
        c=next_case(g,i);o=cand(m,c);e=discrete(c);mis+=o!=e
        v=[o['physical_occupancy_lower_ns'],o['physical_occupancy_upper_ns'],o['authorized_occupancy_lower_ns'],o['authorized_occupancy_upper_ns']]
        inv+=not(0<=v[0]<=v[1]<=o['wait_ns'] and 0<=v[2]<=v[3] and v[2]<=v[0] and v[3]<=v[1])
        h.update((json.dumps({'i':i,'input':c,'out':o},sort_keys=True,separators=(',',':'))+'\n').encode())
    ctl=controls(m); errs=[]
    expected_dec='PASS_USEFUL_CONTROL_INTERVAL_CONTRACT_SCOPED' if mis==0 and inv==0 and all(ctl.values()) else 'NONPASS'
    checks={'task':r.get('task')==TASK,'formal_invocation':r.get('formal_invocation')==1,'formal_reruns':r.get('formal_reruns')==0,'seed':r.get('seed')==SEED,'case_count':r.get('case_count')==N,'candidate_sha':r.get('candidate_sha256')==EXPECTED_SHA,'match_count':r.get('exact_oracle_matches')==N-mis,'mismatch_count':r.get('oracle_mismatch_count')==mis,'invariant_count':r.get('invariant_error_count')==inv,'digest':r.get('case_digest_sha256')==h.hexdigest(),'controls':r.get('controls')==ctl,'decision':(r.get('decision')=='PASS_USEFUL_CONTROL_INTERVAL_CONTRACT_SCOPED')==(expected_dec.startswith('PASS'))}
    errs=[k for k,v in checks.items() if not v]
    out={'passed':not errs,'errors':errs,'recomputed_mismatches':mis,'recomputed_invariant_errors':inv,'recomputed_digest':h.hexdigest(),'recomputed_controls':ctl,'result_sha256':sha(rp)}
    print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if not errs else 1)
if __name__=='__main__':main()
