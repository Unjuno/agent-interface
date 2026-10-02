import argparse, hashlib, importlib.util, json, random, sys
from pathlib import Path
ROOT=Path(__file__).parent; sys.path.insert(0,str(ROOT))

def load_v12():
    spec=importlib.util.spec_from_file_location('v12_primary',ROOT/'input_owner_v12.py'); m=importlib.util.module_from_spec(spec); sys.modules['v12_primary']=m; spec.loader.exec_module(m); return m
V12=load_v12()
from oracle import IdentityOracle, press_status as opress, release_status as orelease
import press_contract, release_contract
from adapter_contract import Edge, compose

KEYS={'F8':74,'F9':75}
LEASES={'A':'intentA','B':'intentB','N':None}

class Control:
    def __init__(self):
        self.held={}; self.active=None; self.physical=set(); self.touched=set(); self.trace=[]
    def snap(self): return (tuple(sorted(self.held.items())),self.active,tuple(sorted(self.physical)),tuple(self.trace))

def apply_external(c,key,state):
    if state=='DOWN': c.physical.add(key)
    elif state=='UP': c.physical.discard(key)

def baseline(c,e):
    k=e['key']; code=KEYS[k]; lease=e['lease']; apply_external(c,code,e['external'])
    start_trace=len(c.trace)
    if not e['key_available']: return ('ERR_KEY',None,c.snap(),tuple(c.trace[start_trace:]))
    if e['op']=='down':
        if e['fault']: return ('ERR_FAULT',None,c.snap(),tuple(c.trace[start_trace:]))
        if c.active is not None and c.active!=lease: return ('ERR_ACTIVE',None,c.snap(),tuple(c.trace[start_trace:]))
        if e['focus_invalid']: return ('ERR_FOCUS',None,c.snap(),tuple(c.trace[start_trace:]))
        if not e['lease_ok']: return ('ERR_LEASE',None,c.snap(),tuple(c.trace[start_trace:]))
        if e['cancel']: return ('ERR_CANCEL',None,c.snap(),tuple(c.trace[start_trace:]))
        c.active=lease; c.held[code]=lease; c.touched.add(code)
        if not e['inject_ok']: return ('ERR_INJECT',None,c.snap(),tuple(c.trace[start_trace:]))
        c.trace.append(('press',code)); c.physical.add(code)
        if not e['sync_ok']: return ('ERR_SYNC',None,c.snap(),tuple(c.trace[start_trace:]))
        c.trace.append(('sync',None)); return ('OK_DOWN','input_admission',c.snap(),tuple(c.trace[start_trace:]))
    if e['op']=='up':
        if code in c.held and c.held[code]!=lease: return ('ERR_FOREIGN',None,c.snap(),tuple(c.trace[start_trace:]))
        if code in c.held:
            if not e['inject_ok']: return ('ERR_INJECT',None,c.snap(),tuple(c.trace[start_trace:]))
            c.trace.append(('release',code)); c.physical.discard(code)
            if not e['sync_ok']: return ('ERR_SYNC',None,c.snap(),tuple(c.trace[start_trace:]))
            c.trace.append(('sync',None)); del c.held[code]
        return ('OK_UP',None,c.snap(),tuple(c.trace[start_trace:]))
    # cleanup/release
    if c.active is not None and c.active!=lease: return ('ERR_RELEASE_FOREIGN',None,c.snap(),tuple(c.trace[start_trace:]))
    for hcode in list(c.held):
        if not e['inject_ok']: return ('ERR_INJECT',None,c.snap(),tuple(c.trace[start_trace:]))
        c.trace.append(('release',hcode)); c.physical.discard(hcode)
    if not e['sync_ok']: return ('ERR_SYNC',None,c.snap(),tuple(c.trace[start_trace:]))
    c.trace.append(('sync',None))
    down=[x for x in c.touched if x in c.physical]
    if down: return ('ERR_NOT_NEUTRAL',None,c.snap(),tuple(c.trace[start_trace:]))
    c.held.clear(); c.touched.clear(); c.active=None
    return ('OK_CLEANUP','owner_release',c.snap(),tuple(c.trace[start_trace:]))

