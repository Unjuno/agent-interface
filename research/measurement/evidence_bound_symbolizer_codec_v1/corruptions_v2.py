import copy,json,subprocess,sys,tempfile
from pathlib import Path
HERE=Path(__file__).parent;base=json.loads((HERE/'RESULT.json').read_text())
mods=[]
def add(n,fn):x=copy.deepcopy(base);fn(x);mods.append((n,x))
add('decision',lambda x:x.__setitem__('decision','PASS_OTHER'))
add('valid_cases',lambda x:x.__setitem__('valid_cases',63))
add('fault_accept',lambda x:x.__setitem__('faults_accepted_candidate',1))
add('promotion',lambda x:x.__setitem__('evidence_role_promotions',1))
add('deps_loss',lambda x:x.__setitem__('validity_dependency_loss',1))
add('formal_rerun',lambda x:x.__setitem__('reruns',1))
add('class_counts',lambda x:x.__setitem__('semantic_class_counts',{'negative_or_uncertain':26,'supported':38}))
rows=[]
with tempfile.TemporaryDirectory() as td:
 for n,x in mods:
  p=Path(td)/(n+'.json');p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
  q=subprocess.run([sys.executable,str(HERE/'audit_v2.py'),str(p)],capture_output=True,text=True)
  rows.append({'name':n,'rejected':q.returncode!=0})
out={'all_rejected':all(r['rejected'] for r in rows),'rows':rows,'auditor':'AUDIT_V2'}
(HERE/'CORRUPTION_V2.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
