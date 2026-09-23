import json,sys
from pathlib import Path

rows=[json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines() if line]
errors=[]
if len(rows)!=36: errors.append(f'rows={len(rows)} expected=36')
if {r.get('stratum') for r in rows}!={'idle','cpu_load','delayed_read'}: errors.append('strata')
for row in rows:
    if len(row.get('attempts',[]))!=3: errors.append('outer_attempt_count')
    for call in row.get('attempts',[]):
        reads=call.get('reads',[])
        if not reads or len(reads)%2: errors.append('unpaired_getter_reads'); continue
        pairs=list(zip(reads[::2],reads[1::2]))
        for a,b in pairs:
            if b['start_ns']<a['end_ns']: errors.append('getter_order')
        coherent=any(a['tic']==b['tic'] for a,b in pairs)
        if coherent!=call.get('coherent'): errors.append('scorer_decision_mismatch')
        if call.get('read_count')!=len(reads): errors.append('read_count_mismatch')
        if call['end_ns']<call['start_ns']: errors.append('call_clock_order')
summary=[]
for stratum in ('idle','cpu_load','delayed_read'):
    group=[r for r in rows if r['stratum']==stratum]
    calls=[a for r in group for a in r['attempts']]
    pairs=[(a,b) for c in calls for a,b in zip(c['reads'][::2],c['reads'][1::2])]
    summary.append(dict(stratum=stratum,rows=len(group),outer_attempts=len(calls),
        coherent_calls=sum(c['coherent'] for c in calls),failed_calls=sum(not c['coherent'] for c in calls),
        internal_read_pairs=len(pairs),crossed_pairs=sum(a['tic']!=b['tic'] for a,b in pairs)))
print(json.dumps(dict(decision='PASS_CONSTRUCTION_AUDIT' if not errors else 'HOLD',errors=errors,summary=summary),sort_keys=True))
raise SystemExit(bool(errors))
