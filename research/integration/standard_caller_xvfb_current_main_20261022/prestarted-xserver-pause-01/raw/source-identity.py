import hashlib,json,subprocess
from pathlib import Path
repo=Path.cwd(); expected='b3fdbee40cce6e9040c9a3a9360ea35cc692995e'
head=subprocess.check_output(['git','rev-parse','origin/main'],text=True).strip()
if head != expected: raise SystemExit(f'baseline changed: {head}')
candidate=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
paths=['runtime/cli_v1/test_mcp_xvfb_blocked_release_integration.py','runtime/cli_v1/mcp_guarded.py','runtime/cli_v1/owned_guarded_session.py','runtime/cli_v1/mcp_server.py','runtime/cli_v1/test_synthetic_task_oracle.py']
rows=[]
for name in paths:
 current=hashlib.sha256((repo/name).read_bytes()).hexdigest()
 baseline=hashlib.sha256(subprocess.check_output(['git','show',f'origin/main:{name}'])).hexdigest()
 same=subprocess.run(['git','diff','--quiet','origin/main','--',name]).returncode==0
 rows.append({'path':name,'candidate_worktree_sha256':current,'baseline_git_blob_sha256':baseline,'git_content_matches_baseline':same})
changed=[r['path'] for r in rows if not r['git_content_matches_baseline']]
if changed != ['runtime/cli_v1/test_mcp_xvfb_blocked_release_integration.py']:
 raise SystemExit(f'unexpected changed source paths: {changed}')
report={'baseline_main':head,'candidate_commit':candidate,'changed_paths':changed,'source_hashes':rows}
Path(r'research/integration/standard_caller_xvfb_current_main_20261022/prestarted-xserver-pause-01/raw/source-identity.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps(report,indent=2,sort_keys=True))