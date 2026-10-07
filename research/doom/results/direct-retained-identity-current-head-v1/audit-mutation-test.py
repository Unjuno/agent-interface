"""Prove auditor sensitivity to a changed positive candidate result."""
import json, shutil, subprocess, sys, tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='direct-identity-mutation-') as td:
    clone=Path(td)/'case'; clone.mkdir()
    for name in ('analyzer.py','tests.py','raw_cases.json','FREEZE.json','candidate.py','audit.py'):
        shutil.copy2(HERE/name,clone/name)
    setup=subprocess.run([sys.executable,str(clone/'candidate.py')],capture_output=True,text=True)
    if setup.returncode: raise SystemExit(f'candidate setup failed: {setup.stderr}')
    out=clone/'candidate_results.json'; result=json.loads(out.read_text(encoding='utf-8'))
    result['results'][0]['result']['measurement_ready']=False
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    audit=subprocess.run([sys.executable,str(clone/'audit.py')],capture_output=True,text=True)
    if audit.returncode==0: raise SystemExit('auditor accepted mutated positive result')
    report=json.loads((clone/'audit.json').read_text(encoding='utf-8'))
    if not any(e.get('error')=='candidate_result_mismatch' and e.get('case_id')=='valid_nonempty_pair' for e in report['errors']): raise SystemExit(f'unexpected rejection: {report["errors"]}')
    print(json.dumps({'mutation_rejected':True,'expected_error':'candidate_result_mismatch','audit_exit':audit.returncode},indent=2))
