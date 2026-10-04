"""Historical wall-time attribution, not a counterfactual sampling-policy benchmark."""
import json
from pathlib import Path
from PIL import Image
from session_v4 import Decoder
from report_pages_v2 import digest

HERE=Path(__file__).resolve().parent
CASES=['field-table-live-01/runtime','gui-effect-live-01/runtime','presentation-assistant-02']
rows=[]
for case in CASES:
    root=HERE/'results'/case
    raw=[json.loads(line) for line in (root/'events.jsonl').read_text().splitlines()]
    decoder=Decoder('live-control');previous=None;steps=[];active={};observations=[]
    for event in raw:
        kind=event['event'];key=(event.get('id'),event.get('step'))
        if kind=='step_started':
            item=dict(program=key[0],step=key[1],operation=event['operation'],start_ns=event['issued_ns'],
                      observations=0,exact_repeats=0,capture_ms=0.,image_prepare_ms=0.,bracket_ms=0.,bracket_samples=0)
            steps.append(item);active[key]=item
        elif kind=='observation':
            sequence=event['sequence'];frame=decoder.accept((root/f'{sequence:03d}.ait').read_bytes())
            with Image.open(root/Path(event['image']).name) as image:
                assert (image.width,image.height,image.mode,image.tobytes())==(frame.width,frame.height,frame.mode,frame.pixels)
            repeat=previous==frame;previous=frame
            observation=dict(sequence=sequence,exact_repeat_of_previous=repeat,capture_ns=event['capture_ns'],
                             capture_ms=event['capture_ms'],image_prepare_ms=event.get('image_prepare_ns',0)/1e6)
            if 'input_state_before' in event and 'emit_started_ns' in event:
                start=event['input_state_before']['sample_started_ns'];end=event['emit_started_ns']
                assert start<=event['capture_ns']<=event['input_state_after']['sample_finished_ns']<=end
                observation['bracket_start_ns']=start;observation['bracket_end_ns']=end
                observation['bracket_ms']=(end-start)/1e6
            observations.append(observation)
            if key in active:
                item=active[key];item['observations']+=1;item['exact_repeats']+=int(repeat)
                item['capture_ms']+=observation['capture_ms'];item['image_prepare_ms']+=observation['image_prepare_ms']
                if 'bracket_ms' in observation:
                    item['bracket_ms']+=observation['bracket_ms'];item['bracket_samples']+=1
        elif kind=='step_completed' and key in active:
            item=active.pop(key);item['end_ns']=event['completed_ns'];item['elapsed_ms']=(item['end_ns']-item['start_ns'])/1e6
        elif kind=='settle_result' and key in active:
            active[key]['settle_reason']=event['reason']
    assert not active,'incomplete steps must not be silently profiled as completed'
    # Bracket intervals include capture/encoding/publication/state sampling. Do not
    # add capture_ms or image_prepare_ms to them: these measures overlap.
    spans=sorted((o['bracket_start_ns'],o['bracket_end_ns']) for o in observations if 'bracket_ms' in o)
    assert all(a[1]<=b[0] for a,b in zip(spans,spans[1:]))
    first=observations[0]['capture_ns'];evaluation=next(e for e in reversed(raw) if e['event']=='independent_evaluation')
    completed_ms=sum(s['elapsed_ms'] for s in steps)
    rows.append(dict(case=case,source_sha256=digest((root/'events.jsonl').read_bytes()),
                     initial_capture_to_evaluation_ms=(evaluation['known_ns']-first)/1e6,
                     completed_step_ms=completed_ms,
                     total_bracket_ms=sum(o.get('bracket_ms',0) for o in observations),
                     bracket_coverage=sum('bracket_ms' in o for o in observations),exact_frames=len(observations),
                     exact_repeats=sum(o['exact_repeat_of_previous'] for o in observations),steps=steps,
                     observations=observations))
result=dict(format='observation-cost-profile-v1',profiler_sha256=digest(Path(__file__).read_bytes()),rows=rows,
            limits='Existing heterogeneous traces, not causal cross-app comparison. Bracket wall-time overlaps capture and image publication, excludes some entry/emit work. Missing bracket is unavailable, not zero cost. Exact repeats known only after sampling; no claim they can safely be skipped. No model receipt/token/CPU accounting.')
out=HERE/'results/observation-cost-01';out.mkdir(exist_ok=False)
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps([{k:v for k,v in r.items() if k not in ('steps','observations')} for r in rows]))
print(json.dumps([dict(case=r['case'],steps=[s for s in r['steps'] if s['program'] in ('edit','recover')]) for r in rows]))
