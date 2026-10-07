from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parent/'sample-pair-01'
cells=[]
for p in sorted(root.glob('[0-9][0-9]-*')):
    result=json.loads((p/'RESULT.json').read_text());final=json.loads((p/'FINAL.json').read_text())
    rows=[json.loads(x) for x in (p/'scorer-last-action.jsonl').read_text().splitlines()]
    start=result['accepted']['emit_ns'];end=start+600_000_000
    window=[r for r in rows if r['sample_started_ns']>=start and r['sample_returned_ns']<=end and r['coherent_tic']]
    active=[r for r in window if r['action'][r['buttons'].index('Button.MOVE_RIGHT')]!=0]
    allneutral=all(not any(r['action']) for r in window)
    terminal=result['terminal']
    cells.append({'cell':p.name,'samples':len(window),'move_right_samples':len(active),'all_neutral':allneutral,'window_ns':[start,end],'terminal_after_window_ns':terminal['terminal_ns']-end,'final':final,'score':result['score'],'raw_sha256':hashlib.sha256((p/'scorer-last-action.jsonl').read_bytes()).hexdigest()})
good=len(cells)==6 and all(c['samples']>0 and c['final']=={'child_exit':0,'external_rescue':False,'reader_alive':False} and (c['all_neutral'] if c['cell'].endswith('coast') else c['move_right_samples']>0) for c in cells)
audit={'disposition':'PASS_SAMPLED_INPUT_CONTRAST_SCOPED' if good else 'FAIL_OR_HOLD_SAMPLED_CONTRAST','cells':cells,'limits':'Post-result saved-only authored audit, not independent review. Samples are not continuous occupancy or exact transitions. Runtime overhead/trajectory remain unmatched; no useful recovery efficacy.'}
(root/'SAVED_AUDIT.json').write_text(json.dumps(audit,indent=2));print(json.dumps(audit,indent=2))
