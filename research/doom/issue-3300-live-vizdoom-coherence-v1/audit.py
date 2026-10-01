import json,sys
rows=[json.loads(x) for x in open(sys.argv[1]) if x.strip()]; errors=[]
if len(rows)!=36: errors.append(f'rows={len(rows)} expected=36')
if {r.get('stratum') for r in rows} != {'idle','cpu_load','delayed_read'}: errors.append('strata')
for r in rows:
    if r.get('clock_hz')!=35 or len(r.get('attempts',[]))!=3: errors.append(f"shape {r.get('stratum')} {r.get('sample')}")
    for a in r.get('attempts',[]):
        if a.get('api_status')!='ok' or a.get('span_ns',-1)<0: errors.append('api/span')
        if a.get('crossed_tic') != (a.get('tic_after')>a.get('tic_before')): errors.append('crossing')
        if a.get('monotonic_end_ns',0)<a.get('monotonic_start_ns',0): errors.append('monotonic')
print(f"{'PASS' if not errors else 'HOLD'}_LIVE_VIZDOOM_COHERENCE rows={len(rows)} errors={len(errors)}")
for e in errors: print('ERROR',e)
raise SystemExit(bool(errors))