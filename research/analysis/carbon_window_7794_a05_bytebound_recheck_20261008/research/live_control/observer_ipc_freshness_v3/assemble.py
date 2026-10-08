#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,pathlib,time
ROOT=pathlib.Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);args=ap.parse_args();out=pathlib.Path(args.out)
    freeze=json.loads((ROOT/'FREEZE.json').read_text());rows=[];batches=[]
    for i in range(10):
        bd=out/f'batch-{i:02d}'; ex=bd/'OUTER_EXIT'; end=bd/'END.json'; cases=bd/'CASES.json'
        if not(ex.exists() and ex.read_text().strip()=='0' and end.exists() and cases.exists()):raise SystemExit(f'incomplete batch {i}')
        e=json.loads(end.read_text());c=json.loads(cases.read_text())
        if e.get('batch')!=i or e.get('cases')!=4 or len(c.get('cases',[]))!=4:raise SystemExit(f'bad batch {i}')
        rows.extend(c['cases']);batches.append({'batch':i,'outer_exit':0,'end':e,'cases_sha256':sha(cases),'end_sha256':sha(end)})
    raw={'schema':'observer-ipc-freshness-v3','allocation':freeze['allocation'],'freeze_sha256':sha(ROOT/'FREEZE.json'),'cases':rows,'batches':batches,'completed_ns':time.monotonic_ns()}
    (out/'RAW.json').write_text(json.dumps(raw,sort_keys=True,separators=(',',':')),encoding='utf-8')
    (out/'END.json').write_text(json.dumps({'allocation':freeze['allocation'],'cases':len(rows),'batches':len(batches),'raw_sha256':sha(out/'RAW.json')},sort_keys=True,indent=2)+'\n')
    print(json.dumps({'cases':len(rows),'batches':len(batches),'raw_sha256':sha(out/'RAW.json')},sort_keys=True))
if __name__=='__main__':main()
