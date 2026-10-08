#!/usr/bin/env python3
import argparse, base64, hashlib, json
from collections import defaultdict
from pathlib import Path

TASK='LOCAL-SYSTEM1-MAP01-TYPED-REPRESENTATION-COLLISION-20260917-001'
REPORT='2aed2e7e3f58b4f8b013fc98c79482a4036225ae'

def canon(action):
    x=dict(action); x.pop('assessment',None)
    return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--rows',required=True); ap.add_argument('--result',required=True); ap.add_argument('--out',required=True)
    a=ap.parse_args(); src=json.loads(Path(a.rows).read_text()); got=json.loads(Path(a.result).read_text())
    errors=[]
    if src.get('task')!=TASK or got.get('task')!=TASK: errors.append('task')
    if src.get('report_git_blob')!=REPORT or got.get('report_git_blob')!=REPORT: errors.append('report_blob')
    eligible=[]
    for r in src['rows']:
        try: p=base64.b64decode(r['prompt_b64'],validate=True)
        except Exception: errors.append(f"prompt_b64:{r.get('iteration')}"); continue
        e=(r.get('planner_answer_eligible') is True and r.get('planner_turn_status')=='completed' and r.get('action') is not None and r.get('model_action_discarded') is not True and r.get('plan_terminal')=='completed')
        if e: eligible.append((r['iteration'],hashlib.sha256(p).hexdigest(),canon(r['action']),r.get('prompt_git_blob'),r.get('model_image_sha256')))
    groups=defaultdict(list)
    for x in eligible: groups[x[1]].append(x)
    cols=[]
    for sig,g in sorted(groups.items()):
        labs=sorted({x[2] for x in g})
        if len(labs)>1: cols.append((sig,tuple(x[0] for x in g),len(labs)))
    expected='HOLD_INSUFFICIENT_ELIGIBLE_ROWS' if len(eligible)<2 else ('PASS_TYPED_REPRESENTATION_COLLISION_REPLICATED_SCOPED' if cols else 'HOLD_NO_HELDOUT_COLLISION')
    if got.get('formal_invocations')!=1 or got.get('formal_reruns')!=0: errors.append('formal_counts')
    if got.get('rows_total')!=len(src['rows']) or got.get('eligible_rows')!=len(eligible): errors.append('row_counts')
    if got.get('signature_groups')!=len(groups): errors.append('group_count')
    if len(got.get('collisions',[]))!=len(cols): errors.append('collision_count')
    if got.get('decision')!=expected: errors.append('decision')
    audit={'task':TASK,'audit':'PASS' if not errors else 'FAIL','errors':errors,'recomputed_decision':expected,'eligible_rows':len(eligible),'collision_groups':len(cols),'report_git_blob':REPORT}
    Path(a.out).write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n')
    print(json.dumps(audit,sort_keys=True))
if __name__=='__main__': main()
