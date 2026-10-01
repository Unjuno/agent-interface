from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from model import Candidate
from oracle import HistoryOracle
from corpus import CHUNKS,PER_CHUNK,LIFETIMES,SEED,sequence

def amap(snapshot):
    return {row[0]:(row[1],row[2],row[3]) for row in snapshot['active']}

def run_chunk(chunk):
    if not (0<=chunk<CHUNKS): raise ValueError('chunk')
    start=chunk*PER_CHUNK; end=min(start+PER_CHUNK,LIFETIMES)
    counts={k:0 for k in ['steps','mismatches','false_mint','retired_reuse','cross_lineage_retirement','multi_id_per_hold','repeated_down_instability','unconfirmed_fabrication','active_retired_overlap']}
    h=hashlib.sha256()
    for idx in range(start,end):
        c=Candidate(); o=HistoryOracle(); hold_aid={}
        for pos,e in enumerate(sequence(idx)):
            before=c.snapshot(); before_active=amap(before); retired_before=set(before['retired'])
            co=c.step(e); oo=o.step(e); after=c.snapshot(); oa=o.snapshot(); counts['steps']+=1
            if co!=oo or after!=oa: counts['mismatches']+=1
            retired_after=set(after['retired'])
            status,aid=co
            if status=='MINTED':
                if e.op!='down' or not e.confirmed or e.key in before_active: counts['false_mint']+=1
                if aid in retired_before: counts['retired_reuse']+=1
                if e.key in hold_aid and hold_aid[e.key]!=aid: counts['multi_id_per_hold']+=1
                hold_aid[e.key]=aid
            if e.op=='down' and e.key in before_active and before_active[e.key][:2]==(e.owner,e.intent):
                if status!='ACTIVE_REUSED' or aid!=before_active[e.key][2]: counts['repeated_down_instability']+=1
            if not e.confirmed:
                if aid is not None or before!=after: counts['unconfirmed_fabrication']+=1
            if e.op in ('up','cleanup') and e.confirmed and e.key in before_active:
                bo,bi,ba=before_active[e.key]
                if (bo,bi)!=(e.owner,e.intent) and ba in retired_after-retired_before: counts['cross_lineage_retirement']+=1
                if status=='RETIRED' and aid==ba: hold_aid.pop(e.key,None)
            if set(x[3] for x in after['active']) & retired_after: counts['active_retired_overlap']+=1
            h.update(json.dumps({'i':idx,'p':pos,'e':[e.op,e.owner,e.intent,e.key,e.confirmed],'o':co,'s':after},sort_keys=True,separators=(',',':')).encode()+b'\n')
    return {'task':'PHYSICAL-KEY-HOLD-ACTUATION-IDENTITY-AUDITABLE-20260918-003','seed':SEED,'chunk':chunk,'start':start,'end':end,'lifetimes':end-start,'counts':counts,'digest_sha256':h.hexdigest(),'reruns':0}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--chunk',type=int,required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    out=Path(a.out)
    if out.exists(): raise RuntimeError('exclusive output exists')
    r=run_chunk(a.chunk); out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n'); print(json.dumps(r,sort_keys=True))
if __name__=='__main__': main()
