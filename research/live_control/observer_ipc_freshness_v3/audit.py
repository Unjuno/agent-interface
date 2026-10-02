#!/usr/bin/env python3
from __future__ import annotations
import argparse,base64,hashlib,json,pathlib,zlib
TARGET=1024
ARMS=("INLINE_IDLE","INLINE_THREAD","PROCESS_IDLE","PROCESS_THREAD")

def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def count_target(s):
    raw=zlib.decompress(base64.b64decode(s))
    if len(raw)!=4096: raise ValueError('roi length')
    return sum(1 for i in range(0,4096,4) if (int.from_bytes(raw[i:i+4],'little')&0xffffff)==0xdc3232)

def audit(raw_path,freeze_path):
    raw=json.loads(pathlib.Path(raw_path).read_text()); freeze=json.loads(pathlib.Path(freeze_path).read_text()); errors=[]; checks=0
    def ck(cond,msg):
        nonlocal checks; checks+=1
        if not cond: errors.append(msg)
    ck(raw.get('allocation')==freeze.get('allocation'),'allocation')
    batches=raw.get('batches'); ck(isinstance(batches,list) and len(batches)==10,'batch denominator')
    if isinstance(batches,list):
        for i,b in enumerate(batches):
            ck(b.get('batch')==i,'batch index '+str(i)); ck(b.get('outer_exit')==0,'batch exit '+str(i)); ck(b.get('end',{}).get('cases')==4,'batch cases '+str(i)); ck(b.get('end',{}).get('xvfb',{}).get('socket_absent') is True,'batch socket cleanup '+str(i))
    ck(raw.get('freeze_sha256')==sha(freeze_path),'freeze hash')
    cases=raw.get('cases'); ck(isinstance(cases,list),'cases list')
    expected=freeze['plan']['cases']; ck(len(cases)==40,'case denominator')
    ids=[c.get('case') for c in cases]; ck(ids==[c['case'] for c in expected],'case order'); ck(len(ids)==len(set(ids)),'case unique')
    byarm={a:[] for a in ARMS}
    for i,(c,e) in enumerate(zip(cases,expected)):
        prefix=f"case{i}:{c.get('case')}"
        for k in ('case','block','arm','offset_ms'): ck(c.get(k)==e.get(k),prefix+':'+k)
        ck(c.get('arm') in ARMS,prefix+':arm')
        ck(c.get('consumer',{}).get('affinity')==[0],prefix+':consumer affinity')
        if c['arm'].endswith('THREAD'):
            load=c.get('load') or {}; ck(load.get('affinity')==[1],prefix+':load affinity'); ck(type(load.get('cpu_start_ns')) is int and type(load.get('cpu_end_ns')) is int and load['cpu_end_ns']>load['cpu_start_ns'],prefix+':load cpu')
        else: ck(c.get('load') is None,prefix+':idle load')
        f=c.get('fixture',{}); ck(c.get('fixture_exit')==0,prefix+':fixture exit'); ck(f.get('draw_rc')==0 and f.get('clear_rc')==0,prefix+':paint rc')
        exposure=f.get('clear_request_ns',0)-f.get('draw_complete_ns',0); ck(4_000_000<=exposure<=8_000_000,prefix+':pulse exposure')
        ck(c.get('final',{}).get('target_pixels')==0,prefix+':final clear')
        if c['arm'].startswith('PROCESS'): ck(c.get('observer_exit')==0,prefix+':observer exit')
        else: ck(c.get('observer_exit') is None,prefix+':inline observer')
        recs=c.get('records'); ck(isinstance(recs,list) and len(recs)>0,prefix+':records')
        target=0; ageq=0
        prevseq=-1
        for j,r in enumerate(recs):
            rp=f'{prefix}:r{j}'
            ck(type(r.get('seq')) is int and r['seq']>prevseq,rp+':seq'); prevseq=r.get('seq',prevseq)
            ck(r.get('case')==c.get('case'),rp+':case')
            cs=r.get('c_ns'); ck(isinstance(cs,list) and len(cs)==6 and all(type(x) is int for x in cs),rp+':c')
            if isinstance(cs,list) and len(cs)==6: ck(r['py_before_ns']<=cs[0]<=cs[1]<=cs[2]<=cs[3]<=r['py_return_ns']<=r['received_ns'],rp+':time order')
            try: pix=count_target(r['roi_zlib_b64']); ck(pix==r.get('target_pixels'),rp+':pixels')
            except Exception: errors.append(rp+':roi'); pix=-1
            if pix==TARGET:
                target+=1
                if r['received_ns']-cs[1]<=5_000_000: ageq+=1
        ck(target==c.get('capture_count'),prefix+':capture count'); ck(ageq==c.get('age_qualified_count'),prefix+':ageq')
        byarm[c['arm']].append((target>0,ageq>0))
    for arm in ARMS: ck(len(byarm[arm])==10,'arm denominator '+arm)
    process_thread=sum(1 for hit,_ in byarm['PROCESS_THREAD'] if hit); inline_thread=sum(1 for hit,_ in byarm['INLINE_THREAD'] if hit); process_age=sum(1 for _,a in byarm['PROCESS_THREAD'] if a)
    integrity=not errors
    decision='PASS_CAPTURE_AND_DELIVERY_SCOPED' if integrity and process_thread>=9 and process_thread-inline_thread>=3 and process_age>=9 else ('HOLD_CAPTURE_DELIVERY_GAIN' if integrity else 'FAIL_INTEGRITY')
    return {"decision":decision,"errors":errors,"checks":checks,"counts":{"PROCESS_THREAD_capture_cases":process_thread,"INLINE_THREAD_capture_cases":inline_thread,"PROCESS_THREAD_age_qualified_cases":process_age,"by_arm":{a:{"capture_cases":sum(h for h,_ in v),"age_qualified_cases":sum(q for _,q in v)} for a,v in byarm.items()}}}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('raw');ap.add_argument('freeze');args=ap.parse_args(); out=audit(args.raw,args.freeze); print(json.dumps(out,sort_keys=True,indent=2)); raise SystemExit(0 if not out['errors'] else 2)
if __name__=='__main__':main()
