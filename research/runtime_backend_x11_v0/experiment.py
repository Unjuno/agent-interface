#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, random, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PORTABLE = HERE.parent / 'runtime_portability_v0'
if not PORTABLE.exists():
    external = os.environ.get('AGENT_INTERFACE_PORTABLE_ORACLE')
    if not external:
        raise RuntimeError('portable oracle path missing; set AGENT_INTERFACE_PORTABLE_ORACLE')
    PORTABLE = Path(external)
sys.path.insert(0, str(PORTABLE))
from contract import OFFICE_FLOOR, admit_program, capability_manifest  # noqa: E402
from backend_x11 import X11Backend  # noqa: E402


def read_events(path: Path) -> list[dict]:
    if not path.exists(): return []
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line]


def program(pid, seq, revision, expires, ops):
    if ops[-1].get('op') != 'release_all': ops = list(ops) + [{'op':'release_all'}]
    return {'schema':'agent-interface/program-v0','program_id':pid,
            'source':{'observation_seq':seq,'binding_revision':revision},
            'authority':{'lease_id':'x11-test','expires_at_ns':expires},
            'ops':ops,'terminal':{'release_all_required':True}}


def manifest():
    return capability_manifest('x11-private-v0','linux','x11',OFFICE_FLOOR,
        frames=('screen_physical_px','window_client'))


def run_case(name, p, backend, *, current_seq=7, current_revision=3):
    before_events = len(read_events(EVENTS))
    before_emit = backend.emissions
    adm = admit_program(p, manifest(), now_ns=time.monotonic_ns(),
                        current_observation_seq=current_seq,
                        current_binding_revision=current_revision)
    row = {'name':name,'admission':{'accepted':adm.accepted,'error':adm.error,
                                    'required_capabilities':list(adm.required_capabilities)},
           'emissions_before':before_emit,'fixture_events_before':before_events}
    if adm.accepted:
        row['execution'] = backend.execute(p)
        time.sleep(0.03)
    row['emissions_after'] = backend.emissions
    after = read_events(EVENTS)
    row['fixture_events_after'] = len(after)
    delta = after[before_events:]
    row['fixture_summary'] = {
        'kinds': [e.get('kind') for e in delta],
        'key_press_keysyms': [e.get('keysym') for e in delta if e.get('kind') == 'key_press'],
        'button_presses': [
            {'button': e.get('button'), 'x': e.get('x'), 'y': e.get('y')}
            for e in delta if e.get('kind') == 'button_press'
        ],
    }
    return row

EVENTS: Path

