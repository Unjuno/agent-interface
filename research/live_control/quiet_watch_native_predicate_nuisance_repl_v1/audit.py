#!/usr/bin/env python3
import argparse, hashlib, json, lzma, statistics
from pathlib import Path
TARGET=(50,50,220)

def sha(b): return hashlib.sha256(b).hexdigest()
def count_raw(raw):
    if len(raw)!=4096: raise ValueError(len(raw))
    return sum(raw[i]==50 and raw[i+1]==50 and raw[i+2]==220 for i in range(0,4096,4))
def integrity(r):
    kinds=[e['kind'] for e in r['events']]
    return (not r.get('thread_errors') and not r['owner'].get('error') and not r['watcher'].get('error') and r['owner'].get('verified_empty') and not r['right_down_final'] and kinds==['app_key_press','app_key_release'] and r['final']['match_count']==0 and not r['derived']['detected'] and len(r['observation_metrics'])==len(r['acquisitions']))
def recompute(records):
    by={}
    for r in records: by.setdefault(r['case']['pair_id'],{})[r['case']['count_backend']]=r
    rows=[]
    for pid in sorted(by):
        p,n=by[pid]['python_count'],by[pid]['native_count']
        def met(r):
            ms=r['observation_metrics']; gaps=[(ms[i+1]['start_ns']-ms[i]['count_end_ns'])/1e6 for i in range(len(ms)-1)]
            return {'cpu_ms':sum(x['total_thread_cpu_ns'] for x in ms)/1e6,'wall_ms':sum(x['count_end_ns']-x['start_ns'] for x in ms)/1e6,'max_gap_ms':max(gaps),'samples':len(ms)}
        pm,nm=met(p),met(n); rows.append({'pair_id':pid,'python':pm,'native':nm,'cpu_ratio':nm['cpu_ms']/pm['cpu_ms'],'wall_ratio':nm['wall_ms']/pm['wall_ms'],'max_gap_ratio':nm['max_gap_ms']/pm['max_gap_ms']})
    cpu=[x['cpu_ratio'] for x in rows]; wall=[x['wall_ratio'] for x in rows]; gap=[x['max_gap_ratio'] for x in rows]; stable=sum(x<=1.10 for x in gap); safe=all(integrity(r) for r in records)
    decision='REPLICATE_STABLE_SCOPED' if safe and statistics.median(cpu)<=.80 and statistics.median(wall)<=.90 and statistics.median(gap)<=1.10 and stable>=8 else ('FAIL_SAFETY_OR_SEMANTICS' if not safe else 'HOLD_GAP_STABILITY')
    return {'pairs':rows,'median_cpu_ratio':statistics.median(cpu),'median_wall_ratio':statistics.median(wall),'median_max_gap_ratio':statistics.median(gap),'pairs_gap_ratio_le_1_10':stable,'pair_count':len(rows),'safety_integrity_all':safe,'decision':decision}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--raw',required=True); ap.add_argument('--xz',required=True); ap.add_argument('--prereg',required=True); ap.add_argument('--root',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    rawp=Path(a.raw); xp=Path(a.xz); pp=Path(a.prereg); root=Path(a.root); rawb=rawp.read_bytes(); data=json.loads(rawb); pre=json.loads(pp.read_text())
    checks={}
    checks['xz_roundtrip']=lzma.decompress(xp.read_bytes())==rawb
    checks['record_count']=len(data['records'])==24
    checks['schedule']=data['schedule']==pre['schedule']==[r['case'] for r in data['records']]
    checks['sources']=data['sources']==pre['sources']
    checks['binaries']=data['binaries']==pre['binaries']
    checks['all_integrity']=all(integrity(r) for r in data['records'])
    pixel_n=0; pixel_ok=True; timestamp_ok=True
    for r in data['records']:
        for ac in r['acquisitions']+[r['final']]:
            b64=r['pixel_payloads'][ac['digest']]
            import base64
            b=base64.b64decode(b64); pixel_n+=1
            pixel_ok &= sha(b)==ac['digest'] and count_raw(b)==ac['match_count']
        for ac,m in zip(r['acquisitions'],r['observation_metrics']):
            timestamp_ok &= ac['start_ns']==m['start_ns'] and ac['end_ns']==m['acquire_end_ns'] and m['start_ns']<=m['acquire_end_ns']<=m['count_start_ns']<=m['count_end_ns']
    checks['pixels_reclassified']=bool(pixel_ok); checks['timestamp_chain']=bool(timestamp_ok)
    recomputed=recompute(data['records']); checks['summary_exact']=recomputed==data['summary']
    checks['frozen_source_files']=all(hashlib.sha256((root/k).read_bytes()).hexdigest()==v for k,v in pre['sources'].items() if k!='upstream')
    result={'schema':'quiet_watch_native_predicate_nuisance_repl_v1_audit','checks':checks,'pixel_frames_checked':pixel_n,'raw_sha256':sha(rawb),'xz_sha256':sha(xp.read_bytes()),'prereg_sha256':sha(pp.read_bytes()),'recomputed':recomputed,'formal_pass':all(checks.values())}
    Path(a.out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if result['formal_pass'] else 2)
if __name__=='__main__': main()
