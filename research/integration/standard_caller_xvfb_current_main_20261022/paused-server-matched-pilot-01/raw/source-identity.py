import hashlib,json,subprocess
from pathlib import Path
repo=Path.cwd(); expected='cc5ef16c560cc985ee0951d3d53d659e892f5167'
head=subprocess.check_output(['git','rev-parse','origin/main'],text=True).strip()
if head != expected: raise SystemExit(f'main changed: {head}')
paths=['runtime/cli_v1/test_mcp_xvfb_blocked_release_integration.py','runtime/cli_v1/mcp_guarded.py','runtime/cli_v1/owned_guarded_session.py','runtime/cli_v1/mcp_server.py','runtime/cli_v1/test_synthetic_task_oracle.py']
rows=[]
for name in paths:
 current=hashlib.sha256((repo/name).read_bytes()).hexdigest()
 baseline=hashlib.sha256(subprocess.check_output(['git','show',f'origin/main:{name}'])).hexdigest()
 if subprocess.run(['git','diff','--quiet','origin/main','--',name]).returncode: raise SystemExit(f'working source differs from main: {name}')
 rows.append({'path':name,'working_sha256':current,'main_blob_sha256':baseline,'git_diff_clean':True})
report={'main_sha':head,'source_hashes':rows}
Path(r'research/integration/standard_caller_xvfb_current_main_20261022/paused-server-matched-pilot-01/raw/source-identity.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps(report,indent=2,sort_keys=True))