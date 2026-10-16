"""Replay receipt projection against successful, failed and blocked-output evidence."""
import hashlib,json
from pathlib import Path
from presentation_v2 import Presentation
HERE=Path(__file__).resolve().parent
out=HERE/'results/review-receipt-01';out.mkdir(exist_ok=False)
corpora=['servo-recovery-01','servo-self-use-01','servo-stall-02/yield_timeout','servo-distractor-03/red']
rows=[];sources=[Path(__file__),HERE/'presentation.py',HERE/'presentation_v2.py']
for name in corpora:
    path=HERE/'results'/name/'events.jsonl';sources.append(path)
    events=[json.loads(x) for x in path.read_text().splitlines()];p=Presentation();latest=None;terminals=0;reused=0;prior=0;delivered=[]
    for e in events:
        original=json.dumps(e,sort_keys=True)
        if e['event']=='observation':latest=e
        result=p.project(e);assert json.dumps(e,sort_keys=True)==original
        delivered.extend(result)
        if e['event']=='terminal':
            terminals+=1;r=result[-1];assert r['event']=='terminal' and r['review']['runtime_ns']==e['terminal_ns']
            observation=r['review']['observation']
            assert observation['sequence']==latest['sequence'] and observation['image']==latest['image']
            assert observation['from_this_program']==(latest['id']==e['id'])
            assert (path.parent/Path(observation['image']).name).exists()
            reused+=bool(observation['image_reused']);prior+=not observation['from_this_program']
        if e['event'] not in ('observation','step_started','step_completed','input_admission','terminal'):
            assert e in result,'critical/unknown event dropped'
    (out/(name.replace('/','_')+'.jsonl')).write_text(''.join(json.dumps(e)+'\n' for e in delivered))
    rows.append(dict(corpus=name,terminals=terminals,reused_image_receipts=reused,prior_program_receipts=prior))
# No observation yet is explicit, not a guessed filename.
p=Presentation();r=p.project(dict(event='terminal',id='empty',terminal_ns=1))[-1]
assert r['review']['observation'] is None
(out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},indent=2)+'\n')
(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
