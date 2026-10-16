#!/usr/bin/env python3
import argparse, base64, hashlib, json, math, statistics
from pathlib import Path
PERIOD_NS=2_000_000; PAIRS=6; N=32; INTERVALS={'gil5ms':0.005,'gil1ms':0.001}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def count_pixels(raw):return sum(raw[j:j+3]==b'\x32\x32\xdc' for j in range(0,4096,4))
def expected_schedule():
    counts=(0,511,512,513,1023,1024);out=[]
    for i in range(PAIRS):
        order=('gil5ms','gil1ms') if i%2==0 else ('gil1ms','gil5ms')
        for arm in order:out.append({'pair':i,'arm':arm,'count':counts[i],'order':len(out)})
    return out

def validate(raw,plan,root):
    checks={}
    checks['identity']=raw['task']==plan['task'] and raw['base']==plan['base'] and raw['mode']=='formal'
    checks['sources']=raw['sources']==plan['sources'] and all(sha(root/k)==v for k,v in plan['sources'].items())
    checks['binary']=raw['binary_sha256']==plan['binary_sha256']==sha(root/'native.so')
    checks['schedule']=[r['case'] for r in raw['records']]==plan['schedule']==expected_schedule() and len(raw['records'])==12
    checks['errors']=raw['errors']==[] and raw.get('server',{}).get('reaped') is True
    good_rows=True;good_pixels=True;good_load=True;good_row_hash=True;case_s=[]
    for rec in raw['records']:
        arm=rec['case']['arm']; target=INTERVALS[arm]
        if abs(rec['switch_interval']-target)>1e-9 or rec['observer_affinity']!=[plan['cpus']['observer']]: good_load=False
        ld=rec['load'];
        if not(ld.get('cleaned') and ld['before']['alive'] and ld['after']['alive'] and ld['before']['affinity']==[plan['cpus']['competitor']] and ld['after']['affinity']==[plan['cpus']['competitor']] and ld['after']['ticks']>ld['before']['ticks']):good_load=False
        if len(rec['rows'])!=N:good_rows=False
        expected_row_hash=hashlib.sha256(json.dumps(rec['rows'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
        if rec.get('rows_sha256')!=expected_row_hash:good_row_hash=False
        prev_due=None;posts=[];xs=[];totals=[]
        for row in rec['rows']:
            ts=[row[k] for k in ('python_before_ns','c_enter_ns','x_before_ns','x_after_ns','c_exit_ns','python_return_ns','bytes_ready_ns')]
            if ts!=sorted(ts):good_rows=False
            due=row['due_ns'];
            if prev_due is not None and (due-prev_due<PERIOD_NS or (due-prev_due)%PERIOD_NS):good_rows=False
            prev_due=due
            dg=row['pixel_digest']; enc=rec['pixels'].get(dg)
            if enc is None:good_pixels=False;continue
            b=base64.b64decode(enc)
            if hashlib.sha256(b).hexdigest()!=dg or len(b)!=4096 or count_pixels(b)!=rec['case']['count']:good_pixels=False
            posts.append(row['python_return_ns']-row['c_exit_ns']);xs.append(row['x_after_ns']-row['x_before_ns']);totals.append(row['bytes_ready_ns']-row['python_before_ns'])
        case_s.append({'pair':rec['case']['pair'],'arm':arm,'post_native_median_ns':statistics.median(posts),'x_internal_median_ns':statistics.median(xs),'total_median_ns':statistics.median(totals)})
    checks['rows']=good_rows;checks['row_hash']=good_row_hash;checks['pixels']=good_pixels;checks['load']=good_load
    pairs=[];passed=0
    for i in range(PAIRS):
        b=next(x for x in case_s if x['pair']==i and x['arm']=='gil5ms');c=next(x for x in case_s if x['pair']==i and x['arm']=='gil1ms');ratio=c['post_native_median_ns']/max(b['post_native_median_ns'],1);ok=c['post_native_median_ns']<=2_000_000 and ratio<=.40;passed+=ok;pairs.append({'pair':i,'baseline_post_native_median_ns':b['post_native_median_ns'],'candidate_post_native_median_ns':c['post_native_median_ns'],'ratio':ratio,'passes_pair_gate':bool(ok)})
    decision='GIL_INTERVAL_TRACKING_SCOPED' if passed>=4 else 'HOLD_GIL_INTERVAL_ATTRIBUTION'
    derived={'case_summaries':case_s,'pairs':pairs,'pairs_passing':passed,'decision':decision}
    checks['summary']=raw.get('summary')==derived
    return {'pass':all(checks.values()),'checks':checks,'derived':derived}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('raw');ap.add_argument('prereg');ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);a=ap.parse_args();root=Path(a.root);res=validate(json.loads(Path(a.raw).read_text()),json.loads(Path(a.prereg).read_text()),root);Path(a.out).write_text(json.dumps(res,indent=2,sort_keys=True)+'\n');print(json.dumps(res,indent=2,sort_keys=True));raise SystemExit(0 if res['pass'] else 2)
if __name__=='__main__':main()
