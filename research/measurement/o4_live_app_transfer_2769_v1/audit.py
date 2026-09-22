from __future__ import annotations
import sys,json,pathlib,gzip,hashlib,copy
ROOT=pathlib.Path(sys.argv[1]); raw=json.loads((ROOT/'RAW.json').read_text()); rows=raw['rows']; errors=[]
def sha(b): return hashlib.sha256(b).hexdigest()
def oracle(r):
    if r['timeout_before'] or r['timeout_after']: return 'ESCALATE_TIMEOUT'
    p=ROOT/f"{r['_idx']:02d}-{r['app']}-{r['case']}"/'frame.bin.gz'
    if not p.exists(): return 'ESCALATE_MALFORMED'
    b=gzip.decompress(p.read_bytes())
    if r['malformed'] or len(b)!=r['expected_bytes']: return 'ESCALATE_MALFORMED'
    if r['request_window_id']!=r['capture_window_id'] or r['request_generation']!=r['capture_generation'] or r['capture_generation']!=r['return_generation'] or r['capture_window_id']!=r['return_window_id']: return 'ESCALATE_STALE_OR_MISMATCH'
    return 'LOCAL_TRUE' if r['capture_effect'] else 'LOCAL_FALSE'
if len(rows)!=18: errors.append('count')
seen=set(); unsafe=0; local=0; naive_unsafe=0
for idx,r0 in enumerate(rows):
    r=dict(r0); r['_idx']=idx
    key=(r['app'],r['case']);
    if key in seen: errors.append('dup');
    seen.add(key)
    exp=oracle(r)
    if r['oracle']!=exp: errors.append(f'oracle:{idx}')
    if r['candidate']!=exp: errors.append(f'candidate:{idx}')
    if r['candidate'].startswith('LOCAL_'): local+=1
    if r['case'] in ('stale_after_newer','timeout_before','timeout_after','replacement','malformed','delayed_verifier') and r['candidate'].startswith('LOCAL_'): unsafe+=1
    if r['case'] in ('stale_after_newer','timeout_after','replacement','malformed','delayed_verifier') and r['naive'].startswith('LOCAL_'): naive_unsafe+=1
    if r['case']!='timeout_before' and not r.get('events'): errors.append(f'events:{idx}')
summary={'status':'PASS_RAW_AUDIT' if not errors else 'FAIL_RAW_AUDIT','errors':errors,'rows':len(rows),'candidate_local':local,'candidate_unsafe_local':unsafe,'naive_unsafe_local':naive_unsafe,'candidate_oracle_mismatch':sum(r['candidate']!=r['oracle'] for r in rows)}
print(json.dumps(summary,sort_keys=True));
if errors: raise SystemExit(1)
