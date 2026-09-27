"""Offline raw PNG/trace/persisted-SVG audit. Never called by live controller."""
from pathlib import Path
import argparse,hashlib,json,statistics
import numpy as np
from PIL import Image
from oracle import svg_snapshot
from resolver import resolve,center_gate
from reference_controller_v3 import Matcher
import cv2
cv2.setNumThreads(1)

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('out');a=p.parse_args();root=Path(a.out);base=Path(__file__).parent
    plan=json.loads((base/'prereg.json').read_text());rows=[];counts=dict(images=0,inputs=0,pointers=0,releases=0,target_gates=0)
    for name,d in plan['source_sha256'].items():assert sha(base/name)==d, name
    assert (root/'COMPLETED.json').exists(), 'incomplete allocation'
    for spec in plan['schedule']:
        case=root/spec['case_id'];score=json.loads((case/'score.json').read_text());trace=json.loads((case/'controller/trace.json').read_text());config=json.loads((case/'config.json').read_text())
        assert 'error' not in score and score['controller_exit_code']==0
        assert all(score[k]==spec[k] for k in ('scenario','mode','seed','pan'))
        ref=np.asarray(Image.open(case/'reference.png').convert('RGB'));tpl=np.asarray(Image.open(case/'template.png').convert('RGB'));image=None;last_capture=None;prediction=None;gates=[];m=None
        for event in trace['events']:
            if 'image' in event:
                image=np.asarray(Image.open(case/'controller'/event['image']).convert('RGB'))
                assert hashlib.sha256(image.tobytes()).hexdigest()==event['rgb_sha256']
                assert event['capture_ns']>=event['capture_started_ns'];last_capture=event['capture_ns'];counts['images']+=1
                if event['kind']=='scene_observation':
                    m=Matcher(ref).locate(image)
                    assert m['valid']
                    prediction=cv2.perspectiveTransform(np.float32(config['point']).reshape(1,1,2),np.asarray(m['homography']))[0,0].tolist()
            if event['kind']=='target_gate':
                assert image is not None and prediction is not None
                recomputed=resolve(image,tpl,prediction) if spec['mode']=='footprint' else center_gate(ref,image,config['point'],prediction)
                assert recomputed==event['result'], (spec['case_id'],recomputed,event['result'])
                assert event['eligible']==bool(recomputed['eligible'] and event['age_ns']<=500_000_000 and event['stable']);gates.append(event);counts['target_gates']+=1
            if event['kind'] in ('input','pointer'):
                r=event['release'];assert r['verified'] is True and not r['keys_down'] and not r['buttons_down']
                assert r['verified_ns']>=event['up_started_ns'];counts['inputs' if event['kind']=='input' else 'pointers']+=1
                if event['kind']=='pointer':assert len(gates)==2 and all(g['eligible'] for g in gates)
        owner_rows=trace['owner_records']+score['setup_owner_records']+score['reference_owner_records']
        for record in owner_rows:
            if record.get('event')=='owner_release':
                assert record['verified'] and record['keys_down']==[] and record['buttons_down']==[];counts['releases']+=1
        before,ar=svg_snapshot(case/'before.svg');after,br=svg_snapshot(case/'current-board.svg')
        lost=sorted(before.keys()-after.keys());added=sorted(after.keys()-before.keys());changed=sorted(k for k in before.keys()&after.keys() if before[k]!=after[k]);unchanged=(case/'before.svg').read_bytes()==(case/'current-board.svg').read_bytes()
        expected=spec['scenario'] in ('stable','moved_decoy')
        success=(lost==['task-target'] and not added and not changed and ar==br) if expected else (unchanged and not any(e['kind'] in ('input','pointer') for e in trace['events']))
        assert bool(success)==score['independent_success'] and lost==score['removed_ids'] and changed==score['changed_ids']
        rows.append(dict(case_id=spec['case_id'],scenario=spec['scenario'],mode=spec['mode'],seed=spec['seed'],success=bool(success),decision=trace['decision'],removed=lost,wall_ms=score['controller_wall_ns']/1e6,observations=score['observations'],target_compute_ms=[g['compute_ns']/1e6 for g in gates],target_rmse=[g['result'].get('best_rmse') for g in gates],candidate_status=[g['result']['status'] for g in gates],source_sha256=score['sources']))
    by={}
    for mode in ('center','footprint'):
        r=[x for x in rows if x['mode']==mode]
        by[mode]=dict(cases=len(r),successes=sum(x['success'] for x in r),wrong_target_deletions=sum('decoy' in x['removed'] for x in r),by_scenario={s:dict(passed=sum(x['success'] for x in r if x['scenario']==s),n=sum(x['scenario']==s for x in r)) for s in ('stable','moved_decoy','replaced_square','missing','duplicate')},wall_ms_median=statistics.median(x['wall_ms'] for x in r),wall_ms_range=[min(x['wall_ms'] for x in r),max(x['wall_ms'] for x in r)])
    candidate=by['footprint'];passed=candidate['successes']==15 and candidate['wrong_target_deletions']==0
    result=dict(schema='target-footprint-reacquire-audit-v1',integrity_pass=True,disposition='PASS_SCOPED_CANDIDATE' if passed else 'REJECT_OR_HOLD_CANDIDATE',counts=counts,summary=by,rows=rows,model_calls=0,security_proof=False,scorer_never_controller_input=True)
    (root/'audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
if __name__=='__main__':main()
