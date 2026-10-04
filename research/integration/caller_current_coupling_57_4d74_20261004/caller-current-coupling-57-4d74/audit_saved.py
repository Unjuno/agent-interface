"""Read-only qualification custody audit, authored after the first test run."""
import hashlib,json,pathlib,re
root=pathlib.Path(__file__).resolve().parent
plan=json.loads((root/'PLAN.json').read_text(encoding='utf8'))
errors=[]
for item in plan['inputs']:
    if hashlib.sha256((root/item['path']).read_bytes()).hexdigest()!=item['sha256']:
        errors.append('source mismatch:'+item['path'])
log=(root/'first-run.log').read_text(encoding='utf-8-sig')
methods=re.findall(r'^test_.*\.\.\. ok$',log,re.M)
if len(methods)!=31:errors.append('first log method count')
if not re.search(r'Ran 31 tests in [0-9.]+s\s+OK\s*$',log):errors.append('terminal unittest result')
if (root/'EXIT.txt').read_text(encoding='utf-8-sig').strip()!='0':errors.append('host exit')
command=json.loads((root/'COMMAND.json').read_text(encoding='utf-8-sig'))
for flag,value in [('--network','none'),('--pull','never'),('--workdir','/data')]:
    if command[command.index(flag)+1]!=value:errors.append(flag)
if not command[command.index('--volume')+1].endswith(':/data:ro'):errors.append('read-only mount')
print(json.dumps(dict(errors=errors,source_files=len(plan['inputs']),method_count=len(methods),scope='saved bytes and first result only; same author, not blind independent scientific review')))
raise SystemExit(bool(errors))
