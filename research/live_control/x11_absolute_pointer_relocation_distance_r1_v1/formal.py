from __future__ import annotations
import json, math, platform, statistics, sys
from pathlib import Path
from common import *
ROOT=Path(__file__).resolve().parent
BLOCKS=100

def p95(values):
    s=sorted(values); return s[math.ceil(.95*len(s))-1]

def main():
    p,name=start_xvfb(); rows=[]; cleanup='UNKNOWN'
    try:
        actor=display.Display(name); observer=display.Display(name)
        for block in range(BLOCKS):
            shift=block%len(DISTANCES)
            order=DISTANCES[shift:]+DISTANCES[:shift]
            for order_index,distance in enumerate(order):
                reset(actor,observer)
                t0,t1=move_sync(actor,CX+distance,CY)
                x,y,mask=read_pointer(observer)
                rows.append({'block':block,'order_index':order_index,'distance_px':distance,
                             'issued_ns':t0,'sync_return_ns':t1,'duration_ns':t1-t0,
                             'readback_x':x,'readback_y':y,'mask':mask,
                             'exact':(x,y)==(CX+distance,CY),'neutral':(mask&BUTTON_MASK)==0})
        actor.close(); observer.close(); cleanup='CLOSED_CLIENTS'
    finally:
        stop_xvfb(p)
        if cleanup=='CLOSED_CLIENTS': cleanup='PASS'
    (ROOT/'FORMAL_ROWS.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
    by={}
    for d in DISTANCES:
        vals=[r['duration_ns'] for r in rows if r['distance_px']==d]
        by[str(d)]={'n':len(vals),'p50_ns':statistics.median(vals),'p95_ns':p95(vals),'min_ns':min(vals),'max_ns':max(vals)}
    p50s=[v['p50_ns'] for v in by.values()]; p95s=[v['p95_ns'] for v in by.values()]
    median_spread=max(p50s)-min(p50s); p95_spread=max(p95s)-min(p95s)
    integrity=(len(rows)==400 and all(r['exact'] and r['neutral'] and r['duration_ns']>0 and r['sync_return_ns']>r['issued_ns'] for r in rows) and cleanup=='PASS')
    flat=median_spread<=250000 and p95_spread<=750000
    decision=('PASS_X11_ABSOLUTE_RELOCATION_DISTANCE_FLAT_SCOPED' if integrity and flat else
              'HOLD_X11_DISTANCE_COMPONENT_EXPOSED' if integrity else 'FAIL_X11_RELOCATION_INTEGRITY')
    out={'task':'X11-ABSOLUTE-POINTER-RELOCATION-DISTANCE-R1-20260918-001','formal_invocations':1,'reruns':0,
         'rows':len(rows),'by_distance':by,'median_spread_ns':median_spread,'p95_spread_ns':p95_spread,
         'exact_rows':sum(r['exact'] for r in rows),'neutral_rows':sum(r['neutral'] for r in rows),'cleanup':cleanup,
         'display':name,'environment':{'python':sys.version.split()[0],'platform':platform.platform(),'xvfb':'private'},
         'decision':decision,'pass':decision=='PASS_X11_ABSOLUTE_RELOCATION_DISTANCE_FLAT_SCOPED'}
    (ROOT/'RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if integrity else 2)
if __name__=='__main__':main()
