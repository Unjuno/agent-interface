from __future__ import annotations
import hashlib,json,random
from pathlib import Path
from normalizer import normalize_one,normalize_stream
from oracle import oracle
from queue_contract import reduce_candidate
HERE=Path(__file__).resolve().parent
SEED=104220260918001; VALID=25000; INVALID=10000
REASONS=['focus_changed','expired','surface_changed','cancelled','stop_requested']

def env(i,raw,seq=None):
    return {'event_id':f'v{i}','seq':i if seq is None else seq,'received_ns':1_000_000+i,'session':f's{i%7}','target':f't{i%5}','stream':'input_owner','raw':raw}
def release(reason,verified=True,buttons=None,keys=None,i=0):
    return {'event':'owner_release','reason':reason,'verified':verified,'buttons_down':[] if buttons is None else buttons,'keys_down':[] if keys is None else keys,'verified_ns':900_000+i,'valid_until_ns':1_500_000+i}
def valid_case(rng,i):
    k=rng.randrange(8)
    if k<5: raw=release(REASONS[k],i=i)
    elif k==5: raw={'event':'owner_failed','error':f'err-{i}','verified':False}
    elif k==6: raw={'event':'cleanup_failed','error':f'err-{i}','verified':False}
    else:
        raw=release(rng.choice(REASONS),verified=rng.choice([False,True]),buttons=[1] if rng.randrange(2) else [],keys=[38] if rng.randrange(2) else [],i=i)
        if raw['verified'] and not raw['buttons_down'] and not raw['keys_down']: raw['verified']=False
    return env(i,raw)
def invalid_case(rng,i):
    base=env(i,release('focus_changed',i=i)); m=rng.randrange(8)
    if m==0: base['raw']={'event':'input_admission'}
    elif m==1: base['raw']=release('release',i=i)
    elif m==2: base['event_id']=' '
    elif m==3: base['seq']=-1
    elif m==4: base['received_ns']=-1
    elif m==5: base['raw']={'event':'owner_failed','error':'x','verified':True}
    elif m==6: del base['raw']['verified_ns']
    else: base['raw']['reason']=' '
    return base

def main():
    out=HERE/'RESULT.json'
    if out.exists(): raise RuntimeError('RESULT exists')
    rng=random.Random(SEED); h=hashlib.sha256(); valid_mismatch=0; invalid_accepted=0; composition_errors=0; raw_errors=0; kinds={}; batch=[]
    for i in range(VALID):
        e=valid_case(rng,i); n=normalize_one(e); o=oracle(e)
        if n['normalization']['kind']!=o['kind']: valid_mismatch+=1
        if n['raw']!=o['raw'] or n['raw']!=e['raw']: raw_errors+=1
        kinds[n['normalization']['kind']]=kinds.get(n['normalization']['kind'],0)+1
        h.update(json.dumps([e['event_id'],n['normalization']['kind']],separators=(',',':')).encode())
        batch.append(e)
        if len(batch)==10:
            ns=normalize_stream(batch); rr=reduce_candidate([x['record'] for x in ns],2_000_000_000,0)
            ids=[x['event_id'] for x in batch]
            if rr['delivered_ids']!=ids or rr['critical_ids']!=ids or rr['grants_input_authority']: composition_errors+=1
            batch=[]
    for i in range(INVALID):
        e=invalid_case(rng,VALID+i)
        ca=oa=False
        try: normalize_one(e); ca=True
        except ValueError: pass
        try: oracle(e); oa=True
        except ValueError: pass
        if ca or oa: invalid_accepted+=1
        h.update(json.dumps(['invalid',i,ca,oa],separators=(',',':')).encode())
    decision='PASS_INPUT_OWNER_CRITICAL_NORMALIZATION_SCOPED' if not any((valid_mismatch,invalid_accepted,composition_errors,raw_errors)) else 'FAIL_NORMALIZATION_CONTRACT'
    r={'schema':'input_owner_critical_normalization_result_v1','task':'INPUT-OWNER-CRITICAL-NORMALIZATION-20260918-001','base':'6c3e11c3b794422340eb395ef167434c6554a322','seed':SEED,'valid_records':VALID,'invalid_records':INVALID,'valid_mismatches':valid_mismatch,'invalid_accepted':invalid_accepted,'composition_errors':composition_errors,'raw_provenance_errors':raw_errors,'kind_counts':kinds,'digest':h.hexdigest(),'decision':decision,'formal_invocation':1,'reruns':0,'source_git_blobs':{'input_owner_v10':'341b3c01649943ddaad5f28431a792c4889cc36e','queue_contract':'404a452aa304b4bde73ec0182450d241e2a744af','#1032_RESULT':'f9afddd78ad2221e45dc9f69d304362ed1a3abbb'},'model_calls':0,'gui_actions':0,'task_input_actions':0,'authority_actions':0}
    out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n'); print(decision)
if __name__=='__main__': main()
