"""Read-only separate raw audit. Imports neither runtime nor experiment code."""
import collections, hashlib, json, sys
from pathlib import Path

def audit(root):
    root=Path(root); errors=[]; checks=0; counts=collections.Counter(); sessions=set()
    def check(ok,label):
        nonlocal checks
        checks+=1
        if not ok: errors.append(label)
    freeze=json.loads((root/'FREEZE.json').read_text())
    for rel,digest in freeze['files'].items():
        p=root/rel;check(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==digest,'source:'+rel)
    expected_conditions={'OFF','INITIAL_ON','PROGRAM_ON','PROGRAM_OFF','PROGRAM_ROUNDTRIP','ON_DIGITS'}
    folders=sorted((root/'formal').glob('batch*'))
    check(len(folders)==4,'batch count')
    for folder in folders:
        batch=json.loads((folder/'BATCH.json').read_text()); b=int(folder.name[5:])
        arm=['CURRENT','TEXT_LOCK_GUARD'][b%2];guard=arm=='TEXT_LOCK_GUARD'
        check(batch['complete'] is True and len(batch['rows'])==6,'batch complete '+str(b))
        check(batch['arm']==arm and batch['rep']==b//2,'batch identity '+str(b))
        check({q.name for q in folder.iterdir() if q.is_dir()}==expected_conditions,'case coverage '+str(b))
        outer={row['condition']:row for row in batch['rows']}
        for condition in sorted(expected_conditions):
            p=folder/condition
            if not p.is_dir(): continue
            r=json.loads((p/'record.json').read_text()); program=json.loads((p/'program.json').read_text())
            response=json.loads((p/'response.json').read_text()); events=[json.loads(x) for x in (p/'app.jsonl').read_text().splitlines()]
            tag=str(b)+':'+condition; sid=f'k8n4-r{b//2}-{arm.lower()}-{condition.lower()}'
            check(r['session']==sid and sid not in sessions,'session '+tag);sessions.add(sid)
            check(program['program_id']==sid and outer[condition]['session']==sid,'program binding '+tag)
            check(r['arm']==arm and r['condition']==condition,'arm/condition '+tag)
            check(r['errors']==[] and outer[condition]['exit']==0,'driver exit '+tag)
            check(outer[condition]['pid']==r['driver_pid'],'driver pid '+tag)
            check(r['app']['exit']==0 and r['app'].get('forced_cleanup') is not True,'app exit '+tag)
            check(r['xvfb']['exit'] in (0,-15) and r['xvfb']['termination_requested'] is True,'xvfb exit '+tag)
            check(r['display_socket_removed'] is True,'display cleanup '+tag)
            check(r['response']==response,'response bytes '+tag)
            check(all(e['pid']==r['app']['pid'] for e in events),'app pid '+tag)
            check(all(x['ns']<=y['ns'] for x,y in zip(events,events[1:])),'app order '+tag)
            check(r['app_before']['value']=='','initial value '+tag)
            initial_on=condition in ('INITIAL_ON','PROGRAM_OFF','ON_DIGITS')
            final_on=condition in ('INITIAL_ON','PROGRAM_ON','ON_DIGITS')
            check(r['before']['lock'] is initial_on and r['before_app']['lock'] is initial_on,'initial lock '+tag)
            check(r['fixture_setup_emissions']==(2 if initial_on else 0),'setup count '+tag)
            for phase in ('before','after','terminal'):
                s=r[phase]
                check(len(s['keymap'])==32 and all(type(n) is int and n==0 for n in s['keymap']),'neutral '+phase+tag)
                check(type(s['mask']) is int and s['mask'] & 0x1f00==0,'buttons '+phase+tag)
                check(s['started_ns']<=s['ended_ns'],'query brackets '+phase+tag)
                check(s['lock'] is bool(s['mask'] & 2),'mask flag '+phase+tag)
            check(r['after']['lock'] is final_on and r['terminal']['lock'] is final_on,'final lock '+tag)
            check(r['before']['ended_ns']<r['dispatch_started_ns']<r['dispatch_ended_ns']<r['after']['started_ns'],'dispatch order '+tag)
            refuse=guard and final_on
            expected_value=('1' if condition=='PROGRAM_ON' else '') if refuse else {
                'OFF':'aB2','INITIAL_ON':'Ab2','PROGRAM_ON':'1Ab2','PROGRAM_OFF':'aB2',
                'PROGRAM_ROUNDTRIP':'aB2','ON_DIGITS':'12'}[condition]
            expected_keys=({'OFF':8,'INITIAL_ON':8,'PROGRAM_ON':12,'PROGRAM_OFF':10,'PROGRAM_ROUNDTRIP':12,'ON_DIGITS':4}[condition]
                           if not refuse else (4 if condition=='PROGRAM_ON' else 0))
            check(r['app_after']['value']==expected_value and r['app_close']['value']==expected_value,'value '+tag)
            check(events[-1]['event']=='exit' and events[-1]['value']==expected_value,'final app event '+tag)
            snapshots=[e for e in events if e['event']=='snapshot'];check(snapshots==[r['app_before'],r['app_after'],r['app_close']],'snapshot IPC '+tag)
            pressed=collections.Counter(); keys=[e for e in events if e['event'] in ('KeyPress','KeyRelease')]
            for e in keys: pressed[e['keycode']]+=1 if e['event']=='KeyPress' else -1
            check(all(n==0 for n in pressed.values()),'key pairs '+tag)
            check(len(keys)==expected_keys,'key count '+tag)
            execution=response.get('result',{}).get('execution',{});status=response.get('result',{}).get('status')
            check(response.get('status')=='returned','public return '+tag)
            check(status==('execution_failed' if refuse else 'completed'),'status '+tag)
            check(execution.get('program_emissions')==expected_keys,'native emission '+tag)
            releases=execution.get('releases',[])
            check(len(releases)==1 and all(x.get('verified') is True and x.get('keys_down')==[] and x.get('buttons_down')==[] for x in releases),'release '+tag)
            if refuse:
                failed=3 if condition=='PROGRAM_ON' else 1
                check(execution.get('failed_op')==failed and type(execution.get('failed_op')) is int,'failed index '+tag)
                check('CAPS_LOCK_ACTIVE' in execution.get('error',''),'guard reason '+tag)
                check(execution.get('completed_ops')==list(range(failed)),'partial prefix '+tag)
                check(execution.get('failed_op_effect')=='unknown; may have emitted partial input','uncertainty retained '+tag)
            else: check(execution.get('completed_ops')==list(range(len(program['ops']))),'complete prefix '+tag)
            source='candidate_source' if guard else 'current_source'
            for name,item in r['runtime_imports'].items():
                check(freeze['files'].get(source+'/'+item['path'])==item['sha256'],'import '+tag+':'+name)
            check('runtime.cli_v1.api' in r['runtime_imports'] and 'runtime.backends.x11_v1.session' in r['runtime_imports'],'public composition '+tag)
            counts[arm+'_cases']+=1;counts[arm+'_key_events']+=len(keys)
            counts[arm+'_wrong_text']+=int(not guard and condition in ('INITIAL_ON','PROGRAM_ON'))
            counts[arm+'_refused_text']+=int(refuse)
    check(len(sessions)==24,'total cases')
    return {'checks':checks,'errors':errors,'counts':dict(sorted(counts.items())),
            'decision':'PASS_PUBLIC_TEXT_LOCK_BOUNDARY_SCOPED' if not errors else 'HOLD_OR_FAIL_REVIEW_REQUIRED',
            'task_success_claim':False,'independent_nonauthor_review':False}
if __name__=='__main__':
    out=audit(sys.argv[1]); print(json.dumps(out,sort_keys=True,indent=2));raise SystemExit(bool(out['errors']))
