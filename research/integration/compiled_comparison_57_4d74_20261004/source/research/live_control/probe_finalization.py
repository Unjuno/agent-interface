"""Faults preserve stage boundaries and never turn unknown evaluation into false."""
import hashlib,json
from pathlib import Path
from finalization import finalize
HERE=Path(__file__).resolve().parent
out=HERE/'results/finalization-01';out.mkdir(exist_ok=False)
rows=[]
for case in ('success','task_failure','close_error','score_error','invalid_score','publish_error','unconfirmed_output'):
    calls=[]
    def close():
        calls.append('close')
        if case=='close_error':raise OSError('injected close failure')
    def score():
        calls.append('score')
        if case=='score_error':raise OSError('injected scorer failure')
        if case=='invalid_score':return {'actual':None}
        return dict(success=case!='task_failure',actual=[532,590])
    def publish(record):
        calls.append('publish')
        if case=='publish_error':raise BrokenPipeError('injected output failure')
        return case!='unconfirmed_output'
    result=finalize('final',close,score,publish)
    expected={'close_error':'close_admission','score_error':'evaluate','invalid_score':'evaluate','publish_error':'publish','unconfirmed_output':'publish'}.get(case)
    if expected:
        assert result['status']=='finalization_error' and result['failure_stage']==expected
        assert not result['output_flushed']
        if expected!='publish':assert result['evaluation'] is None and 'publish' not in calls
        else:assert result['evaluation']['success'] is True
    else:assert result['status']=='finished' and result['evaluation']['success']==(case=='success') and result['output_flushed']
    if case=='close_error':assert calls==['close']
    rows.append(dict(case=case,calls=calls,result=result))
(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
(out/'sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),HERE/'finalization.py')},indent=2)+'\n')
print('7 finalization cases pass; evaluation failure, task failure and output failure remain distinct.')
