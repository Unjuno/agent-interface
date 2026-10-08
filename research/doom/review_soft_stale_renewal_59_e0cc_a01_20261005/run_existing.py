import hashlib,json,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent;view=ROOT/'view'
manifest=json.loads((ROOT/'source-manifest.json').read_text())
actual=lambda:{n:hashlib.sha256((view/n).read_bytes()).hexdigest() for n in manifest['files']}
expected={n:r['sha256'] for n,r in manifest['files'].items()}
if actual()!=expected:raise ValueError('source changed')
args=['-B','-m','unittest','-v']+[p[:-3].replace('/','.') for p in manifest['selected_tests']]
start=time.time_ns()
with (ROOT/'existing-normal.stdout.txt').open('xb') as out,(ROOT/'existing-normal.stderr.txt').open('xb') as err:
 proc=subprocess.run([sys.executable,*args],cwd=view,stdout=out,stderr=err,timeout=60)
record={'classification':'local synthetic regression and import check, not full main/live integration','head':manifest['head'],'argv':['bundled-python-3.12.14',*args], 'started_unix_ns':start,'finished_unix_ns':time.time_ns(),'exit_code':proc.returncode,'python':platform.python_version(),'source_sha256_before':expected,'source_sha256_after':actual()}
(ROOT/'existing-normal.execution.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'exit_code':proc.returncode,'source_unchanged':actual()==expected}))
print((ROOT/'existing-normal.stderr.txt').read_text())
