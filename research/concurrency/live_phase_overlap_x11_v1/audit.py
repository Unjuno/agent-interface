import json, pathlib, statistics, sys
root=pathlib.Path(__file__).parent
schedule=json.loads((root/'schedule.json').read_text())['cases']
raw=json.loads((root/'RAW_CASES.json').read_text())
res=json.loads((root/'RESULT.json').read_text())
errors=[]
expected_arms={'serial_independent','overlap_independent','serial_shared','overlap_shared'}
if len(raw)!=24: errors.append(f'raw_count={len(raw)}')
if [(r.get('case_id'),r.get('arm')) for r in raw] != [(r['case_id'],r['arm']) for r in schedule]: errors.append('schedule_mismatch')
by={a:[] for a in expected_arms}
for r in raw:
    arm=r.get('arm')
    if arm not in by: errors.append('unknown_arm'); continue
    by[arm].append(r)
    required=['wall_ms','effects','pixels','space_neutral','keypress_counts','b_keypress_before_a_effect','a_effect_before_b_keypress']
    if any(k not in r for k in required): errors.append(f"missing_fields:{r.get('case_id')}"); continue
    if r['keypress_counts']!={'A':1,'B':1}: errors.append(f"keypress_count:{r['case_id']}")
    if not r['space_neutral']: errors.append(f"key_not_neutral:{r['case_id']}")
    if arm.startswith('overlap_'):
        if not r['b_keypress_before_a_effect'] or r['a_effect_before_b_keypress']:
            errors.append(f"overlap_order:{r['case_id']}")
    else:
        if not r['a_effect_before_b_keypress'] or r['b_keypress_before_a_effect']:
            errors.append(f"serial_order:{r['case_id']}")

for arm in expected_arms:
    if len(by[arm])!=6: errors.append(f'{arm}_n={len(by[arm])}')

correct_pixels={'A':[255,0,0],'B':[0,0,255]}
for arm in ['serial_independent','overlap_independent','serial_shared']:
    for r in by[arm]:
        if r.get('effects')!={'A':'A','B':'B'}: errors.append(f"effect_wrong:{r['case_id']}")
        if r.get('pixels')!=correct_pixels or not r.get('pixel_correct'): errors.append(f"pixel_wrong:{r['case_id']}")
for r in by['overlap_shared']:
    if r.get('effects')!={'A':'B','B':'B'}: errors.append(f"negative_effect_missing:{r['case_id']}")
    if r.get('pixels')!={'A':[0,0,255],'B':[0,0,255]} or r.get('pixel_correct'):
        errors.append(f"negative_pixel_missing:{r['case_id']}")

smed=statistics.median(r['wall_ms'] for r in by['serial_independent']) if len(by['serial_independent'])==6 else None
omed=statistics.median(r['wall_ms'] for r in by['overlap_independent']) if len(by['overlap_independent'])==6 else None
ratio=omed/smed if smed and omed else None
reduction=smed-omed if smed and omed else None
if ratio is None or ratio>0.65: errors.append(f'ratio={ratio}')
if reduction is None or reduction<100: errors.append(f'reduction={reduction}')
if res.get('formal_invocations')!=1 or res.get('reruns')!=0 or res.get('tuning_after_freeze')!=0: errors.append('formal_budget')
rm=res.get('metrics',{})
if smed is not None and abs(rm.get('serial_independent_median_wall_ms',-1)-smed)>1e-9: errors.append('serial_median_mismatch')
if omed is not None and abs(rm.get('overlap_independent_median_wall_ms',-1)-omed)>1e-9: errors.append('overlap_median_mismatch')

decision='PASS_LIVE_PHASE_OVERLAP_X11_SCOPED' if not errors else 'FAIL_LIVE_PHASE_OVERLAP_X11'
out={'decision':decision,'pass':not errors,'errors':errors,'serial_median_ms':smed,'overlap_median_ms':omed,'median_reduction_ms':reduction,'overlap_serial_ratio':ratio,'arm_counts':{a:len(by[a]) for a in sorted(by)}}
(root/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True))
sys.exit(0 if not errors else 1)
