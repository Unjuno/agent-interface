from __future__ import annotations
import hashlib,json
from pathlib import Path
import r0_bridge_snapshot as bridge
PRECISION_LIMIT_NS=5_000_000

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load_jsonl(path):return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
def evaluate(runtime,program_id):
    runtime=Path(runtime); rows=load_jsonl(runtime/'events.jsonl')
    terminals=[r for r in rows if r.get('event')=='terminal' and r.get('id')==program_id]
    releases=[r for r in rows if r.get('event')=='input_release_transition' and r.get('release_batch_identifier')==program_id]
    downs=[]
    for r in rows:
        if r.get('event')!='input_admission':continue
        m=r.get('physical_key_measurement');e=m.get('adapter_edge') if isinstance(m,dict) else None
        if isinstance(e,dict) and e.get('key') in ('a','d'):downs.append((r,e))
    pairs={};errors=[]
    for rr in releases:
        m=rr.get('physical_key_measurement');up=m.get('adapter_edge') if isinstance(m,dict) else None
        key=rr.get('key'); candidates=[e for row,e in downs if e.get('key')==key and e.get('intent_token')==rr.get('intent_token') and e.get('owner_id')==rr.get('owner_id')]
        if len(candidates)!=1 or not isinstance(up,dict):errors.append(f'pair:{key}:{len(candidates)}');continue
        pairs[key]=[candidates[0],up]
    bound=bridge.bind_batch(releases,pairs,bridge.EXPECTED_SOURCE);acts=bound.get('actuations') or [];metrics=[]
    for a in acts:
        dlo,dhi=a['physical_down_interval'];ulo,uhi=a['physical_up_interval'];width=(dhi-dlo)+(uhi-ulo)
        metrics.append({'key':a['key'],'actuation_id':a['actuation_id'],'hold_lower_ns':ulo-dhi,'hold_upper_ns':uhi-dlo,'censor_width_ns':width,'censor_width_ms':width/1e6,'precision_pass':width<=PRECISION_LIMIT_NS})
    result={'program_id':program_id,'terminal_completed':len(terminals)==1 and terminals[0].get('status')=='completed','release_rows':len(releases),'down_rows':len(downs),'pair_keys':sorted(pairs),'bridge_status':bound.get('status'),'actuations':metrics,'confirmed_down':sum(p[0].get('status')=='CONFIRMED_PHYSICAL_DOWN' for p in pairs.values()),'confirmed_up':sum(p[1].get('status')=='CONFIRMED_PHYSICAL_UP' for p in pairs.values()),'v3_physical_promotions':sum(r.get('physical_verification_authoritative') is not False for r in releases),'authority_expansions':sum(r.get('grants_input_authority') is not False for r in releases)+sum(a.get('grants_input_authority') is not False for a in acts),'owned_after_empty':bool(releases) and all(r.get('owned_keycodes_after_batch')==[] for r in releases),'post_sample_up':all(isinstance(r.get('physical_key_measurement'),dict) and r['physical_key_measurement'].get('post_sample',{}).get('down') is False for r in releases),'errors':errors}
    result['pass']=result['terminal_completed'] and result['release_rows']==2 and result['down_rows']==2 and result['pair_keys']==['a','d'] and result['bridge_status']=='BOUND_MAP01_PHYSICAL_BATCH' and len(metrics)==2 and result['confirmed_down']==2 and result['confirmed_up']==2 and all(x['precision_pass'] for x in metrics) and result['v3_physical_promotions']==0 and result['authority_expansions']==0 and result['owned_after_empty'] and result['post_sample_up'] and not errors
    return result
