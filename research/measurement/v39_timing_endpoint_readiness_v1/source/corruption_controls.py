import json,tempfile,subprocess,sys
from pathlib import Path
base=json.loads(Path('../RESULT.json').read_text())
controls=[]
def reject(name,mut):
    d=json.loads(json.dumps(base));mut(d)
    p=Path(tempfile.mkstemp(suffix='.json')[1]);p.write_text(json.dumps(d))
    q=subprocess.run([sys.executable,'independent_audit.py','source_map.json',str(p)],capture_output=True,text=True)
    controls.append({'name':name,'rejected':q.returncode!=0});p.unlink()
reject('invent_ready',lambda d:d.update(decision='READY_RETAINED_V39_TIMING_ENDPOINTS_SCOPED'))
reject('invent_count',lambda d:d.update(reportable_count=6))
reject('invent_planner_wait',lambda d:d['intervals']['planner_wait'].update(reportable=True,reasons=[]))
reject('erase_reason',lambda d:d['intervals']['input_to_useful'].update(reasons=[]))
out={'controls':controls,'all_rejected':all(x['rejected'] for x in controls)}
Path('../MUTATION_CONTROLS.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
