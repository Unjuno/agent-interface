import argparse,json
from pathlib import Path
TASK='CONCURRENT-FAST-DECISION-T2-ASYNC-HANDBACK-CONSTRUCTION-20260918-007';CLEAR='CLEAR_PROGRESS';WATCH='UNCERTAIN_TRANSIENT';HARD='HARD_INVALIDATION';MAP={CLEAR:'ADVANCE',WATCH:'WATCH',HARD:'YIELD'}
def first_clear(c):
    if c['initial_state']==CLEAR:return c['start_ns']
    xs=[x['t_ns'] for x in c.get('actual_transitions',[]) if x.get('state')==CLEAR];return min(xs) if xs else None
def intervals(c,state):
    start=c['start_ns'];end=c['frontier_return_event_ns'];cur=c['initial_state'];cursor=start;out=[]
    for tr in sorted(c.get('actual_transitions',[]),key=lambda x:x['t_ns']):
        if tr['t_ns']>=end:break
        if cur==state and cursor<tr['t_ns']:out.append((cursor,tr['t_ns']))
        cur=tr['state'];cursor=tr['t_ns']
    if cur==state and cursor<end:out.append((cursor,end))
    return out
def audit(r):
    integ=[];race=[];auth=[];value=[]
    if r.get('task')!=TASK or r.get('phase')!='construction' or r.get('construction_invocations')!=1 or r.get('reruns')!=0 or r.get('replacements')!=0 or r.get('tuning')!=0:integ.append('contract')
    if r.get('controller_knows_return_offset') is not False or len(r.get('cases',[]))!=12 or len(r.get('child_runs',[]))!=12:integ.append('shape')
    if any(x.get('returncode')!=0 for x in r.get('child_runs',[])):integ.append('child_exit')
    for c in r.get('cases',[]):
        cid=c.get('case_id','?');ret=c.get('frontier_return_event_ns')
        if c.get('exceptions'):integ.append(cid+':exception')
        if not ret:integ.append(cid+':missing_return');continue
        if c.get('terminal_f8_up') is not True:auth.append(cid+':keyup')
        if not all(c.get('cleanup',{}).get(k) for k in ('xvfb_exit','tk_destroyed','control_closed','scorer_closed')):auth.append(cid+':cleanup')
        for s in c.get('samples',[]):
            if MAP.get(s.get('state'))!=s.get('disposition'):auth.append(cid+':selector')
        post=[s for s in c.get('sends',[]) if s.get('send_begin_ns',0)>=ret]
        if post:race.append(cid+':post_return_send')
        sends=sorted(c.get('sends',[]),key=lambda x:x['send_begin_ns'])
        for e in c.get('effects',[]):
            prior=[s for s in sends if s['send_begin_ns']<=e['t_ns']]
            if prior and prior[-1]['send_begin_ns']>=ret:race.append(cid+':post_return_effect_origin')
        for st in (WATCH,HARD):
            for lo,hi in intervals(c,st):
                if any(lo<=e.get('t_ns',0)<hi for e in c.get('effects',[])):auth.append(cid+':forbidden_'+st)
        clear=first_clear(c)
        if clear is not None and ret-clear>=5_000_000:
            if not any(e.get('effect_kind')=='useful' and clear<=e.get('t_ns',0)<ret for e in c.get('effects',[])):value.append(cid+':no_pre_return_value')
    if integ:decision='STOP_ASYNC_HANDBACK_INTEGRITY'
    elif auth:decision='STOP_ASYNC_HANDBACK_AUTHORITY'
    elif race:decision='STOP_ASYNC_HANDBACK_RACE'
    elif value:decision='STOP_ASYNC_HANDBACK_NO_VALUE'
    else:decision='PASS_ASYNC_HANDBACK_CONSTRUCTION_ELIGIBLE'
    return {'decision':decision,'pass':decision.startswith('PASS_'),'integrity_errors':integ,'authority_errors':auth,'race_errors':race,'value_errors':value,'rows':len(r.get('cases',[]))}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('result');ap.add_argument('--out',required=True);a=ap.parse_args();r=json.loads(Path(a.result).read_text());o=audit(r);Path(a.out).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(o,sort_keys=True));return 0 if o['pass'] else 4
if __name__=='__main__':raise SystemExit(main())
