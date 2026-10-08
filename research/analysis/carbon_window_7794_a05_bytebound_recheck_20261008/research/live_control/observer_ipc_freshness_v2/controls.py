#!/usr/bin/env python3
from __future__ import annotations
import argparse,copy,json,pathlib,tempfile,subprocess,sys

def main():
    ap=argparse.ArgumentParser();ap.add_argument('raw');ap.add_argument('freeze');args=ap.parse_args(); base=json.loads(pathlib.Path(args.raw).read_text())
    muts=[]
    def add(name,fn):
        x=copy.deepcopy(base); fn(x); muts.append((name,x))
    add('missing_case',lambda x:x['cases'].pop())
    add('duplicate_case',lambda x:x['cases'].__setitem__(1,copy.deepcopy(x['cases'][0])))
    add('boolean_block',lambda x:x['cases'][0].__setitem__('block',False))
    add('bad_arm',lambda x:x['cases'][0].__setitem__('arm','PROCESS_BOGUS'))
    add('affinity',lambda x:x['cases'][0]['consumer'].__setitem__('affinity',[4]))
    add('fixture_exit',lambda x:x['cases'][0].__setitem__('fixture_exit',7))
    add('pulse_exposure',lambda x:x['cases'][0]['fixture'].__setitem__('clear_request_ns',x['cases'][0]['fixture']['draw_complete_ns']+20_000_000))
    add('final_pixels',lambda x:x['cases'][0]['final'].__setitem__('target_pixels',1))
    add('boolean_seq',lambda x:x['cases'][0]['records'][0].__setitem__('seq',False))
    add('timestamp_order',lambda x:x['cases'][0]['records'][0].__setitem__('received_ns',0))
    add('roi_payload',lambda x:x['cases'][0]['records'][0].__setitem__('roi_zlib_b64','eJwDAAAAAAE='))
    results=[]
    with tempfile.TemporaryDirectory() as td:
        for name,row in muts:
            p=pathlib.Path(td)/(name+'.json');p.write_text(json.dumps(row,sort_keys=True,separators=(',',':')))
            cp=subprocess.run([sys.executable,'-B',str(pathlib.Path(__file__).with_name('audit.py')),str(p),args.freeze],capture_output=True,text=True)
            results.append({'name':name,'rejected':cp.returncode!=0,'exit':cp.returncode,'stdout':cp.stdout[-1200:],'stderr':cp.stderr[-500:]})
    out={'controls':results,'rejected':sum(r['rejected'] for r in results),'total':len(results)};print(json.dumps(out,sort_keys=True,indent=2));raise SystemExit(0 if all(r['rejected'] for r in results) else 2)
if __name__=='__main__':main()
