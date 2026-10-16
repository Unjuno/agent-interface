from __future__ import annotations
import copy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
TASK='MULTI-APP-GUARDED-RECOVERY-A2-20260918-002'
REASONS=['REFUSE_GEOMETRY','REFUSE_FOCUS','REFUSE_BINDING','REFUSE_OBSERVATION']
TITLES=['chrome://downloads/ - Chromium','chrome://history/ - Chromium','chrome://downloads/ - Chromium','chrome://history/ - Chromium']

def valid(r):
    if r.get('task')!=TASK:return False
    if (r.get('formal_invocations'),r.get('reruns'),r.get('replacements'),r.get('tuning'))!=(1,0,0,0):return False
    if r.get('sessions')!=4 or r.get('passed_sessions')!=4 or r.get('errors')!=[]:return False
    if r.get('decision')!='PASS_MULTI_APP_GUARDED_RECOVERY_A2_SCOPED':return False
    rows=r.get('rows',[])
    if len(rows)!=4:return False
    for row in rows:
        if row.get('pass') is not True or row.get('errors')!=[]:return False
        if sorted(row.get('apps',[]))!=['Chromium','XTerm']:return False
        refs=row.get('refusals',[])
        if [x.get('reason') for x in refs]!=REASONS:return False
        if any(x.get('input_before')!=x.get('input_after') for x in refs):return False
        batches=row.get('task_batches',[])
        if row.get('task_input_batches')!=4 or len(batches)!=4:return False
        if any(b.get('active_before')!=b.get('window') for b in batches):return False
        eff=row.get('effects',[])
        if [x.get('title') for x in eff]!=TITLES:return False
        if [x.get('phase') for x in eff]!=[1,2,3,4]:return False
        if row.get('old_window')==row.get('new_window') or row.get('old_gone') is not True:return False
        if row.get('terminal_neutral') is not True:return False
    return True

def main():
    r=json.loads((ROOT/'RESULT.json').read_text());errors=[]
    if not valid(r):errors.append('primary')
    muts={
      'stale_input':lambda x:x['rows'][0]['refusals'][0].__setitem__('input_after',1),
      'wrong_active':lambda x:x['rows'][0]['task_batches'][0].__setitem__('active_before',0),
      'wrong_effect':lambda x:x['rows'][1]['effects'][2].__setitem__('title','wrong'),
      'replacement':lambda x:x['rows'][2].__setitem__('old_gone',False),
      'neutral':lambda x:x['rows'][3].__setitem__('terminal_neutral',False),
      'invocation':lambda x:x.__setitem__('formal_invocations',2),
      'decision':lambda x:x.__setitem__('decision','FAIL')
    }
    controls={}
    for name,mut in muts.items():
        y=copy.deepcopy(r);mut(y);controls[name]=not valid(y)
    if not all(controls.values()):errors.append('corruption')
    out={'pass':not errors,'errors':errors,'decision':r.get('decision') if not errors else 'FAIL_INTEGRITY','sessions':r.get('sessions'),'corruption_controls':controls}
    (ROOT/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True));raise SystemExit(0 if out['pass'] else 1)
if __name__=='__main__':main()
