from __future__ import annotations
import hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent
DIST=(1,8,64,256)

def med(v):
    s=sorted(v); n=len(s); return s[n//2] if n%2 else (s[n//2-1]+s[n//2])/2

def p95(v):
    s=sorted(v); return s[math.ceil(.95*len(s))-1]

def main():
    rows=json.loads((ROOT/'FORMAL_ROWS.json').read_text()); r=json.loads((ROOT/'RESULT.json').read_text()); e=[]
    if len(rows)!=400 or r.get('rows')!=400 or r.get('formal_invocations')!=1 or r.get('reruns')!=0:e.append('allocation')
    seen={d:[] for d in DIST}; blocks={}
    for row in rows:
        d=row.get('distance_px'); blocks.setdefault(row.get('block'),[]).append(d)
        if d not in seen:e.append('distance'); continue
        seen[d].append(row['duration_ns'])
        if not row.get('exact') or not row.get('neutral'):e.append('readback')
        if row.get('duration_ns')!=row.get('sync_return_ns')-row.get('issued_ns') or row.get('duration_ns',0)<=0:e.append('timing')
    if set(blocks)!=set(range(100)) or any(sorted(v)!=list(DIST) for v in blocks.values()):e.append('block_schedule')
    if any(len(v)!=100 for v in seen.values()):e.append('counts')
    by={str(d):{'n':len(seen[d]),'p50_ns':med(seen[d]),'p95_ns':p95(seen[d]),'min_ns':min(seen[d]),'max_ns':max(seen[d])} for d in DIST}
    if r.get('by_distance')!=by:e.append('summary')
    ms=max(v['p50_ns'] for v in by.values())-min(v['p50_ns'] for v in by.values())
    ps=max(v['p95_ns'] for v in by.values())-min(v['p95_ns'] for v in by.values())
    if r.get('median_spread_ns')!=ms or r.get('p95_spread_ns')!=ps:e.append('spread')
    expected=('PASS_X11_ABSOLUTE_RELOCATION_DISTANCE_FLAT_SCOPED' if ms<=250000 and ps<=750000 else 'HOLD_X11_DISTANCE_COMPONENT_EXPOSED')
    if r.get('decision')!=expected or r.get('cleanup')!='PASS':e.append('decision')
    out={'pass':not e,'errors':sorted(set(e)),'decision':r.get('decision') if not e else 'FAIL_INTEGRITY',
         'result_sha256':hashlib.sha256((ROOT/'RESULT.json').read_bytes()).hexdigest(),
         'rows_sha256':hashlib.sha256((ROOT/'FORMAL_ROWS.json').read_bytes()).hexdigest()}
    (ROOT/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True));raise SystemExit(0 if not e else 1)
if __name__=='__main__':main()
