from __future__ import annotations
import argparse,collections,json,sys
from pathlib import Path
from rule import decide

def key(d):return tuple((k,d[k]) for k in sorted(d))
def norm(p,d):
    z={'op':d['op']}
    if 'reason' in d:z['reason']=d['reason']
    if 'target' in d:
        ids=[c['id'] for c in p['candidates']];z['target_slot']=ids.index(d['target']) if d['target'] in ids else 'UNBOUND'
    if 'payload_ref' in d:z['payload_arg']='PAYLOAD_PRESENT' if d['payload_ref'] is not None else 'NULL'
    return tuple((k,z[k]) for k in sorted(z))
def sig(p):return (tuple(sorted(p['allowed_operations'])),p['target_admissibility'],p['payload_ref'] is not None,tuple((c['role'],tuple(sorted(c['ops']))) for c in p['candidates']))
def main(path):
    r=json.load(open(path));errs=[];rows=r['rows_detail'];groups=collections.defaultdict(list);exact=falseexec=stale=missing=leak=ordererr=0
    forbidden={'acceptable','hidden_mode','future_effect','post_state','oracle','oracle_facts','desired_action'}
    for x in rows:
        p,o=x['public'],x['oracle'];prop=decide(p);groups[sig(p)].append((p,o));member=key(prop) in {key(a) for a in o['acceptable']};exact+=member
        neg=all(a['op'] in ('NO_LOCAL_ACTION','YIELD') for a in o['acceptable']);falseexec+=neg and prop['op'] in ('CLICK','TYPE_TEXT','SCROLL')
        stale+=p['target_admissibility']=='STALE' and prop['op'] in ('CLICK','TYPE_TEXT','SCROLL')
        missing+=any(a['op']=='TYPE_TEXT' for a in o['acceptable']) and p['payload_ref'] is None
        leak+=bool(set(p)&forbidden);ordererr+=not(o['applied_ns']<=p['receipt_ns']<=x['read_ns']) or p['generation']!=o['generation']
    conflicts=0
    for items in groups.values():
        common=None
        for p,o in items:
            s={norm(p,a) for a in o['acceptable']};common=s if common is None else common&s
        conflicts+=not bool(common)
    metrics=(len(rows),exact,falseexec,stale,missing,leak,ordererr,conflicts)
    if metrics!=(96,96,0,0,0,0,0,0):errs.append(['metrics',metrics])
    if r['formal_invocations']!=1 or r['reruns']!=0:errs.append('identity')
    if r['decision']!='PASS_PRIVATE_X11_OPERATION_TARGET_CONTRACT_SCOPED':errs.append('decision')
    if r['task_input_actions'] or r['model_calls']:errs.append('actions')
    if r['unique_x11_frame_hashes']<4:errs.append('x11_witness')
    print(json.dumps({'pass':not errs,'errors':errs,'metrics':metrics},sort_keys=True));raise SystemExit(bool(errs))
if __name__=='__main__':ap=argparse.ArgumentParser();ap.add_argument('result');a=ap.parse_args();main(a.result)