class Candidate:
    def __init__(self): self.c=Control(); self.ids=V12._HoldIdentity('ownerA'); self.oracle_ids=IdentityOracle('ownerA'); self.down_edges={}
    def run(self,e,seq):
        c=self.c; k=e['key']; code=KEYS[k]; lease=e['lease']; intent=LEASES[lease]; apply_external(c,code,e['external']); start_trace=len(c.trace)
        if not e['key_available']: return ('ERR_KEY',None,c.snap(),tuple(c.trace[start_trace:])), None
        if e['op']=='down':
            if e['fault']: return ('ERR_FAULT',None,c.snap(),tuple(c.trace[start_trace:])),None
            if c.active is not None and c.active!=lease: return ('ERR_ACTIVE',None,c.snap(),tuple(c.trace[start_trace:])),None
            if e['focus_invalid']: return ('ERR_FOCUS',None,c.snap(),tuple(c.trace[start_trace:])),None
            if not e['lease_ok']: return ('ERR_LEASE',None,c.snap(),tuple(c.trace[start_trace:])),None
            if e['cancel']: return ('ERR_CANCEL',None,c.snap(),tuple(c.trace[start_trace:])),None
            owner_before=code in c.held; pre=(code in c.physical) if e['pre_sample_ok'] else None
            c.active=lease; c.held[code]=lease; c.touched.add(code)
            if not e['inject_ok']: return ('ERR_INJECT',None,c.snap(),tuple(c.trace[start_trace:])),None
            c.trace.append(('press',code)); c.physical.add(code)
            if not e['sync_ok']: return ('ERR_SYNC',None,c.snap(),tuple(c.trace[start_trace:])),None
            c.trace.append(('sync',None)); post=(code in c.physical) if e['post_sample_ok'] else None
            status='PHYSICAL_SAMPLE_UNAVAILABLE' if pre is None or post is None else V12._classify_press(owner_before,pre,True,True,post,code in c.held and c.held[code]==lease)[0]
            confirmed=status=='CONFIRMED_PHYSICAL_DOWN'; ist,aid=self.ids.on_down(code,k,intent,owner_before,confirmed)
            ostatus=None if pre is None or post is None else opress(owner_before,pre,post,code in c.held and c.held[code]==lease)
            oist,oaid=self.oracle_ids.down(code,k,intent,owner_before,confirmed)
            meas={'edge':'down','status':status,'oracle_status':ostatus,'identity':(ist,aid),'oracle_identity':(oist,oaid),'interval':None,'adapter':None}
            if confirmed: meas['interval']=(seq*100+2,seq*100+8)
            if intent and pre is not None and post is not None:
                t=press_contract.Times(seq*100,seq*100+1,seq*100+2,seq*100+3,seq*100+4,seq*100+5,seq*100+8,seq*100+9)
                parent=press_contract.build(press_contract.Evidence(f'p{seq}','ownerA',intent,k,owner_before,pre,True,True,post,code in c.held and c.held[code]==lease,t))
                meas['parent']=(parent['status'],tuple(parent['physical_down_interval']) if parent['physical_down_interval'] else None)
                if aid:
                    edge=Edge('down',parent['status'],aid,'ownerA',intent,k,tuple(parent['physical_down_interval']) if parent['physical_down_interval'] else None); meas['adapter']=edge
                    if parent['status']=='CONFIRMED_PHYSICAL_DOWN': self.down_edges[aid]=edge
            return ('OK_DOWN','input_admission',c.snap(),tuple(c.trace[start_trace:])),meas
        if e['op']=='up':
            if code in c.held and c.held[code]!=lease: return ('ERR_FOREIGN',None,c.snap(),tuple(c.trace[start_trace:])),None
            owner_owned=code in c.held; pre=(code in c.physical) if e['pre_sample_ok'] else None; attempted=owner_owned
            if owner_owned:
                if not e['inject_ok']: return ('ERR_INJECT',None,c.snap(),tuple(c.trace[start_trace:])),None
                c.trace.append(('release',code)); c.physical.discard(code)
                if not e['sync_ok']: return ('ERR_SYNC',None,c.snap(),tuple(c.trace[start_trace:])),None
                c.trace.append(('sync',None)); del c.held[code]
            post=(code in c.physical) if e['post_sample_ok'] else None
            status='PHYSICAL_SAMPLE_UNAVAILABLE' if pre is None or post is None else V12._classify_release(owner_owned,pre,attempted,attempted,post)[0]
            confirmed=status=='CONFIRMED_PHYSICAL_UP'; ist,aid=self.ids.on_up(code,k,intent,confirmed)
            ostatus=None if pre is None or post is None else orelease(owner_owned,pre,post)
            oist,oaid=self.oracle_ids.up(code,k,intent,confirmed)
            meas={'edge':'up','status':status,'oracle_status':ostatus,'identity':(ist,aid),'oracle_identity':(oist,oaid),'interval':None,'adapter':None,'compose':None}
            if confirmed: meas['interval']=(seq*100+2,seq*100+8)
            if intent and pre is not None and post is not None:
                t=release_contract.Times(seq*100,seq*100+1,seq*100+2,seq*100+3,seq*100+4,seq*100+5,seq*100+8,seq*100+9)
                parent=release_contract.build(release_contract.Evidence(f'u{seq}','ownerA',intent,k,owner_owned,pre,attempted,attempted,post,t))
                meas['parent']=(parent['status'],tuple(parent['physical_up_interval']) if parent['physical_up_interval'] else None)
                if aid:
                    edge=Edge('up',parent['status'],aid,'ownerA',intent,k,tuple(parent['physical_up_interval']) if parent['physical_up_interval'] else None); meas['adapter']=edge
                    if aid in self.down_edges: meas['compose']=compose(self.down_edges[aid],edge)['status']
            return ('OK_UP',None,c.snap(),tuple(c.trace[start_trace:])),meas
        # cleanup
        if c.active is not None and c.active!=lease: return ('ERR_RELEASE_FOREIGN',None,c.snap(),tuple(c.trace[start_trace:])),None
        for hcode in list(c.held):
            if not e['inject_ok']: return ('ERR_INJECT',None,c.snap(),tuple(c.trace[start_trace:])),None
            c.trace.append(('release',hcode)); c.physical.discard(hcode)
        if not e['sync_ok']: return ('ERR_SYNC',None,c.snap(),tuple(c.trace[start_trace:])),None
        c.trace.append(('sync',None)); down=[x for x in c.touched if x in c.physical]
        if down: return ('ERR_NOT_NEUTRAL',None,c.snap(),tuple(c.trace[start_trace:])),None
        c.held.clear(); c.touched.clear(); c.active=None; self.ids.terminate_after_verified_neutral(); self.oracle_ids.cleanup_verified()
        return ('OK_CLEANUP','owner_release',c.snap(),tuple(c.trace[start_trace:])),{'edge':'cleanup','per_key_interval':False}

