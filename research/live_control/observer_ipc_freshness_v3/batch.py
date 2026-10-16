#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, time
import study
ROOT=pathlib.Path(__file__).resolve().parent

def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def put(path,obj):
    path=pathlib.Path(path); tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(obj,sort_keys=True,separators=(',',':')),encoding='utf-8'); tmp.replace(path)

def verify(freeze):
    for name,row in freeze['files'].items():
        p=ROOT/name
        if not p.exists() or sha(p)!=row['sha256']: raise SystemExit('source mismatch '+name)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--index',type=int,required=True);ap.add_argument('--out',required=True);args=ap.parse_args()
    if not 0<=args.index<10: raise SystemExit('index')
    freeze=json.loads((ROOT/'FREEZE.json').read_text());verify(freeze)
    out=pathlib.Path(args.out)
    if args.index==0: out.mkdir(parents=True,exist_ok=False)
    elif not out.is_dir(): raise SystemExit('missing allocation root')
    if args.index:
        prev=out/f'batch-{args.index-1:02d}'/'OUTER_EXIT'
        if not prev.exists() or prev.read_text().strip()!='0': raise SystemExit('previous external exit not retained zero')
    bd=out/f'batch-{args.index:02d}';bd.mkdir(exist_ok=False)
    (bd/'STARTED').write_text(str(time.monotonic_ns()),encoding='ascii')
    cases=[]; display=f':{250+args.index}'; xvfb,sock=study.start_xvfb(display)
    xstop=None
    try:
        lib=study.load_native();d=study.open_display(lib,display);study.set_aff(0);study.time.sleep(.01);lib.q_paint(d,0);lib.q_close(d)
        specs=freeze['plan']['cases'][args.index*4:(args.index+1)*4]
        for spec in specs:
            cases.append(study.run_case(spec,display))
            put(bd/'CASES.json',{'allocation':freeze['allocation'],'batch':args.index,'cases':cases})
    finally:
        xstop=study.stop_xvfb(xvfb,sock)
    end={'allocation':freeze['allocation'],'batch':args.index,'cases':len(cases),'xvfb':xstop,'completed_ns':time.monotonic_ns()}
    put(bd/'END.json',end)
    print(json.dumps(end,sort_keys=True,separators=(',',':')))
if __name__=='__main__':main()
