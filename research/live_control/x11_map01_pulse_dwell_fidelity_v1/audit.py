import argparse, json, pathlib, statistics, sys

MAX_DELTA_MS = 5.0
MIN_X_DWELL_MS = 180
MAX_X_DWELL_MS = 230

def audit_case(case_dir):
    events = json.loads((case_dir/'events.json').read_text())
    ctl = json.loads((case_dir/'controller.json').read_text())
    errors=[]; rows=[]
    if len(events) != 12: errors.append(f'event_count={len(events)}')
    if len(ctl['ops']) != 12: errors.append(f'op_count={len(ctl["ops"])}')
    if ctl['focus_after'] != ctl['window_id']: errors.append('focus_not_verified')
    if ctl['final_right_down']: errors.append('final_right_down')
    expected=['press','release']*6
    if [e['kind'] for e in events] != expected: errors.append('event_order')
    if [o['kind'] for o in ctl['ops']] != expected: errors.append('op_order')
    if events and any(e['keycode'] != ctl['keycode'] or e['keysym'] != 'Right' for e in events): errors.append('wrong_key_event')
    if len(events)==12 and len(ctl['ops'])==12:
        for i in range(6):
            ep,er=events[2*i],events[2*i+1]; op,orr=ctl['ops'][2*i],ctl['ops'][2*i+1]
            x_dwell = er['x_time_ms'] - ep['x_time_ms']
            controller_dwell = (orr['before_ns'] - op['after_sync_ns'])/1e6
            callback_dwell = (er['callback_ns'] - ep['callback_ns'])/1e6
            delta = abs(x_dwell-controller_dwell)
            if not (MIN_X_DWELL_MS <= x_dwell <= MAX_X_DWELL_MS): errors.append(f'pulse{i+1}_x_dwell={x_dwell}')
            if delta > MAX_DELTA_MS: errors.append(f'pulse{i+1}_delta={delta:.6f}')
            rows.append({'pulse':i+1,'x_dwell_ms':x_dwell,'controller_dwell_ms':controller_dwell,'callback_dwell_ms':callback_dwell,'abs_x_minus_controller_ms':delta})
    return errors, rows

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--plan',required=True); ap.add_argument('--results-root',required=True); ap.add_argument('--out'); args=ap.parse_args()
    plan=json.loads(pathlib.Path(args.plan).read_text()); root=pathlib.Path(args.results_root); errors=[]; cases=[]; all_rows=[]
    for spec in plan['cases']:
        d=root/spec['case_id']
        if not d.exists(): errors.append([spec['case_id'],'missing_case']); continue
        e,rows=audit_case(d); cases.append({'case_id':spec['case_id'],'errors':e,'pulses':rows}); all_rows.extend(rows)
        errors.extend([[spec['case_id'],x] for x in e])
    if len(cases)!=12: errors.append(['aggregate','case_count',len(cases)])
    decision='PASS_X11_SIX_PULSE_DWELL_FIDELITY_SCOPED' if not errors else ('X11_DWELL_DISTORTION_OBSERVED_SCOPED' if errors and all(('delta=' in str(x)) for x in errors if len(x)>1 and 'pulse' in str(x)) else 'FAIL_INTEGRITY')
    # precise disposition: if all structural gates pass and only >5ms dwell deltas fail, call distortion.
    flat=[str(x) for x in errors]
    non_delta=[x for x in flat if 'delta=' not in x]
    if errors and not non_delta: decision='X11_DWELL_DISTORTION_OBSERVED_SCOPED'
    out={'decision':decision,'errors':errors,'case_count':len(cases),'pulse_count':len(all_rows),'cases':cases}
    if all_rows:
        vals=[r['x_dwell_ms'] for r in all_rows]; ds=[r['abs_x_minus_controller_ms'] for r in all_rows]
        out['summary']={'x_dwell_min_ms':min(vals),'x_dwell_max_ms':max(vals),'x_dwell_median_ms':statistics.median(vals),'max_abs_x_minus_controller_ms':max(ds),'median_abs_x_minus_controller_ms':statistics.median(ds)}
    text=json.dumps(out,indent=2,sort_keys=True)+'\n'
    if args.out: pathlib.Path(args.out).write_text(text)
    print(text,end=''); sys.exit(0 if decision.startswith('PASS_') else 1)

if __name__=='__main__': main()
