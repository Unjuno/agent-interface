from __future__ import annotations
import copy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
TASK='MULTI-APP-GUARDED-RECOVERY-R3-DURABLE-A2-20260918-004'
REASONS=['REFUSE_GEOMETRY','REFUSE_FOCUS','REFUSE_BINDING','REFUSE_OBSERVATION']*3
TITLES=['chrome://downloads/ - Chromium','chrome://history/ - Chromium','chrome://downloads/ - Chromium','chrome://history/ - Chromium']*3

def valid(r):
    if r.get('task')!=TASK or r.get('decision')!='PASS_MULTI_APP_GUARDED_RECOVERY_R3_DURABLE_A2_SCOPED':return False
    if (r.get('formal_invocations'),r.get('reruns'),r.get('replacements'),r.get('tuning'))!=(1,0,0,0):return False
    if r.get('batch_invocations')!={str(i):1 for i in range(1,5)}:return False
    if r.get('sessions')!=4 or r.get('passed_sessions')!=4 or r.get('errors')!=[]:return False
    if r.get('aggregate')!={'refusal_gates':48,'refusal_zero_task_input':48,'fallback_active_match':48,'effects':48,'replacement_valid':12,'terminal_neutral':4}:return False
    rows=r.get('rows',[])
    if len(rows)!=4:return False
    for row in rows:
        if row.get('pass') is not True or row.get('errors')!=[]:return False
        if row.get('cycles_completed')!=3:return False
        if [x.get('reason') for x in row.get('refusals',[])]!=REASONS:return False
        if any(x.get('input_before')!=x.get('input_after') for x in row.get('refusals',[])):return False
        if any(x.get('active_before')!=x.get('window') for x in row.get('task_batches',[])):return False
        if [x.get('title') for x in row.get('effects',[])]!=TITLES:return False
        if len(row.get('replacements',[]))!=3 or not all(x.get('old_gone') is True and x.get('old_window')!=x.get('new_window') for x in row['replacements']):return False
        if row.get('terminal_neutral') is not True:return False
    return True

def main():
    r=json.loads((ROOT/'RESULT.json').read_text()); errors=[]
    if not valid(r):errors.append('primary')
    muts={'batch':lambda x:x['batch_invocations'].__setitem__('2',2),'stale_input':lambda x:x['rows'][0]['refusals'][0].__setitem__('input_after',1),'wrong_active':lambda x:x['rows'][1]['task_batches'][3].__setitem__('active_before',0),'wrong_effect':lambda x:x['rows'][2]['effects'][4].__setitem__('title','wrong'),'replacement':lambda x:x['rows'][3]['replacements'][2].__setitem__('old_gone',False),'neutral':lambda x:x['rows'][0].__setitem__('terminal_neutral',False),'aggregate':lambda x:x['aggregate'].__setitem__('effects',47),'decision':lambda x:x.__setitem__('decision','FAIL')}
    controls={}
    for n,m in muts.items():
        y=copy.deepcopy(r);m(y);controls[n]=not valid(y)
    if not all(controls.values()):errors.append('corruption')
    out={'pass':not errors,'errors':errors,'decision':r.get('decision') if not errors else 'FAIL_INTEGRITY','corruption_controls':controls}
    (ROOT/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True));raise SystemExit(0 if out['pass'] else 1)
if __name__=='__main__':main()