def event(rng):
    op=rng.choices(['down','up','cleanup'],[45,40,15])[0]; key=rng.choice(list(KEYS)); lease=rng.choices(['A','B','N'],[46,46,8])[0]
    ext=rng.choices([None,'UP','DOWN'],[90,5,5])[0]
    return {'op':op,'key':key,'lease':lease,'external':ext,'key_available':rng.random()>=.02,'fault':rng.random()<.01,'focus_invalid':rng.random()<.03,'lease_ok':rng.random()>=.02,'cancel':rng.random()<.02,'pre_sample_ok':rng.random()>=.05,'post_sample_ok':rng.random()>=.05,'inject_ok':rng.random()>=.01,'sync_ok':rng.random()>=.01}

def run(seed,seqs,max_len):
    rng=random.Random(seed); counts={'sequences':seqs,'events':0,'control_mismatch':0,'measurement_mismatch':0,'identity_mismatch':0,'parent_mismatch':0,'false_interval':0,'authority_error':0,'composed':0,'cleanup_edge_claim':0}
    digest=hashlib.sha256()
    first_errors=[]
    for si in range(seqs):
        b=Control(); cand=Candidate()
        n=rng.randint(1,max_len)
        for j in range(n):
            e=event(rng); seq=si*max_len+j+1
            bo=baseline(b,e); co,m=cand.run(e,seq); counts['events']+=1
            # Control states and backend traces must be exact, excluding measurement-only up payload.
            if bo!=co:
                counts['control_mismatch']+=1
                if len(first_errors)<5:first_errors.append(['control',si,j,e,bo,co])
            if m:
                if m['edge'] in ('down','up'):
                    if m['oracle_status'] is not None and m['status']!=m['oracle_status']:
                        counts['measurement_mismatch']+=1
                        if len(first_errors)<5:first_errors.append(['status',si,j,e,m])
                    if m['identity']!=m['oracle_identity']:
                        counts['identity_mismatch']+=1
                        if len(first_errors)<5:first_errors.append(['identity',si,j,e,m])
                    if 'parent' in m and m['parent'][0]!=m['status']:
                        counts['parent_mismatch']+=1
                    if m['interval'] is not None and m['status'] not in ('CONFIRMED_PHYSICAL_DOWN','CONFIRMED_PHYSICAL_UP'):
                        counts['false_interval']+=1
                    if m.get('compose')=='COMPOSED_PHYSICAL_ACTUATION': counts['composed']+=1
                elif m['edge']=='cleanup' and m.get('per_key_interval'): counts['cleanup_edge_claim']+=1
            if cand.ids.active != {k:(v[0],v[1],v[2]) for k,v in cand.ids.active.items()}: raise AssertionError('impossible')
            if cand.ids.counter != cand.oracle_ids.gen or tuple(sorted(cand.ids.active.items()))!=tuple(sorted(cand.oracle_ids.active.items())) or tuple(sorted(cand.ids.retired))!=tuple(sorted(cand.oracle_ids.retired)):
                counts['identity_mismatch']+=1
            digest.update(json.dumps([si,j,e,co,m],sort_keys=True,default=str,separators=(',',':')).encode())
    counts['digest_sha256']=digest.hexdigest(); counts['first_errors']=first_errors
    counts['decision']='PASS_INPUT_OWNER_V12_OFFLINE_MECHANICS_SCOPED' if all(counts[k]==0 for k in ('control_mismatch','measurement_mismatch','identity_mismatch','parent_mismatch','false_interval','authority_error','cleanup_edge_claim')) and counts['composed']>0 else 'FAIL_OFFLINE_MECHANICS'
    return counts

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--seed',type=int,default=99820260918002); ap.add_argument('--sequences',type=int,default=120000); ap.add_argument('--max-len',type=int,default=12); ap.add_argument('--out',default='RESULT.json'); a=ap.parse_args()
    r=run(a.seed,a.sequences,a.max_len); Path(a.out).write_text(json.dumps(r,sort_keys=True,indent=2)+'\n'); print(json.dumps({k:v for k,v in r.items() if k!='first_errors'},sort_keys=True))
