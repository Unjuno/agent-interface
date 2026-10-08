"""Versioned raw-only auditor for the retained A04 child-process construction."""
from pathlib import Path
import hashlib,json,subprocess
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]/'work'/'agent-interface'

def read_case(root,label):
    result=json.loads((root/'RESULT.json').read_text(encoding='utf-8'))
    arm=next(x for x in result['arms'] if x['arm']==label)
    d=root/'results'/label
    stdout=(d/'child-stdout.jsonl').read_text(encoding='utf-8').splitlines()
    stderr=(d/'child-stderr.txt').read_text(encoding='utf-8')
    summary_path=d/'scorer'/'scorer-summary.json'
    summary=json.loads(summary_path.read_text(encoding='utf-8')) if summary_path.exists() else None
    return result,arm,stdout,stderr,summary

def validate(root,result,baseline,candidate,baseline_stdout,candidate_stdout,baseline_stderr,candidate_stderr,baseline_summary,candidate_summary):
    freeze=json.loads((root/'FREEZE.json').read_text(encoding='utf-8'))
    assert result['schema']=='v39-v15-real-child-pipe-construction-result-v1'
    assert result['main_sha']==freeze['main_sha'] and result['candidate_sha']==freeze['candidate_sha']
    assert result['decision']=='PASS_V39_SELECTION_V15_CHILD_PIPE_SCOPED'
    assert Path(baseline['selected_command'][1]).name=='session_map01_v15.py'
    assert Path(candidate['selected_command'][1]).name=='session_map01_v15.py'
    assert baseline['stdout_lines']==baseline_stdout
    assert candidate['stdout_lines']==candidate_stdout
    assert baseline['stderr']==baseline_stderr
    assert candidate['stderr']==candidate_stderr
    b_events=[json.loads(line) for line in baseline_stdout]
    c_events=[json.loads(line) for line in candidate_stdout]
    assert b_events and b_events[0]['event']=='ready'
    assert c_events and c_events[0]['event']=='ready'
    b_commands=[e for e in b_events if e.get('event')=='command']
    c_commands=[e for e in c_events if e.get('event')=='command']
    assert baseline['exit_code']!=0 and 'WinError 10093' in baseline_stderr and not b_commands
    assert candidate['exit_code']==0 and candidate['sent_delayed_command'] and len(c_commands)==1
    assert candidate['command_events']==c_commands
    row=c_commands[0]
    assert json.loads(row['line'])=={'op':'finish'}
    assert row['parsed_command']=={'op':'finish'}
    assert row['command_thread_id']==row['polling_owner_thread_id']==c_events[0]['owner_thread_id']
    assert row['sample_thread_ids'] and set(row['sample_thread_ids'])=={row['command_thread_id']}
    assert row['periodic_samples']>=2
    assert baseline_summary is not None and candidate_summary is not None
    assert baseline['scheduler']==baseline_summary['scheduler']
    assert candidate['scheduler']==candidate_summary['scheduler']
    assert candidate_summary['scheduler']['commands']==1
    assert candidate_summary['scheduler']['samples']==row['periodic_samples']
    assert candidate_summary['scheduler']['samples']>=2
    return {'candidate_command':row['parsed_command'],'command_thread_id':row['command_thread_id'],
        'scheduler_samples':candidate_summary['scheduler']['samples'],'baseline_failure':'WinError 10093',
        'stdout_line_counts':{'baseline':len(baseline_stdout),'candidate':len(candidate_stdout)}}

def verify(root=HERE):
    freeze=json.loads((root/'FREEZE.json').read_text(encoding='utf-8'))
    for rel,expected in freeze['files'].items():
        assert hashlib.sha256((root/rel).read_bytes()).hexdigest()==expected, f'frozen file hash mismatch: {rel}'
    for ref,paths in freeze['git_blobs'].items():
        for path,expected in paths.items():
            actual=subprocess.check_output(['git','rev-parse',f'{ref}:{path}'],cwd=REPO,text=True).strip()
            assert actual==expected, f'Git blob mismatch: {ref}:{path}'
    result,b,bs,be,bsummary=read_case(root,'baseline')
    _,c,cs,ce,csummary=read_case(root,'candidate')
    summary=validate(root,result,b,c,bs,cs,be,ce,bsummary,csummary)
    outputs={}
    for p in sorted(root.rglob('*')):
        if p.is_file() and p.name not in {'AUDIT_V2.json'}:
            outputs[str(p.relative_to(root)).replace('\\','/')]=hashlib.sha256(p.read_bytes()).hexdigest()
    audit={'schema':'v39-v15-real-child-pipe-audit-v2','decision':'PASS_AUDIT_SCOPED','main_sha':freeze['main_sha'],'candidate_sha':freeze['candidate_sha'],'reconstruction':summary,'sha256':outputs}
    (root/'AUDIT_V2.json').write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('PASS_AUDIT_SCOPED')
    print(json.dumps(summary,sort_keys=True))
    return audit

if __name__=='__main__': verify()
