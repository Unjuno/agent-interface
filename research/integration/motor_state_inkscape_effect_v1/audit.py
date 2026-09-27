#!/usr/bin/env python3
import argparse,json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
CONDS=['STABLE_NAIVE','DISPLACED_NAIVE','DISPLACED_OBSERVED_GUARD','STABLE_OBSERVED_GUARD','OBSERVER_UNAVAILABLE_NAIVE','OBSERVER_UNAVAILABLE_GUARD']

def parse(raw):
    r=ET.fromstring(raw.encode()).find('{http://www.w3.org/2000/svg}rect'); return {k:r.attrib.get(k) for k in ('x','y','width','height','transform')}
def check_rows(rows,formal=True):
    errs=[]
    expected=len(CONDS)*(3 if formal else 1)
    if len(rows)!=expected: errs.append(f'row_count:{len(rows)}')
    seen=set()
    for r in rows:
        key=(r.get('rep'),r.get('condition'))
        if key in seen: errs.append('duplicate:'+repr(key))
        seen.add(key)
        if r.get('condition') not in CONDS or r.get('status')!='complete': errs.append('schema:'+repr(key));continue
        if r.get('authority')!='none': errs.append('authority:'+repr(key))
        for fld in ('before_svg_utf8','after_svg_utf8'):
            if hashlib.sha256(r[fld].encode()).hexdigest()!=r[fld.replace('_utf8','_sha256')]: errs.append('sha:'+fld+repr(key))
        bef=parse(r['before_svg_utf8']); aft=parse(r['after_svg_utf8'])
        if bef!=r['before_svg'] or aft!=r['after_svg']: errs.append('svg_parse:'+repr(key))
        effect=float(aft['x'])>50.5 and abs(float(aft['y'])-50)<.1 and abs(float(aft['width'])-40)<.1 and abs(float(aft['height'])-30)<.1
        if effect!=r.get('intended_effect'): errs.append('effect:'+repr(key))
        if not r.get('neutral'): errs.append('neutral:'+repr(key))
        c=r['condition']; disp=r['motor_disposition']; sent=r['input_dispatched']
        if c in ('STABLE_NAIVE','STABLE_OBSERVED_GUARD') and not (disp=='MATCH' and sent and effect): errs.append('stable:'+repr(key))
        if c=='DISPLACED_NAIVE' and not (disp=='MISMATCH' and sent and not effect): errs.append('displaced_naive:'+repr(key))
        if c=='DISPLACED_OBSERVED_GUARD' and not (disp=='MISMATCH' and not sent and not effect): errs.append('displaced_guard:'+repr(key))
        if c=='OBSERVER_UNAVAILABLE_NAIVE' and not (disp=='UNKNOWN' and sent and effect): errs.append('unknown_naive:'+repr(key))
        if c=='OBSERVER_UNAVAILABLE_GUARD' and not (disp=='UNKNOWN' and not sent and not effect): errs.append('unknown_guard:'+repr(key))
        if sent and not (r.get('held_observed') and r['held_observed'].get('button1')): errs.append('held_missing:'+repr(key))
        if (not sent) and r.get('held_observed') is not None: errs.append('refusal_input:'+repr(key))
        if not all(k in r.get('process_exits',{}) for k in ('inkscape','openbox','xvfb')): errs.append('process_receipt:'+repr(key))
    return errs

def load(paths):
    rows=[]
    for p in paths:
        rows += [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
    return rows

def main():
    ap=argparse.ArgumentParser();ap.add_argument('raw',nargs='+');ap.add_argument('--construction',action='store_true');ap.add_argument('--out',type=Path);args=ap.parse_args()
    rows=load(args.raw);errs=check_rows(rows,not args.construction);summary={'rows':len(rows),'errors':errs,'pass':not errs}
    if args.out: args.out.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,sort_keys=True));return 0 if not errs else 1
if __name__=='__main__':raise SystemExit(main())
