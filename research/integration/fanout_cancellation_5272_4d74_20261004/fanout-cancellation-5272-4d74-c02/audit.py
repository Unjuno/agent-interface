import json,pathlib,hashlib
R=pathlib.Path(__file__).resolve().parent;P=json.loads((R/'PLAN.json').read_text());F=json.loads((R/'FREEZE.json').read_text());raw=json.loads((R/'raw.json').read_text(encoding='utf-8-sig'));errors=[];summaries=[]
for name,digest in F['inputs'].items():
    if hashlib.sha256((R/name).read_bytes()).hexdigest()!=digest:errors.append('source:'+name)
expected={(c,p) for c in P['cases'] for p in P['policies']}
if {(r['case'],r['policy']) for r in raw['rows']}!=expected or len(raw['rows'])!=12:errors.append('coverage')
for row in raw['rows']:
    ev=row['events'];active=set();sealed=None;release=False;overlap=False;last=-1;times={}
    for e in ev:
        k=e['event'];times[k]=e['t_ns']
        if e['t_ns']<last:errors.append('clock');last=e['t_ns']
        last=e['t_ns']
        if k=='worker_start':active.add('original')
        if k=='replacement_start':active.add('replacement');overlap|='original' in active
        if k=='release_receipt':release=True
        if k=='worker_terminal':active.remove('original')
        if k=='replacement_terminal':active.remove('replacement')
        if sorted(active)!=e['live']:errors.append('live:'+row['case'])
        if k=='decision_sealed':sealed=e['decision']
        if k=='cell_terminal' and e['decision']!=sealed:errors.append('unsealed')
        if k=='slot_refunded' and row['policy']=='TERMINAL_RELEASE' and ('original' in active or not release):errors.append('premature_refund')
    if active:errors.append('unfinished')
    if sealed!=('UNKNOWN' if row['case']=='mandatory_unfinished' else 'FAIL'):errors.append('mandatory')
    if row['policy']=='TERMINAL_RELEASE' and overlap:errors.append('safe_overlap')
    if row['case'] in ('slow_cleanup','suppressed_late') and row['policy']=='REQUEST_ONLY' and not overlap:errors.append('contrast_absent')
    if row['case']=='missing_release' and row['policy']=='TERMINAL_RELEASE' and ('slot_hold' not in times or 'replacement_start' in times):errors.append('missing_release')
    if row['case']=='completion_race' and overlap:errors.append('null')
    if row['case']=='suppressed_late' and 'late_result' not in times:errors.append('late_missing')
    summaries.append(dict(case=row['case'],policy=row['policy'],overlap=overlap,decision=sealed,cancel_to_terminal_ns=times.get('worker_terminal',0)-times.get('cancel_requested',times.get('worker_terminal',0)),postdecision_to_terminal_ns=times['cell_terminal']-times['decision_sealed']))
print(json.dumps(dict(disposition='METHOD_PASS_SCOPED' if not errors else 'METHOD_FAIL',errors=errors,rows=summaries,scope='independent event-state reconstruction; fixture resource only'),indent=2));raise SystemExit(bool(errors))
