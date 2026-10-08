import argparse,hashlib,json
from pathlib import Path
REV='fallback-v1'

def sid(scope,g,sup):
    obj={'authority':False,'fallback_revision':REV,'generation':g,'scope':scope,'supported':sorted(sup)}
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def truth(cur,snap,req):
    if not snap['runtime_owned'] or snap['authority'] or snap['fallback_revision']!=REV:return ('INVALID',None,False)
    if snap['snapshot_id']!=sid(snap['scope'],snap['generation'],snap['supported']):return ('INVALID',None,False)
    if snap['snapshot_id']!=sid(cur['scope'],cur['generation'],cur['supported']):return ('INVALID',None,False)
    S=set(snap['supported'])
    if req in S:return ('DIRECT',req,False)
    if req=='XTEST_INPUT' and 'CORE_INPUT_FALLBACK' in S:return ('FALLBACK','CORE_INPUT_FALLBACK',False)
    return ('UNSUPPORTED',None,False)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('result');ap.add_argument('--out',required=True);a=ap.parse_args();r=json.loads(Path(a.result).read_text());errors=[]
    expected={'E_FRESH_A':('DIRECT','XTEST_INPUT'),'E_WRONG_SCOPE_B':('INVALID',None),'D_STALE_E_SNAPSHOT':('INVALID',None),'D_FRESH_A':('FALLBACK','CORE_INPUT_FALLBACK'),'D_WRONG_SCOPE_B':('INVALID',None)}
    for i,x in enumerate(r['rows']):
        kind,sel,grant=truth(x['current'],x['snapshot'],x['request']);cand=x['candidate'];ck=cand['disposition'] if cand['disposition'] in ('DIRECT','FALLBACK','UNSUPPORTED') else 'INVALID'
        if (ck,cand['selected'],cand['grants_action_authority'])!=(kind,sel,grant):errors.append(f'{i}:candidate')
        if (kind,sel)!=expected[x['scenario']]:errors.append(f'{i}:expected')
        if x['before']['focus_id']!=x['after']['focus_id']:errors.append(f'{i}:focus')
        if x['before']['cap']['present']!=x['after']['cap']['present']:errors.append(f'{i}:cap')
        if x['task_input_calls'] or x['xtest_action_calls']:errors.append(f'{i}:input')
    for p in r['pairs']:
        if p['E']['cap_reply']['present']!=1:errors.append(f"pair{p['pair']}:Ecap")
        if not p['E_close']['socket_disappeared']:errors.append(f"pair{p['pair']}:socket")
        if p['D']['cap_reply']['present']!=0:errors.append(f"pair{p['pair']}:Dcap")
    o={'pass':not errors,'errors':errors[:100],'checked_rows':len(r['rows']),'checked_pairs':len(r['pairs']),'method':'raw QueryExtension/lifecycle/snapshot contract audit; imports no candidate resolver'};Path(a.out).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(o,indent=2,sort_keys=True));raise SystemExit(0 if o['pass'] else 5)
