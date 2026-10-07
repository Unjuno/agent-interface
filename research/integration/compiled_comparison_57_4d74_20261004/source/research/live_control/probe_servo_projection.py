"""Matched source-trace comparison of receipt and local-review projections."""
import hashlib,json
from pathlib import Path
from presentation_v2 import Presentation as Baseline
from presentation_v3 import Presentation as Candidate
HERE=Path(__file__).resolve().parent;out=HERE/'results/servo-projection-01';out.mkdir(exist_ok=False)
names=['servo-recovery-02','servo-stall-02/yield_timeout','servo-occlusion-02/replacement','guided-self-use-02']
rows=[];sources=[Path(__file__),HERE/'presentation.py',HERE/'presentation_v2.py',HERE/'presentation_v3.py']
for name in names:
    path=HERE/'results'/name/'events.jsonl';sources.append(path)
    events=[json.loads(x) for x in path.read_text().splitlines()];original=json.dumps(events,sort_keys=True)
    outputs=[]
    for cls in (Baseline,Candidate):
        p=cls();result=[]
        for event in events:result.extend(p.project(event))
        outputs.append(result)
    assert json.dumps(events,sort_keys=True)==original
    baseline,candidate=outputs
    for event in events:
        if event['event'] in ('servo_outcome','cancel_requested','rejected','environment_fixture') or (event['event']=='servo_feedback' and event['reason']!='correct'):
            assert event in candidate,'critical evidence missing'
    assert [r for r in baseline if r['event']=='terminal']==[r for r in candidate if r['event']=='terminal']
    if name=='guided-self-use-02':assert baseline==candidate,'manual reply flow changed'
    encoded=[''.join(json.dumps(r)+'\n' for r in arm) for arm in outputs]
    (out/(name.replace('/','_')+'.jsonl')).write_text(encoded[1])
    rows.append(dict(corpus=name,baseline_json_bytes=len(encoded[0].encode()),candidate_json_bytes=len(encoded[1].encode()),baseline_observations=sum(r['event']=='observation' for r in baseline),candidate_observations=sum(r['event']=='observation' for r in candidate)))
# Unknown critical event is forwarded while local execution is active.
p=Candidate();p.project(dict(event='step_started',id='a',step=0,operation='pointer_servo'))
e=dict(event='future_critical_event',id='a',reason='test');assert e in p.project(e)
(out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},indent=2)+'\n')
(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
