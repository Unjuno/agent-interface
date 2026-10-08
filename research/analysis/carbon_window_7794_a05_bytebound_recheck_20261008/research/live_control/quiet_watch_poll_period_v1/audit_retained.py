#!/usr/bin/env python3
import argparse, hashlib, json, statistics
from pathlib import Path

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('evidence'); ap.add_argument('prereg'); ap.add_argument('source'); a=ap.parse_args()
 e=json.load(open(a.evidence)); p=json.load(open(a.prereg)); C=e['columns']; cs=[dict(zip(C,r)) for r in e['rows']]; checks=[]
 def ck(n,x): checks.append([n,bool(x)])
 ck('schema',e['schema']=='quiet_watch_poll_period_v1_retained_derived'); ck('source_hash',sha(a.source)==e['source_sha256']==p['source_sha256']); ck('prereg_hash',sha(a.prereg)==e['prereg_sha256']); ck('case_count',len(cs)==p['measured_cases']==38)
 ck('schedule_identity',[{'case_id':c['id'],'kind':c['kind'],'period_ms':c['period_ms'],'offset_ms':c['offset_ms'],'order':c['order']} for c in cs]==p['schedule'])
 ck('integrity',all(c['verified_empty']==1 and c['right_down_final']==0 and c['press_count']==1 and c['release_count']==1 and c['final_match_count']<512 for c in cs))
 arms={}
 for per in (10,2):
  tar=[c for c in cs if c['period_ms']==per and c['kind']=='target']; nui=[c for c in cs if c['period_ms']==per and c['kind']=='nuisance']
  arms[str(per)]={'det':sum(c['detected'] for c in tar),'tar_n':len(tar),'false':sum(c['detected'] for c in nui),'nui_n':len(nui),'cost_med':statistics.median(c['acq_wall_ms'] for c in nui)}
 ck('expected_counts',arms['10']['tar_n']==15 and arms['2']['tar_n']==15 and arms['10']['nui_n']==4 and arms['2']['nui_n']==4); ck('no_nuisance_false',arms['10']['false']==arms['2']['false']==0)
 misses=[c for c in cs if c['period_ms']==10 and c['kind']=='target' and not c['detected']]; ck('miss_gaps_retained',len(misses)==6 and all(c['miss_containing_gap_ms'] is not None and c['miss_containing_gap_ms']>=c['cue_duration_ms'] for c in misses))
 ratio=arms['2']['cost_med']/arms['10']['cost_med']; decision='PROMOTE_2MS_SCOPED' if all(x for _,x in checks) and arms['2']['det']>arms['10']['det'] and ratio<=5 else 'HOLD_OR_FAIL'
 out={'pass':all(x for _,x in checks),'checks':checks,'arms':arms,'cost_ratio':ratio,'decision':decision,'raw_sha256':e['raw_sha256']}; print(json.dumps(out,indent=2,sort_keys=True)); raise SystemExit(0 if out['pass'] else 1)
if __name__=='__main__': main()
