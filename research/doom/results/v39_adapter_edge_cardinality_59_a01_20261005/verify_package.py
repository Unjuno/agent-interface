from pathlib import Path
import hashlib,json
p=Path(__file__).resolve().parent
j=lambda n: json.loads((p/n).read_text(encoding='utf-8-sig'))
sha=lambda n: hashlib.sha256((p/n).read_bytes()).hexdigest()
f=j('FREEZE.json'); a=j('AUDIT_V2_FREEZE.json'); a2=j('AUDIT_A02_FREEZE.json')
checks=[]
def ck(v,n): checks.append((bool(v),n))
ck(sha('src/map01_overlap_controller_v39.py')==f['source']['controller_sha256'],'A01 controller source hash')
ck(sha('src/candidate-events.jsonl')==f['input']['sha256'],'A01 frozen fixture hash')
ck(sha('src/candidate.py')==f['candidate']['sha256'],'A01 candidate hash')
ck(sha('src/audit.py')==f['independent_auditor']['sha256'],'A01 preliminary auditor hash')
ck(sha('raw/candidate.json')==a['inputs']['candidate_sha256'],'A01 output hash for audit v2')
ck(sha('audit-v2-src/audit.py')==a['auditor']['sha256'],'A01 audit-v2 script hash')
ck((p/'audit-v2/audit.json').is_file(),'A01 audit-v2 output exists')
audit=j('audit-v2/audit.json')
ck(audit['audit']=='PASS' and audit['checks']==66 and not audit['errors'],'A01 independent raw-derived audit')
ck(audit['tamper_control']=='PASS','A01 coherent corruption control')
ck(sha('candidate/run_regression.py')==a2['runner_sha256'],'A02 runner hash')
ck(sha(a2['result_path'])==a2['result_sha256'],'A02 result hash')
r=j(a2['result_path'])
ck(r['result']=='PASS' and r['test_cases']==1 and r['subcases']==5,'A02 test result')
ck(r['source_sha256']==a2['hashes']['controller'] and r['test_sha256']==a2['hashes']['test'],'A02 source/test hashes')
ck(r['py_compile']=='PASS','A02 py_compile result')
ck(j('raw/a02-preflight-running-containers.json')==[] and j('raw/a02-postflight-running-containers.json')==[],'A02 empty WSLc inventories')
lines=(p/'SHA256SUMS').read_text(encoding='utf-8-sig').splitlines()
manifest={}
for line in lines:
 h,rel=line.split('  ',1); manifest[rel]=h
ck(len(manifest)==len(lines),'unique manifest paths')
for rel,h in manifest.items(): ck(sha(rel)==h,'sha256 '+rel)
all_files={x.relative_to(p).as_posix() for x in p.rglob('*') if x.is_file() and x.name not in ('SHA256SUMS','verify_package.py') and '__pycache__' not in x.parts}
ck(all_files==set(manifest),'manifest covers all package files')
failed=[n for ok,n in checks if not ok]
print(json.dumps({'audit':'PASS' if not failed else 'FAIL','checks':len(checks),'errors':failed},indent=2))
raise SystemExit(bool(failed))
