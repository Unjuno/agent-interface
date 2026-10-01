import argparse,json,sys
from pathlib import Path
CONDS=['NO_GRAB','HEALTHY_1MS','HEALTHY_20MS','KILL_OWNER_20MS','HUNG_OWNER_100MS_WATCHDOG']

def load_json(p): return json.loads(p.read_text())
def load_jsonl(p): return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]

def audit(root,schedule_path):
    schedule=load_json(schedule_path)['rows']; errors=[]; checks=0; rebuilt=[]
    checks+=1
    if len(schedule)!=15: errors.append(f'schedule_count:{len(schedule)}')
    exp_ids=[]
    for s in schedule:
        cid=f"{s['index']:02d}_{s['condition']}_r{s['repetition']}"; exp_ids.append(cid)
        case_dir=root/cid; checks+=1
        if not case_dir.is_dir(): errors.append(f'missing_case_dir:{cid}'); continue
        try:
            case=load_json(case_dir/'CASE.json'); obs=load_json(case_dir/'observer.json'); xs=load_json(case_dir/'XSERVER_EXIT.json')
        except Exception as e:
            errors.append(f'load:{cid}:{type(e).__name__}:{e}'); continue
        checks+=12
        for k,v in [('case_id',cid),('condition',s['condition']),('repetition',s['repetition']),('hold_ms',s['hold_ms']),('display',s['display'])]:
            if case.get(k)!=v: errors.append(f'{k}:{cid}:{case.get(k)!r}!={v!r}')
        if obs.get('pid')!=case.get('observer_pid'): errors.append(f'observer_pid:{cid}')
        if obs.get('ready_ns')!=case.get('observer_ready_ns'): errors.append(f'observer_ready:{cid}')
        if case.get('observer_returncode')!=0: errors.append(f'observer_exit:{cid}:{case.get("observer_returncode")}')
        if not case.get('xvfb_alive_at_score'): errors.append(f'xvfb_dead_at_score:{cid}')
        if case.get('xvfb_restarts')!=0: errors.append(f'xvfb_restart:{cid}')
        if xs.get('pid')!=case.get('xvfb_pid'): errors.append(f'xserver_pid:{cid}')
        if xs.get('returncode')!=0: errors.append(f'xserver_exit:{cid}:{xs.get("returncode")}')
        if xs.get('socket_exists_after'): errors.append(f'socket_leak:{cid}')
        rows=obs.get('rows'); checks+=1
        if not isinstance(rows,list) or len(rows)<2:
            errors.append(f'observer_rows_invalid:{cid}'); continue
        min_d=None; max_d=None
        for j,r in enumerate(rows):
            checks+=4
            if r.get('i')!=j: errors.append(f'observer_i:{cid}:{j}:{r.get("i")}')
            st=r.get('start_ns'); en=r.get('end_ns'); dur=r.get('duration_ns')
            if not all(isinstance(x,int) and not isinstance(x,bool) for x in (st,en,dur)):
                errors.append(f'observer_type:{cid}:{j}'); continue
            if en-st!=dur or dur<0: errors.append(f'observer_duration:{cid}:{j}')
            if j and st < rows[j-1].get('start_ns',st): errors.append(f'observer_order:{cid}:{j}')
            min_d=dur if min_d is None else min(min_d,dur); max_d=dur if max_d is None else max(max_d,dur)
        checks+=4
        if len(rows)!=case.get('observer_rows'): errors.append(f'observer_count:{cid}:{len(rows)}:{case.get("observer_rows")}')
        if max_d!=case.get('observer_max_duration_ns'): errors.append(f'observer_max:{cid}:{max_d}:{case.get("observer_max_duration_ns")}')
        if min_d!=case.get('observer_min_duration_ns'): errors.append(f'observer_min:{cid}:{min_d}:{case.get("observer_min_duration_ns")}')
        if rows[-1].get('final') is not True: errors.append(f'observer_final:{cid}')

        cond=s['condition']; release=None; grab=None; events=[]
        if cond!='NO_GRAB':
            try: events=load_jsonl(case_dir/'owner.events.jsonl')
            except Exception as e: errors.append(f'owner_events_load:{cid}:{e}'); events=[]
            grabbed=[e for e in events if e.get('event')=='GRABBED']; checks+=2
            if len(grabbed)!=1: errors.append(f'grab_event_count:{cid}:{len(grabbed)}')
            else:
                grab=grabbed[0].get('grab_sync_end_ns')
                if grab!=case.get('grab_sync_end_ns'): errors.append(f'grab_time:{cid}')
            if cond.startswith('HEALTHY_'):
                un=[e for e in events if e.get('event')=='UNGRABBED']; checks+=3
                if len(un)!=1: errors.append(f'ungrab_event_count:{cid}:{len(un)}')
                else:
                    release=un[0].get('ungrab_sync_end_ns')
                    if release!=case.get('release_ns'): errors.append(f'ungrab_time:{cid}')
                if case.get('owner_returncode')!=0: errors.append(f'healthy_owner_exit:{cid}:{case.get("owner_returncode")}')
            else:
                release=case.get('owner_death_observed_ns'); checks+=4
                if release!=case.get('release_ns'): errors.append(f'death_release:{cid}')
                if case.get('owner_returncode')!=-9 or case.get('kill_wait_returncode')!=-9: errors.append(f'kill_owner_exit:{cid}')
                if not isinstance(case.get('kill_signal_ns'),int) or not isinstance(release,int) or release<case.get('kill_signal_ns',0): errors.append(f'kill_order:{cid}')
            if not isinstance(grab,int) or not isinstance(release,int) or release<grab:
                errors.append(f'grab_release_order:{cid}:{grab}:{release}')
            else:
                pre=[r for r in rows if r['end_ns']<grab]
                post=[r for r in rows if r['start_ns']>release]
                spanning=[r for r in rows if r['start_ns']<=release and r['end_ns']>=grab and r['duration_ns']>0]
                during=[r for r in rows if r['start_ns']>=grab and r['start_ns']<=release]
                first_post=min((r['end_ns'] for r in post),default=None)
                max_span=max((r['duration_ns'] for r in spanning),default=0)
                calc={'pre_count':len(pre),'post_count':len(post),'spanning_count':len(spanning),'during_start_count':len(during),'first_post_end_ns':first_post,'max_spanning_duration_ns':max_span,'recovery_after_release_ns':None if first_post is None else first_post-release}
                checks+=len(calc)
                for k,v in calc.items():
                    if case.get(k)!=v: errors.append(f'raw_summary:{cid}:{k}:{case.get(k)}!={v}')
                if len(pre)<1: errors.append(f'no_pre:{cid}')
                if len(post)<1: errors.append(f'no_post:{cid}')
                if len(spanning)<1: errors.append(f'no_spanning:{cid}')
                authored=s['hold_ms']*1_000_000
                if cond.startswith('HEALTHY_'):
                    if release-grab < max(500_000,int(authored*.75)): errors.append(f'healthy_hold_short:{cid}')
                    if max_span < max(500_000,int(authored*.75)): errors.append(f'healthy_stall_short:{cid}')
                if cond=='KILL_OWNER_20MS' and release-grab<15_000_000: errors.append(f'kill_too_short:{cid}')
                if cond=='HUNG_OWNER_100MS_WATCHDOG' and release-grab<95_000_000: errors.append(f'watchdog_too_short:{cid}')
        else:
            checks+=6
            if case.get('release_ns') is not None: errors.append(f'baseline_release:{cid}')
            if case.get('spanning_count')!=0 or case.get('max_spanning_duration_ns')!=0: errors.append(f'baseline_spanning:{cid}')
            if case.get('pre_count')!=len(rows) or case.get('post_count')!=len(rows): errors.append(f'baseline_counts:{cid}')
            if case.get('during_start_count')!=0: errors.append(f'baseline_during:{cid}')
        rebuilt.append({'case_id':cid,'condition':cond,'repetition':s['repetition'],'max_spanning_duration_ns':0 if cond=='NO_GRAB' else case.get('max_spanning_duration_ns'),'release_ns':release,'grab_sync_end_ns':grab})
    actual_dirs=sorted(p.name for p in root.iterdir() if p.is_dir()); checks+=1
    if sorted(exp_ids)!=actual_dirs: errors.append(f'case_dir_set:{actual_dirs}')
    by={(x['condition'],x['repetition']):x for x in rebuilt}
    for rep in range(3):
        a=by.get(('HEALTHY_1MS',rep)); b=by.get(('HEALTHY_20MS',rep)); checks+=1
        if not a or not b or not b['max_spanning_duration_ns']>a['max_spanning_duration_ns']: errors.append(f'20_not_gt_1:{rep}')
    return {'status':'PASS_RAW_RECONSTRUCTION_V2' if not errors else 'FAIL_RAW_RECONSTRUCTION_V2','cases':len(rebuilt),'checks':checks,'errors':errors}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--schedule',required=True); ap.add_argument('--out'); a=ap.parse_args()
    res=audit(Path(a.root),Path(a.schedule)); s=json.dumps(res,indent=2,sort_keys=True)+'\n'; print(s,end='')
    if a.out: Path(a.out).write_text(s)
    raise SystemExit(0 if not res['errors'] else 1)
if __name__=='__main__': main()
