"""Copied-evidence controls, never a GUI or candidate rerun."""
import copy
import json
from pathlib import Path
import sys
from audit import verify_case


def changed_cases(o):
    definitions=(
        ('authority',lambda c:c['response'].__setitem__('authority_granted',True)),
        ('action',lambda c:c['response'].__setitem__('action',{'type':'click'})),
        ('lease',lambda c:c['response'].__setitem__('lease_extended',True)),
        ('roi',lambda c:c['response'].__setitem__('roi',[0,0,16,16])),
        ('pixel',lambda c:c['response']['frames'][0].__setitem__('pixels_b64','AA==')),
        ('generation',lambda c:c['request']['cue'].__setitem__('generation',2)),
        ('foreign_session',lambda c:c['request']['cue'].__setitem__('session','other-session')),
        ('app_effect',lambda c:c['after'].__setitem__('state',4)),
        ('history',lambda c:c['response'].__setitem__('history','MISSING_HISTORY')),
        ('missing_frame',lambda c:c['response']['frames'].pop(0)),
        ('process_exit',lambda c:next(p for p in c['processes'] if p['role']=='engine').__setitem__('returncode',17)),
        ('crop_time',lambda c:c['response']['frames'][1].__setitem__('captured_ns',c['response']['frames'][1]['captured_ns']+1)),
    )
    for name,change in definitions:
        case=copy.deepcopy(o); change(case)
        case['engine_stdin']=json.dumps(case['request'],sort_keys=True)+'\n'
        case['engine_stdout']=json.dumps(case['response'],sort_keys=True)+'\n'
        if name=='app_effect': case['wire'][10]['value']=copy.deepcopy(case['after'])
        if name=='missing_frame': case['response']['decoded_bytes']=len(case['response']['frames'])*1024; case['engine_stdout']=json.dumps(case['response'],sort_keys=True)+'\n'
        yield name,case


def main():
    source,out=Path(sys.argv[1]),Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=False)
    original=json.loads(source.read_text()); assert not verify_case(original)['errors']
    results={}
    for name,case in changed_cases(original):
        changed=case!=original
        result=verify_case(case)
        (out/(name+'.json')).write_text(json.dumps(case,sort_keys=True)+'\n')
        results[name]={'changed':changed,'errors':result['errors'],
                       'rejected':changed and bool(result['errors']) and not any(e.startswith('malformed:') for e in result['errors'])}
    (out/'CONTROLS.json').write_text(json.dumps(results,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'controls':len(results),'rejected':sum(v['rejected'] for v in results.values())}))
    raise SystemExit(not all(v['rejected'] for v in results.values()))


if __name__=='__main__': main()
