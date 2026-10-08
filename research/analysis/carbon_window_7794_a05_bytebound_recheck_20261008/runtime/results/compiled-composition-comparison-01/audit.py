"""Read-only finite raw census; original pixels, input programs and task records."""
import hashlib,json
from pathlib import Path
from PIL import Image

def read(p): return json.loads(p.read_text())
def require(c,m):
    if not c: raise ValueError(m)
def audit(root):
    allocation=read(root/'ALLOCATION.json'); rows=[]; pair_ops={}
    for spec in allocation['cases']:
        case=root/spec['name']; positive=spec['variant']=='positive'; count=2 if positive else 1
        require(read(case/'allocation.json')['token']==spec['token'],'token allocation changed')
        cleanup=read(case/'cleanup.json'); require(cleanup['status']=='closed' and len(cleanup['child_exit_codes'])==2,'owner not terminal')
        commands=[read(p) for p in sorted((case/'commands').glob('*.json'))]
        require([c['op'] for c in commands]==['observe','mint','mint','run','close'],'unexpected request/replay inventory')
        common=read(case/'bridge/method-common.json'); require(common['outcome']==('TASK_SUCCEEDED' if positive else 'SAFE_YIELD'),'wrong outcome')
        require(common['completed_inputs']==count and common['release_verified'] is True,'wrong prefix/release')
        if not positive: require(common['reason']=='unknown_state','wrong changed stop')
        programs=[read(p) for p in (case/'bridge').glob('program-*.json')]; require(len(programs)==count,'wrong input inventory')
        programs.sort(key=lambda p:p['source']['observation_seq']); pair_ops.setdefault(spec['variant'],[]).append([p['ops'] for p in programs])
        require([op['text'] for p in programs for op in p['ops'] if op['op']=='text']==[spec['token']],'wrong/collateral text')
        results=[read(p) for p in (case/'bridge').glob('result-*.json') if 'execution' in read(p)]
        require(len(results)==count,'wrong input receipt inventory')
        require(all(r['status']=='completed' and r.get('recovery_required') is False for r in results),'input incomplete')
        require(all(r['execution']['releases'] and all(s['verified'] and s['keys_down']==[] and s['buttons_down']==[] for s in r['execution']['releases']) for r in results),'nonneutral raw release')
        captures={read(p)['sequence']:read(p) for p in (case/'bridge').glob('observation-*.json')}
        for p in programs:
            source=captures[p['source']['observation_seq']]
            require(p['authority']['expires_at_ns'] <= source['capture_ns']+1_500_000_000,'capture freshness deadline renewed')
        for n in captures.values():
            a=n['native']['artifact']; require(hashlib.sha256(Path(a['path']).read_bytes()).hexdigest()==a['sha256'],'image corrupt')
            require(a['source_raw_sha256']==n['native']['sha256'],'capture identity mismatch')
        raw=read(case/'bridge/method-raw.json'); observations=raw['observations'] if spec['route']=='compiled' or not positive else None
        if observations is None:
            # Baseline returns legacy full results, so reconstruct the fixed
            # local observations from explicit effect trace references;
            # the initial method capture is 2 after the reviewed source 1.
            observations=[{'sequence':2}]+[{'sequence':int(e['evidence_ref'].split('-')[-1])} for e in read(case/'bridge/method-timing.json')['trace'] if e['event']=='effect_checked' and e['status']=='succeeded']
        require(len(observations)==count+1,'wrong local observation inventory')
        first=Image.open(captures[1]['native']['artifact']['path']).convert('RGB')
        boxes={c['alias']:(c['point'][0]-12,c['point'][1]-12,c['point'][0]+12,c['point'][1]+12) for c in commands if c['op']=='mint'}
        for o in observations:
            n=captures[o['sequence']]; rgb=Image.open(n['native']['artifact']['path']).convert('RGB'); color=rgb.getpixel((50,160))
            values={'field_present':rgb.crop(boxes['field']).tobytes()==first.crop(boxes['field']).tobytes(),'submit_present':rgb.crop(boxes['save']).tobytes()==first.crop(boxes['save']).tobytes(),'field_accepted':color in ((40,180,60),(30,110,60)),'saved_cue':color==(30,110,60)}
            if 'predicates' in o: require(o['predicates']==values,'predicate/image mismatch')
            if o is observations[1]: require(values['field_accepted'] and values['submit_present'] is positive,'wrong intermediate decision evidence')
        events=[json.loads(l) for l in (case/'events.jsonl').read_text().splitlines()]; saves=[e for e in events if e['event']=='save']
        require(saves==([{'event':'save','value':spec['token'],'eligible':True}] if positive else []),'wrong independent save outcome')
        require([e for e in events if e['event']=='value_changed'][-1]['value']==spec['token'],'wrong final entry')
        timing=read(case/'bridge/method-timing.json'); accepted=[e for e in timing['trace'] if e['action']=='enter' and e['status']=='succeeded']
        require(len(accepted)==1,'missing local effect timing')
        rows.append({'case':spec['name'],'route':spec['route'],'variant':spec['variant'],'outcome':common['outcome'],'independent_saves':len(saves),'completed_inputs':count,'local_observations':len(observations),'all_native_captures':len(captures),'control_requests':len(commands),'primary_original_images':2,'program_emissions':sum(r['execution']['program_emissions'] for r in results),'fixed_wait_ms':sum(op['timeout_ms'] for p in programs for op in p['ops'] if op['op']=='wait_update'),'local_method_ms':common['local_elapsed_ns']/1e6,'first_local_effect_known_ms':(accepted[0]['known_ns']-timing['started_ns'])/1e6,'first_model_feedback_ms':None,'model_semantic_awareness_ms':None,'child_exit_codes':cleanup['child_exit_codes']})
    require(all(ops[0]==ops[1] for ops in pair_ops.values()),'paired input programs differ')
    return rows
if __name__=='__main__':print(json.dumps(audit(Path(__file__).resolve().parent),indent=2))
