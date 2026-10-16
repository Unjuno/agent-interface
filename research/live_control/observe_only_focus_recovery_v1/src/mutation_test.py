import copy,json
from pathlib import Path
r=json.loads(Path('/tmp/ai_exp849/construction/c1/case.json').read_text())
def valid(x):
    rec=x['recovery']
    return (x['source']['surface']=='A' and x['admission']['surface']=='B' and x['rejection']['reason']=='focus_mismatch' and
            rec['authority']=='none' and rec['task_input_granted'] is False and rec['action_admission_eligible'] is False and
            rec['focus']['surface']=='B' and not x['input_events'] and x['keymap_nonzero']==0)
assert valid(r)
ms=[]
a=copy.deepcopy(r); a['recovery']['authority']='task'; ms.append(a)
b=copy.deepcopy(r); b['recovery']['focus']=copy.deepcopy(b['source']); ms.append(b)
c=copy.deepcopy(r); c['input_events']=[{'event':'<KeyPress>','keysym':'a'}]; ms.append(c)
assert all(not valid(x) for x in ms)
print(json.dumps({'mutations_rejected':3,'total':3}))
