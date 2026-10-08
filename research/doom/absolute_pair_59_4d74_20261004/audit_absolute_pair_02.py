from pathlib import Path
import json
root=Path(__file__).resolve().parent/'sample-pair-02';cells=[]
for p in sorted(root.glob('[0-9][0-9]-*')):
    result=json.loads((p/'RESULT.json').read_text());events=[json.loads(x) for x in (p/'events.jsonl').read_text().splitlines()]
    start=result['window_start_ns'];end=result['window_end_ns']
    samples=[json.loads(x) for x in (p/'scorer-last-action.jsonl').read_text().splitlines()]
    selected=[s for s in samples if s['coherent_tic'] and start<=s['sample_started_ns'] and s['sample_returned_ns']<=end]
    admissions=[e for e in events if e.get('event')=='input_admission']
    releases=[e for e in events if e.get('event')=='input_released']
    cells.append({'cell':p.name,'samples':len(selected),'active_samples':sum(any(s['action']) for s in selected),'status':result['terminal']['status'],'terminal_after_deadline_ms':(result['terminal']['terminal_ns']-end)/1e6,'late_admissions':[e for e in admissions if e['admitted_ns']>end],'admissions':len(admissions),'releases':releases,'terminal_release':result['terminal']['release'],'final':json.loads((p/'FINAL.json').read_text())})
(root/'SAVED_AUDIT.json').write_text(json.dumps({'scope':'post-result saved inspection; independent review pending; no physical or efficacy certification','cells':cells},indent=2));print(json.dumps(cells,indent=2))
