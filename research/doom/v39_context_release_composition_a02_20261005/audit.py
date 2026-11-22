#!/usr/bin/env python3
"""Read-only provenance and result audit for A02."""
import json, re, subprocess
from pathlib import Path
root=Path(__file__).parent
freeze=json.loads((root/'FREEZE.json').read_text())
composition=json.loads((root/'COMPOSITION.json').read_text())
result=json.loads((root/'RESULT.json').read_text())
def git(*args): return subprocess.check_output(['git',*args],text=True).strip()
assert git('rev-parse','origin/main') == freeze['base_main']
prs={'pr_7783_projection_fix_based_on_7602':'refs/remotes/origin/pr/7783','pr_7750_owner_admission_identity':'refs/remotes/origin/pr/7750','pr_7769_per_key_cleanup':'refs/remotes/origin/pr/7769'}
for k,ref in prs.items(): assert git('rev-parse',ref) == freeze['components'][k]
steps=[(freeze['base_main'],freeze['components']['pr_7783_projection_fix_based_on_7602']), (composition['merges'][0]['synthetic_commit'],freeze['components']['pr_7750_owner_admission_identity']), (composition['merges'][1]['synthetic_commit'],freeze['components']['pr_7769_per_key_cleanup'])]
for i,(a,b) in enumerate(steps):
    out=git('merge-tree','--write-tree',a,b).splitlines()[0]
    assert out == composition['merges'][i]['tree']
    assert git('rev-parse',composition['merges'][i]['synthetic_commit']+'^{tree}') == out
assert git('rev-parse',composition['final_commit']+'^{tree}') == composition['final_tree']
blobs=json.loads((root/'SOURCE_BLOBS.json').read_text())
for path,oid in blobs['blobs'].items(): assert git('rev-parse',f"{composition['final_commit']}:{path}") == oid
expected={'typed_state_feedback':37,'owner_admission':3,'perkey_bridge':3}
for name,count in expected.items():
    log=(root/'logs'/f'{name}.log').read_text()
    exit_code=int((root/'logs'/f'{name}.exit').read_text())
    match=re.search(r'Ran (\d+) tests?',log)
    assert result['suites'][name]['exit_code'] == exit_code
    if name=='owner_admission': assert exit_code == 0 and match and int(match.group(1)) == count and '\nOK\n' in log
    else: assert exit_code == 1 and match and int(match.group(1)) == 1 and 'ModuleNotFoundError' in log
assert result['decision']=='HOLD_CONSTRUCTION'
print('AUDIT_PASS_PROVENANCE_AND_HOLD_CLASSIFICATION')
