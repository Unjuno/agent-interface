#!/usr/bin/env python3
import argparse, base64, hashlib, json
from collections import defaultdict
from pathlib import Path

TASK='LOCAL-SYSTEM1-MAP01-TYPED-REPRESENTATION-COLLISION-20260917-001'
EXPECTED_REPORT_BLOB='2aed2e7e3f58b4f8b013fc98c79482a4036225ae'

def canonical_label(action):
    x=dict(action)
    x.pop('assessment',None)
    return json.dumps(x, sort_keys=True, separators=(',',':'), ensure_ascii=False)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--rows',required=True); ap.add_argument('--out',required=True)
    a=ap.parse_args(); rows=json.loads(Path(a.rows).read_text())
    assert rows['task']==TASK and rows['report_git_blob']==EXPECTED_REPORT_BLOB
    eligible=[]
    for r in rows['rows']:
        prompt=base64.b64decode(r['prompt_b64'], validate=True)
        psha=hashlib.sha256(prompt).hexdigest()
        eligible_flag=(r['planner_answer_eligible'] is True and r['planner_turn_status']=='completed' and
                       r['action'] is not None and r.get('model_action_discarded') is not True and
                       r['plan_terminal']=='completed')
        rr={'iteration':r['iteration'],'prompt_sha256':psha,'prompt_git_blob':r['prompt_git_blob'],
            'model_image_sha256':r.get('model_image_sha256'),'eligible':eligible_flag}
        if eligible_flag:
            rr['label']=canonical_label(r['action']); eligible.append(rr)
    groups=defaultdict(list)
    for r in eligible: groups[r['prompt_sha256']].append(r)
    collisions=[]
    for sig,grp in sorted(groups.items()):
        labels=sorted({r['label'] for r in grp})
        if len(labels)>1:
            collisions.append({'prompt_sha256':sig,'row_count':len(grp),'distinct_labels':len(labels),
                               'iterations':[r['iteration'] for r in grp],
                               'prompt_git_blobs':sorted({r['prompt_git_blob'] for r in grp}),
                               'model_image_sha256':[r['model_image_sha256'] for r in grp],
                               'labels':labels})
    if len(eligible)<2: decision='HOLD_INSUFFICIENT_ELIGIBLE_ROWS'
    elif collisions: decision='PASS_TYPED_REPRESENTATION_COLLISION_REPLICATED_SCOPED'
    else: decision='HOLD_NO_HELDOUT_COLLISION'
    out={'task':TASK,'formal_invocations':1,'formal_reruns':0,'report_git_blob':rows['report_git_blob'],
         'rows_total':len(rows['rows']),'eligible_rows':len(eligible),'signature_groups':len(groups),
         'collisions':collisions,'decision':decision}
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'decision':decision,'eligible_rows':len(eligible),'collision_groups':len(collisions)},sort_keys=True))
if __name__=='__main__': main()
