from __future__ import annotations
import base64, hashlib, json, sys
from collections import defaultdict
from pathlib import Path


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

def git_blob(data: bytes) -> str:
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()

def eligible(r):
    e=r['eligibility']
    return e['planner_turn_status']=='completed' and e['planner_answer_eligible'] is True and e['model_action_discarded'] is False and e['plan_terminal']=='completed' and r['teacher_label'] is not None

def derive_prior(rows, iteration):
    by={r['iteration']:r for r in rows}
    for j in range(iteration-1,-1,-1):
        r=by.get(j)
        if r is None: continue
        e=r['eligibility']
        if e['model_action_discarded'] is False and e['plan_terminal']=='completed':
            recs=r.get('own_effect_receipts')
            if recs:
                q=recs[-1]
                return {'kind':'RECEIPT','action':q['action'],'extent':q['extent'],'result':q['result'],'source_iteration':j}
            return {'kind':'UNKNOWN','source_iteration':j}
    return {'kind':'NONE'}

def receipt_repr(r):
    if r['kind'] in ('NONE','UNKNOWN'):
        return {'kind':r['kind']}
    return {'kind':'RECEIPT','action':r['action'],'extent':r['extent'],'result':r['result']}

def groups(rows, enriched=False):
    g=defaultdict(list)
    for r in rows:
        if not eligible(r): continue
        p=base64.b64decode(r['prompt_b64'])
        if enriched:
            sig=hashlib.sha256(p+b'\0LAST_EFFECT\0'+canon(receipt_repr(derive_prior(rows,r['iteration']))).encode()).hexdigest()
        else:
            sig=hashlib.sha256(p).hexdigest()
        g[sig].append((r['iteration'],canon(r['teacher_label'])))
    out=[]
    for sig, vals in sorted(g.items()):
        labels=sorted(set(v for _,v in vals))
        if len(labels)>1:
            out.append({'signature':sig,'iterations':[i for i,_ in vals],'distinct_labels':len(labels),'labels':labels})
    return out, len(g)

def main():
    fixture=json.loads(Path(sys.argv[1]).read_text())
    rows=fixture['rows']
    errors=[]
    if fixture['source'] != {
        'v31_report_git_blob':'2aed2e7e3f58b4f8b013fc98c79482a4036225ae',
        'source_rows_git_blob':'4ab9129253b0c2d976c932d07ed744528ea23734',
        'predecessor_result_git_blob':'d08d66c07ed70cd4f02609a1122df664b90f1a2c'}:
        errors.append('source_identity')
    if len(rows)!=8 or [r['iteration'] for r in rows]!=list(range(8)):
        errors.append('row_identity')
    for r in rows:
        p=base64.b64decode(r['prompt_b64'])
        if git_blob(p)!=r['prompt_git_blob']:
            errors.append(f"prompt_blob:{r['iteration']}")
        if eligible(r)!=r['eligible_expected']:
            errors.append(f"eligibility:{r['iteration']}")
        if derive_prior(rows,r['iteration'])!=r['last_effect_receipt']:
            errors.append(f"prior_receipt:{r['iteration']}")
    erows=[r for r in rows if eligible(r)]
    pcol, pgroups=groups(rows,False)
    ecol, egroups=groups(rows,True)
    if len(erows)!=5: errors.append('eligible_count')
    if len(pcol)!=1 or pcol[0]['iterations']!=[1,2]: errors.append('predecessor_collision')
    if derive_prior(rows,1)!={'kind':'NONE'}: errors.append('iter1_receipt')
    if derive_prior(rows,2)!={'kind':'RECEIPT','action':'retreat_fire','extent':'short','result':'visible_change','source_iteration':1}: errors.append('iter2_receipt')
    if ecol: errors.append('enriched_collision')
    decision='PASS_LAST_EFFECT_REPRESENTATION_V31_R2_SCOPED' if not errors else ('HOLD_REPRESENTATION_STILL_AMBIGUOUS' if errors==['enriched_collision'] else 'FAIL_INTEGRITY')
    out={
      'task':fixture['task'],'formal_invocations':1,'reruns':0,'rows_total':len(rows),'eligible_rows':len(erows),
      'prompt_signature_groups':pgroups,'prompt_collisions':pcol,'enriched_signature_groups':egroups,'enriched_collisions':ecol,
      'derived_receipts':{str(r['iteration']):derive_prior(rows,r['iteration']) for r in rows},
      'source':fixture['source'],'errors':errors,'decision':decision,'pass':not errors}
    Path(sys.argv[2]).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))
    raise SystemExit(0 if not errors else 1)
if __name__=='__main__': main()
