"""Independent raw-only audit of the frozen V39/V15 child pipe run."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent; REPO=ROOT.parents[1]/'work'/'agent-interface'
freeze=json.loads((ROOT/'FREEZE.json').read_text(encoding='utf-8'))
for rel,expected in freeze['files'].items():
    got=hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
    assert got==expected, f'file hash mismatch {rel}'
for ref,paths in freeze['git_blobs'].items():
    for path,expected in paths.items():
        got=subprocess.check_output(['git','rev-parse',f'{ref}:{path}'],cwd=REPO,text=True).strip()
        assert got==expected, f'Git blob changed for {ref}:{path}'
result=json.loads((ROOT/'RESULT.json').read_text(encoding='utf-8'))
assert result['decision']=='PASS_V39_SELECTION_V15_CHILD_PIPE_SCOPED'
base=next(x for x in result['arms'] if x['arm']=='baseline'); cand=next(x for x in result['arms'] if x['arm']=='candidate')
for arm in (base,cand): assert Path(arm['selected_command'][1]).name=='session_map01_v15.py'
assert base['exit_code']!=0 and 'WinError 10093' in base['stderr'] and not base['command_events']
assert cand['exit_code']==0 and cand['sent_delayed_command'] and len(cand['command_events'])==1
row=cand['command_events'][0]
assert row['line']=='{"op":"finish"}'
assert row['command_thread_id']==row['polling_owner_thread_id']
assert row['sample_thread_ids'] and set(row['sample_thread_ids'])=={row['command_thread_id']}
assert row['periodic_samples']>=2 and cand['scheduler']['samples']>=2
assert len(result['arms'])==2
print('PASS_AUDIT: main/V39 selector and V15 child sources match frozen Git blobs; one baseline failure and one candidate command/sample trace reconcile')
