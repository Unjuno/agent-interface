from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from model import Candidate
from oracle import HistoryOracle
from corpus import SEED,CHUNKS,PER_CHUNK,sequence
p=argparse.ArgumentParser();p.add_argument('--chunk',type=int,required=True);p.add_argument('--outdir',required=True);a=p.parse_args()
if not 0<=a.chunk<CHUNKS: raise SystemExit('bad chunk')
outdir=Path(a.outdir);outdir.mkdir(parents=True,exist_ok=True);out=outdir/f'chunk-{a.chunk:02d}.json'
if out.exists(): raise RuntimeError('chunk output exists; rerun forbidden')
start=a.chunk*PER_CHUNK; end=start+PER_CHUNK
counts={'steps':0,'mismatches':0,'false_mint':0,'retired_reuse':0,'cross_lineage_retirement':0,'multi_id_per_hold':0,'repeated_down_instability':0,'unconfirmed_fabrication':0,'active_retired_overlap':0}
digest=hashlib.sha256()
for idx in range(start,end):
    c=Candidate(); o=HistoryOracle(); seen_retired=set()
    for e in sequence(idx):
        pre=c.snapshot(); active_before={x[0]:x[1:] for x in pre['active']}; counter_before=dict(pre['counters'])
        co=c.step(e); oo=o.step(e); post=c.snapshot(); counts['steps']+=1
        if co!=oo or post!=o.snapshot(): counts['mismatches']+=1
        if co[0]=='MINTED':
            if not e.confirmed: counts['false_mint']+=1
            if co[1] in seen_retired: counts['retired_reuse']+=1
            if e.key in active_before: counts['multi_id_per_hold']+=1
        if e.op=='down' and e.key in active_before and active_before[e.key][0:2]==(e.owner,e.intent):
            prior_id=active_before[e.key][2]
            if co!=('ACTIVE_REUSED',prior_id) or dict(post['counters'])!=counter_before: counts['repeated_down_instability']+=1
        if (e.op=='down' and not e.confirmed and e.key not in active_before and co[1] is not None) or (e.op in ('up','cleanup') and not e.confirmed and co[1] is not None): counts['unconfirmed_fabrication']+=1
        if e.op in ('up','cleanup') and e.confirmed and e.key in active_before and active_before[e.key][0:2]!=(e.owner,e.intent):
            if post!=pre or co[0]=='RETIRED': counts['cross_lineage_retirement']+=1
        retired=set(post['retired']); active_ids={x[3] for x in post['active']}
        if retired & active_ids: counts['active_retired_overlap']+=1
        seen_retired |= retired
        digest.update(f'{idx}|{e.op}|{e.owner}|{e.intent}|{e.key}|{int(e.confirmed)}|{co[0]}|{co[1]}|{post}\n'.encode())
r={'schema':'physical_key_hold_identity_chunk_v2','task':'PHYSICAL-KEY-HOLD-ACTUATION-IDENTITY-20260917-002','seed':SEED,'chunk':a.chunk,'start':start,'end':end,'lifetimes':PER_CHUNK,'reruns':0,'counts':counts,'digest_sha256':digest.hexdigest()}
out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,sort_keys=True))
