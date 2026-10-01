#!/usr/bin/env python3
import copy, json, pathlib, subprocess, sys, tempfile
HERE=pathlib.Path(__file__).resolve().parent
fixture=json.loads((HERE/'fixture.json').read_text())
result=json.loads((HERE/'FORMAL_RESULT.json').read_text())
controls=[]

def run(name,mut):
    bad=copy.deepcopy(result); mut(bad)
    with tempfile.NamedTemporaryFile('w',suffix='.json',delete=False) as f:
        json.dump(bad,f); path=f.name
    p=subprocess.run([sys.executable,str(HERE/'audit_result.py'),str(HERE/'fixture.json'),path],capture_output=True,text=True)
    controls.append({'control':name,'rejected':p.returncode!=0,'returncode':p.returncode})
    pathlib.Path(path).unlink()
run('candidate_path', lambda r: r['rows'][1].update(first_path_match=False))
run('binding_fault', lambda r: r['rows'][9].update(fault_refusal_match=False))
run('authority', lambda r: r['rows'][1]['output'].update(authority='task'))
run('source_blob', lambda r: r['source_blobs'].update(procedure='0'*40))
out={'controls':controls,'all_rejected':all(x['rejected'] for x in controls)}
(HERE/'CORRUPTION_CONTROLS.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out))
raise SystemExit(0 if out['all_rejected'] else 1)