def main() -> int:
    global EVENTS
    ap = argparse.ArgumentParser()
    ap.add_argument('--display', required=True)
    ap.add_argument('--window-id', type=int, required=True)
    ap.add_argument('--events', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--seed', type=int, default=20260915)
    args = ap.parse_args(); EVENTS=args.events
    args.out.mkdir(parents=True, exist_ok=False)
    b = X11Backend(args.display, {'fixture':args.window_id})
    now = time.monotonic_ns(); future=now+30_000_000_000
    initial = b.capture('fixture','window_client',0,0,128,128)
    cases=[]
    valid = program('valid',7,3,future,[
        {'op':'focus','target':'fixture'},
        {'op':'pointer_move','frame':'window_client','x':40,'y':50},
        {'op':'pointer_button','button':'left','down':True},
        {'op':'pointer_button','button':'left','down':False},
        {'op':'text','text':'office'},
        {'op':'key_chord','keys':['CTRL','S']},
        {'op':'scroll','dx':0,'dy':-1},
        {'op':'wait_update','timeout_ms':10},
        {'op':'observe','frame':'window_client','x':0,'y':0,'w':128,'h':128},
        {'op':'release_all'}])
    cases.append(run_case('valid_effect',valid,b))
    stale = program('stale',6,3,future,[{'op':'focus','target':'fixture'},{'op':'key_chord','keys':['A']},{'op':'release_all'}])
    cases.append(run_case('stale_observation_zero_input',stale,b))
    bind = program('binding',7,2,future,[{'op':'focus','target':'fixture'},{'op':'key_chord','keys':['B']},{'op':'release_all'}])
    cases.append(run_case('stale_binding_zero_input',bind,b))
    expired = program('expired',7,3,1,[{'op':'focus','target':'fixture'},{'op':'key_chord','keys':['C']},{'op':'release_all'}])
    cases.append(run_case('expired_zero_input',expired,b))
    held = program('held',7,3,future,[{'op':'focus','target':'fixture'},{'op':'key_state','key':'SHIFT','down':True},{'op':'pointer_button','button':'left','down':True},{'op':'wait_update','timeout_ms':5},{'op':'release_all'}])
    cases.append(run_case('held_release',held,b))
    rng=random.Random(args.seed)
    stress=[]
    for i in range(64):
        x=rng.randrange(5,300); y=rng.randrange(5,180)
        key=rng.choice(['A','B','C','D','E'])
        p=program(f's{i}',7,3,future,[{'op':'focus','target':'fixture'},
            {'op':'pointer_move','frame':'window_client','x':x,'y':y},
            {'op':'key_chord','keys':[key]},{'op':'release_all'}])
        stress.append(run_case(f'stress_{i:02d}',p,b))
    time.sleep(0.05)
    final = b.capture('fixture','window_client',0,0,128,128)
    events=read_events(EVENTS)
    rejected=[r for r in cases if not r['admission']['accepted']]
    valid_summary = cases[0]['fixture_summary']
    valid_left = [x for x in valid_summary['button_presses'] if x['button'] == 1]
    valid_scroll = [x for x in valid_summary['button_presses'] if x['button'] == 4]
    expected_keys = {'o','f','i','c','e','Control_L','s'}
    valid_effect_exact = (
        'focus_in' in valid_summary['kinds']
        and 'motion' in valid_summary['kinds']
        and any(x['x'] == 40 and x['y'] == 50 for x in valid_left)
        and bool(valid_scroll)
        and expected_keys.issubset(set(valid_summary['key_press_keysyms']))
        and len(cases[0].get('execution', {}).get('observations', [])) == 1
    )
    zero_input_reject=all(r['emissions_after']==r['emissions_before'] and r['fixture_events_after']==r['fixture_events_before'] for r in rejected)
    accepted=[r for r in cases+stress if r['admission']['accepted']]
    releases=[x for r in accepted for x in r.get('execution',{}).get('releases',[])]
    result={
      'schema':'agent-interface/x11-backend-conformance-v0', 'seed':args.seed,
      'display':args.display, 'window_id':args.window_id,
      'capabilities':b.capabilities(), 'geometry':b.geometry('fixture'),
      'cases':cases, 'stress_count':len(stress),
      'stress_all_admitted':all(r['admission']['accepted'] for r in stress),
      'stress_all_released':all(all(x['verified'] for x in r['execution']['releases']) for r in stress),
      'rejected_zero_backend_input':zero_input_reject,
      'all_release_receipts_verified':bool(releases) and all(x['verified'] and x['keys_down']==[] and x['buttons_down']==[] for x in releases),
      'valid_effect_exact': valid_effect_exact,
      'capture_changed_after_delivered_effects':initial['sha256']!=final['sha256'],
      'initial_capture':initial,'final_capture':final,
      'fixture_event_count':len(events),
      'fixture_effect_event_count':sum(e.get('kind') in {'key_press','button_press'} for e in events),
      'scope':'private Xvfb/XTEST/Xlib fixture; X11 reference only; no model/token/native-Windows/macOS/Wayland claim',
    }
    result['passed']=all([cases[0]['admission']['accepted'], cases[4]['admission']['accepted'],
      len(rejected)==3, zero_input_reject, result['stress_all_admitted'],result['stress_all_released'],
      result['all_release_receipts_verified'], result['valid_effect_exact'], result['capture_changed_after_delivered_effects'],
      result['fixture_effect_event_count']>0])
    (args.out/'report.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['passed','stress_count','rejected_zero_backend_input','all_release_receipts_verified','valid_effect_exact','capture_changed_after_delivered_effects','fixture_event_count','fixture_effect_event_count']},indent=2))
    b.close(); return 0 if result['passed'] else 1

if __name__=='__main__': raise SystemExit(main())
