#!/usr/bin/env python3
"""Independent auditor for the retained XTEST cross-client raw record."""
import argparse, hashlib, json
from pathlib import Path

def audit(raw_bytes):
    raw=json.loads(raw_bytes); checks=[]
    def check(name, ok, detail=''):
        checks.append({'name':name,'ok':bool(ok),'detail':detail})
    check('schema',raw.get('schema')=='x11-xtest-device-cross-client-raw-a01-v1')
    check('candidate-completed',raw.get('status')=='CANDIDATE_COMPLETE' and raw.get('candidate_exit')==0)
    check('frozen-display',raw.get('display')==':87')
    devs=raw.get('devices_found',[])
    check('one-shared-XTEST-keyboard',len(devs)==1 and devs[0][1]==raw.get('device_name') and devs[0][0]==raw.get('device_id'))
    conns=raw.get('client_connections',{})
    check('four-distinct-client-roles',all(conns.get(k) is True for k in ('receiver','observer','A','B')) and conns.get('A_and_B_distinct') is True)
    check('initial-keymap-neutral',raw.get('initial_keymap_down') is False)
    handles=raw.get('device_handles_open',{})
    check('two-client-handles-open-same-device',handles.get('A') is True and handles.get('B') is True and handles.get('same_server_device_id')==raw.get('device_id'))
    check('cleanup-closed-four-displays',raw.get('cleanup',{}).get('displays_closed')==4 and 'exception' not in raw.get('cleanup',{}))
    check('no-X-errors',raw.get('x_errors')==[])
    expected=[(r,a,e) for r in ('core','device') for a,e in (('A','DOWN'),('B','DOWN'),('A','UP'),('B','UP'))]
    calls=raw.get('api_calls',[])
    check('eight-API-calls',[(c.get('route'),c.get('actor'),c.get('edge')) for c in calls]==expected)
    check('API-calls-returned-success',len(calls)==8 and all(isinstance(c.get('return_code'),int) and c['return_code']!=0 for c in calls))
    routes=raw.get('routes',[])
    check('two-routes',[r.get('route') for r in routes]==['core','device'])
    outcomes={}
    for r in routes:
        name=r.get('route'); steps=r.get('steps',[])
        check(name+'-four-steps',len(steps)==4)
        if len(steps)!=4: continue
        check(name+'-order',[(s.get('actor'),s.get('edge')) for s in steps]==[('A','DOWN'),('B','DOWN'),('A','UP'),('B','UP')])
        check(name+'-key-state-after-downs',steps[0].get('keymap_down') is True and steps[1].get('keymap_down') is True)
        check(name+'-final-neutral',steps[3].get('keymap_down') is False)
        for ix,step in enumerate(steps):
            evs=step.get('core_events',[])
            check(name+'-step-'+str(ix)+'-event-shape',all(e.get('type') in ('KeyPress','KeyRelease') and e.get('keycode')==raw.get('keycode') and e.get('window_id')==raw.get('window_id') for e in evs),json.dumps(evs,sort_keys=True))
        release=any(e.get('type')=='KeyRelease' for e in steps[2].get('core_events',[]))
        neutral=steps[2].get('keymap_down') is False
        if neutral and release: outcomes[name]='releases-at-A-UP'
        elif steps[2].get('keymap_down') is True and not release: outcomes[name]='held-until-B-UP'
        else: outcomes[name]='inconsistent'
    check('core-control-reproduces-cross-client-release',outcomes.get('core')=='releases-at-A-UP',outcomes.get('core','missing'))
    dv=outcomes.get('device','missing')
    check('device-observation-classified',dv in ('releases-at-A-UP','held-until-B-UP'),dv)
    verdict='INDETERMINATE_STOP' if outcomes.get('core')!='releases-at-A-UP' or dv not in ('releases-at-A-UP','held-until-B-UP') else ('DEVICE_PATH_ISOLATES' if dv=='held-until-B-UP' else 'DEVICE_PATH_DOES_NOT_ISOLATE')
    return {'schema':'x11-xtest-device-cross-client-audit-a01-v1','raw_sha256':hashlib.sha256(raw_bytes).hexdigest(),'checks':checks,'verdict':verdict,'audit_exit':0 if all(c['ok'] for c in checks) else 1}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--raw',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    raw_bytes=Path(a.raw).read_bytes(); result=audit(raw_bytes); out=Path(a.out); out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'audit':str(out),'verdict':result['verdict'],'checks_passed':sum(c['ok'] for c in result['checks']),'checks_total':len(result['checks']),'audit_exit':result['audit_exit']},sort_keys=True))
    return result['audit_exit']
if __name__=='__main__': raise SystemExit(main())
