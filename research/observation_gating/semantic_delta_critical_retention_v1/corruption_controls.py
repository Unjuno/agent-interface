#!/usr/bin/env python3
import copy,json,pathlib,subprocess,sys,tempfile
HERE=pathlib.Path(__file__).resolve().parent
r=json.loads((HERE/'FORMAL_RESULT.json').read_text())
controls=[]
def test(name,mut):
    x=copy.deepcopy(r); mut(x)
    fd=tempfile.NamedTemporaryFile('w',delete=False,suffix='.json'); json.dump(x,fd); fd.close()
    p=subprocess.run([sys.executable,str(HERE/'audit_result.py'),str(HERE/'fixture.json'),fd.name],capture_output=True,text=True)
    pathlib.Path(fd.name).unlink(); controls.append({'control':name,'rejected':p.returncode!=0})
test('drop_calc_focus_edge',lambda x:x['rows'][1].update(excursion_retained=False))
test('fabricate_unknown_removed',lambda x:x['rows'][6].update(unknown_ok=False))
test('authority_escape',lambda x:x['rows'][1]['output'].update(authority='task'))
test('source_identity',lambda x:x['source_blobs'].update(calc_save_report='0'*40))
out={'controls':controls,'all_rejected':all(c['rejected'] for c in controls)}
(HERE/'CORRUPTION_CONTROLS.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out)); raise SystemExit(0 if out['all_rejected'] else 1)
