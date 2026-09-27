#!/usr/bin/env python3
"""Independent result audit. Imports no measured runner or bus client."""
import argparse,json,hashlib
from pathlib import Path
EXPECTED_PKG='135b9619d7f8bf8996adcee7a869af2563184faaa7eae8f1e384ede62846252f'
KNOWN={'Reset to simple snapping mode','Advanced mode','Open Collections Editor'}
def audit(root):
    root=Path(root); dirs=sorted(p for p in root.glob('case-*') if p.is_dir()); errors=[]; rows=[]
    if len(dirs)!=3: errors.append(f'expected 3 case dirs, got {len(dirs)}')
    for d in dirs:
        p=d/'result.json'
        if not p.is_file(): errors.append(f'{d.name}: missing result'); continue
        r=json.loads(p.read_text()); e=[]
        if r.get('task')!='ATSPI-STANDARD-STACK-20260916-022': e.append('task')
        if r.get('package_sha256')!=EXPECTED_PKG: e.append('package')
        if r.get('session_a11y_bus_owner') is not True: e.append('a11y_bus_owner')
        if r.get('registry_owner') is not True or r.get('registry_get_events_rc')!=0: e.append('registry')
        li=r.get('listener') or {}
        if li.get('registered') is not True or li.get('event')!='object:state-changed:focused' or li.get('return_type')!='()': e.append('listener')
        w=(r.get('widget') or {}).get('known_widget')
        if not isinstance(w,dict) or w.get('name') not in KNOWN or w.get('role')!='button' or 'org.a11y.atspi.Action' not in (w.get('interfaces') or []): e.append('widget_control')
        app=r.get('app_bus'); start=r.get('op_start_epoch'); end=r.get('op_end_epoch'); ev=r.get('focused_events_operation_window')
        if not isinstance(ev,list) or not ev: e.append('event_missing')
        else:
            for x in ev:
                if x.get('sender')!=app: e.append('event_sender'); break
                if x.get('interface')!='org.a11y.atspi.Event.Object' or x.get('member')!='StateChanged': e.append('event_kind'); break
                if not x.get('strings') or x['strings'][0]!='focused': e.append('event_detail'); break
                if not isinstance(x.get('time'),(int,float)) or x['time'] < start-0.05 or x['time'] > end+0.2: e.append('event_time'); break
        if r.get('focused_operation_event_count') != len(ev or []): e.append('event_count')
        if r.get('svg_unchanged') is not True or r.get('svg_before_sha256')!=r.get('svg_after_sha256'): e.append('svg')
        if r.get('final_keymap_empty') is not True or set(r.get('final_keymap_hex',''))-{'0'}: e.append('keymap')
        if r.get('pass') is not True: e.append('runner_pass')
        rows.append({'case':d.name,'errors':sorted(set(e)),'event_count':r.get('focused_operation_event_count'),'widget':w.get('name') if isinstance(w,dict) else None,'app_bus':app})
        errors.extend(f'{d.name}:{x}' for x in sorted(set(e)))
    return {'schema':'atspi-standard-stack-audit-v1','pass':not errors,'decision':'PASS_STANDARD_ATSPI_EVENT_POSITIVE_CONTROL' if not errors else 'FAIL_AUDIT','errors':errors,'rows':rows}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('root');ap.add_argument('--out');a=ap.parse_args();o=audit(a.root);s=json.dumps(o,indent=2,sort_keys=True)+'\n';print(s,end='');
    if a.out:Path(a.out).write_text(s)
    raise SystemExit(0 if o['pass'] else 1)
if __name__=='__main__':main()
