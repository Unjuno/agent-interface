#!/usr/bin/env python3
from __future__ import annotations
import argparse, copy, json, pathlib, tempfile
from audit import audit

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('raw',nargs='+'); a=ap.parse_args()
    rows=[]
    for p in a.raw: rows += [json.loads(x) for x in pathlib.Path(p).read_text().splitlines()]
    muts=[]
    def add(name,fn):
        z=copy.deepcopy(rows); fn(z); muts.append((name,z))
    add('drop_row',lambda z:z.pop())
    add('duplicate_id',lambda z:z[1].__setitem__('case_id',z[0]['case_id']))
    add('source_x',lambda z:z[0]['source_records'][0].__setitem__('x',999.0))
    add('source_time',lambda z:z[0]['source_records'][1].__setitem__('source_ns',z[0]['source_records'][0]['source_ns']))
    add('decision',lambda z:z[0]['decision'].__setitem__('decision','LEFT'))
    add('admission',lambda z:z[2]['admission'].__setitem__('admitted',True))
    add('input_refusal',lambda z:z[2]['input_events'].append({'kind':'press','key':'Right'}))
    add('effect',lambda z:z[0]['app_snapshot'].__setitem__('effect',0))
    add('journal_key',lambda z:z[0]['app_snapshot']['journal'][0].__setitem__('key','Left'))
    add('keymap',lambda z:z[0]['keymap_after'].__setitem__('right',True))
    add('cleanup',lambda z:z[0]['cleanup'].__setitem__('app_exit',9))
    add('window',lambda z:z[0].__setitem__('window_id',z[0]['window_id']+1))
    out=[]
    with tempfile.TemporaryDirectory() as td:
        for name,z in muts:
            p=pathlib.Path(td)/(name+'.jsonl'); p.write_text('\n'.join(json.dumps(x,separators=(',',':'),sort_keys=True) for x in z)+'\n')
            r=audit([str(p)],'formal'); out.append({'name':name,'rejected':bool(r['errors'])})
    ok=all(x['rejected'] for x in out)
    print(json.dumps({'controls':out,'rejected':sum(x['rejected'] for x in out),'total':len(out),'pass':ok},sort_keys=True))
    return 0 if ok else 1
if __name__=='__main__': raise SystemExit(main())
