from pathlib import Path
import subprocess,json,hashlib,importlib.util
out=Path(__file__).resolve().parent
src=out/'source'
m=json.loads((src/'MANIFEST.json').read_text())
for n,h in m['evidence_sha256'].items():
    if hashlib.sha256((src/n).read_bytes()).hexdigest()!=h: raise ValueError('evidence pin '+n)
pins={}
for n,pin in m['source_pins'].items():
    raw=subprocess.check_output(['git','show',m['base_main']+':'+n])
    blob=subprocess.check_output(['git','rev-parse',m['base_main']+':'+n],text=True).strip()
    crlf=raw.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
    pins[n]={'git_blob':blob,'raw_git_sha256':hashlib.sha256(raw).hexdigest(),'crlf_sha256':hashlib.sha256(crlf).hexdigest(),'matches_published_git_blob':blob==pin['git_blob'],'published_sha256_matches_crlf':hashlib.sha256(crlf).hexdigest()==pin['sha256']}
    if not pins[n]['matches_published_git_blob'] or not pins[n]['published_sha256_matches_crlf']:raise ValueError('unexplained pin')
spec=importlib.util.spec_from_file_location('retained_audit',src/'audit.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
record=json.loads((src/'probe-output.json').read_text())
actual=module.audit(record)
if actual!=json.loads((src/'audit-output.json').read_text()):raise ValueError('retained audit mismatch')
invalid=['execution_end_1000','execution_end_1001','effect_at_499','effect_at_699']
cases={}
for mode in ['remove','null','string']:
    c=dict(record)
    for k in invalid:
        if mode=='remove':c.pop(k)
        elif mode=='null':c[k]=None
        else:c[k]='false'
    cases[mode]=module.audit(c)
result={'original_evidence_hashes_valid':True,'source_pins':pins,
'original_audit_reproduced':actual,'copied_record_controls':cases,
'findings':['PLAN case 7 says reject at execution end; audit requires effect_at_700 true.',
'PLAN baseline mentions effect time 900; probe has no effect_at_900 record.',
'All four invalid-temporal fields omitted, null or string produce NO_GAP_OBSERVED.',
'Current public MCP path uses core_v1/backend execution, not RequestLifecycle.'],
'first_intake_attempt':'Stopped on Git-byte SHA mismatch before audit; published SHA matches CRLF checkout bytes, published Git blobs match exactly. No scientific-source normalization or rewrite.',
'disposition':'HOLD_RUNTIME_ADOPTION',
'scope':'read-only retained-record audit and copied-data controls; no frozen probe rerun, GUI input or timing performance claim'}
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
