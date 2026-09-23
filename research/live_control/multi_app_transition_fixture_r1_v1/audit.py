from __future__ import annotations
import copy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REQ={'geometry_change','focus_drift','window_replacement','modal_transition','input_neutral'}

def valid(r):
    if r.get('task')!='MULTI-APP-TRANSITION-LIVE-FIXTURE-R1-20260918-001':return False
    if (r.get('formal_invocations'),r.get('reruns'),r.get('replacements'),r.get('tuning'))!=(1,0,0,0):return False
    if r.get('sessions')!=4 or r.get('passed_sessions')!=4 or r.get('errors')!=[]:return False
    if r.get('decision')!='PASS_MULTI_APP_TRANSITION_FIXTURE_SCOPED':return False
    rows=r.get('rows',[])
    if len(rows)!=4:return False
    for row in rows:
        if sorted(row.get('apps',[]))!=['Chromium','XTerm'] or row.get('pass') is not True:return False
        if set(row.get('gates',{}))!=REQ or not all(row['gates'][k] is True for k in REQ):return False
        ev={e['event']:e for e in row.get('events',[])}
        if set(ev)!=REQ:return False
        if not (ev['geometry_change']['before']!=ev['geometry_change']['after']):return False
        if not (ev['focus_drift']['from']!=ev['focus_drift']['to']):return False
        if not (ev['window_replacement']['old']!=ev['window_replacement']['new'] and ev['window_replacement']['old_gone'] is True):return False
        if not (ev['modal_transition']['before']!=ev['modal_transition']['after']):return False
        if ev['input_neutral'].get('ok') is not True:return False
    return True

def main():
    r=json.loads((ROOT/'RESULT.json').read_text());errors=[]
    if not valid(r):errors.append('primary')
    controls={}
    muts={
      'gate':lambda x:x['rows'][0]['gates'].__setitem__('focus_drift',False),
      'old_gone':lambda x:x['rows'][1]['events'][2].__setitem__('old_gone',False),
      'modal_hash':lambda x:x['rows'][2]['events'][3].__setitem__('after',x['rows'][2]['events'][3]['before']),
      'input':lambda x:x['rows'][3]['events'][4].__setitem__('ok',False),
      'session_count':lambda x:x.__setitem__('sessions',3),
      'invocation':lambda x:x.__setitem__('formal_invocations',2),
      'decision':lambda x:x.__setitem__('decision','FAIL')
    }
    for name,mut in muts.items():
        y=copy.deepcopy(r);mut(y);controls[name]=not valid(y)
    if not all(controls.values()):errors.append('corruption')
    out={'pass':not errors,'errors':errors,'corruption_controls':controls,'sessions':r.get('sessions'),'decision':r.get('decision') if not errors else 'FAIL_INTEGRITY'}
    (ROOT/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
    raise SystemExit(0 if out['pass'] else 1)
if __name__=='__main__':main()
