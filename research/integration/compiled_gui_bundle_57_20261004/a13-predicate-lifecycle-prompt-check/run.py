import hashlib, json, pathlib, subprocess, sys, time
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[3]
REL='research/integration'
TASK=ROOT/REL/'planner_contract_56_4d74_20261004/r02/formal-output/block-2/C/task-1.json'
IMAGE=ROOT/REL/'planner_contract_56_4d74_20261004/r02/formal-output/block-2/C/client/runtime/005.png'
A12=ROOT/REL/'compiled_gui_bundle_57_20261004/a12-predicate-lifecycle-guard/candidate.py'
EXPECTED={
 'PROMPT.txt':'8398ebec2581d05810dcbf3a39bf1389ffaf135edf25b62a8728bb6a2fa8d601',
 'schema.json':'1b79d332398ea3e9d816c4982c441a34b4536a79d4fc0be2a9fac7457876d964',
 'MODEL.json':'31635e8aeb77521c4b55fe1171cd246939df3e4cbae557b3e073efc1eb09aa3d',
}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
for n,h in EXPECTED.items():
 if sha(HERE/n)!=h: raise SystemExit(f'pin mismatch: {n}')
if sha(HERE/'PLAN.md')!='dc72930ebd77dd96c6997bf9ceb63d8f14b75ebdb0cf92b092b5d7714e5d6d90': raise SystemExit('plan pin mismatch')
if sha(TASK)!='80535efedb1af9bfa1b16346d66f27b10bf1119c21038629b08e3cb79356fc64': raise SystemExit('task pin mismatch')
if sha(IMAGE)!='dceef5c6abee047328d99007369db0fade828b26a02fb83ba931896ae818ed21': raise SystemExit('image pin mismatch')
if sha(A12)!='48549d1000a0a307436479fe64ae47fb0322d1e42f2a90a70e613691445526a7': raise SystemExit('A12 candidate pin mismatch')
task=json.loads(TASK.read_text()); model=json.loads((HERE/'MODEL.json').read_text())
cmd=['codex','exec','--ephemeral','--ignore-user-config','--ignore-rules','--disable','plugins','--disable','remote_plugin','--disable','shell_snapshot','--disable','shell_tool','--skip-git-repo-check','--sandbox','read-only','--json','--color','never','--model','gpt-5.6-luna','-c','model_reasoning_effort="low"','-c','project_doc_max_bytes=0','-c','approval_policy="never"','--cd',str(ROOT),'--output-schema',str(HERE/'schema.json'),'--output-last-message',str(HERE/'answer.json'),'--image',str(IMAGE),'-']
(HERE/'argv.json').write_text(json.dumps(cmd,indent=2)+'\n')
start=time.monotonic_ns()
try:
 p=subprocess.run(cmd,input=(HERE/'PROMPT.txt').read_bytes(),capture_output=True,timeout=90)
 result={'exit_code':p.returncode,'timed_out':False,'elapsed_ns':time.monotonic_ns()-start}
 (HERE/'stdout.jsonl').write_bytes(p.stdout); (HERE/'stderr.txt').write_bytes(p.stderr)
except subprocess.TimeoutExpired as e:
 result={'exit_code':None,'timed_out':True,'elapsed_ns':time.monotonic_ns()-start}
 (HERE/'stdout.jsonl').write_bytes(e.stdout or b''); (HERE/'stderr.txt').write_bytes(e.stderr or b'')
answer=(HERE/'answer.json').read_bytes() if (HERE/'answer.json').exists() else b''
raw={'status':'captured','provider_attempts':1,'requested_model':'gpt-5.6-luna','requested_effort':'low','timeout_seconds':90,**result,'inputs':{'prompt_sha256':sha(HERE/'PROMPT.txt'),'schema_sha256':sha(HERE/'schema.json'),'model_catalog_sha256':sha(HERE/'MODEL.json'),'task_sha256':sha(TASK),'image_sha256':sha(IMAGE),'candidate_sha256':sha(A12)},'answer_sha256':hashlib.sha256(answer).hexdigest() if answer else None,'answer':json.loads(answer) if answer else None,'cli_stdout_sha256':sha(HERE/'stdout.jsonl'),'cli_stderr_sha256':sha(HERE/'stderr.txt'),'argv_sha256':sha(HERE/'argv.json')}
(HERE/'RAW.json').write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:raw[k] for k in ['exit_code','timed_out','answer_sha256','inputs']},indent=2))
