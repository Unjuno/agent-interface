import argparse,hashlib,json
from pathlib import Path
GRID=tuple(range(0,1001,25)); A=tuple(range(250,826,25)); W=(225,325,425,500,600,700,800,900,925,950,975)
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def event(s,a):return any(a-100<=t<a for t in s) and any(a<t<=a+100 for t in s)
def rev(s,a):return any(a-150<=t<=a-25 for t in s) and any(a+25<=t<=a+150 for t in s)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--freeze',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();r=json.loads(Path(a.result).read_text());f=json.loads(Path(a.freeze).read_text());o=Path(a.output);assert not o.exists()
 regions=[set(range(900,1001,25)),set(range(150,276,25)),set(range(300,376,25)),set(range(400,476,25)),set(range(500,576,25)),set(range(600,676,25)),set(range(700,776,25)),set(range(800,876,25))]
 disjoint=all(not regions[i]&regions[j] for i in range(len(regions)) for j in range(i+1,len(regions)))
 valid=(len(W)==11 and sum(900<=t<=1000 for t in W)>=4 and any(t<=300 for t in W) and all(event(W,x) for x in A) and all(rev(W,x) for x in A))
 checks={'decision':r['decision']=='PASS_TEMPORAL_FIXED_SCHEDULE_MIN_BUDGET_11_SCOPED','lower':r['lower_bound']==11==4+7,'disjoint':disjoint and r['certificate_pairwise_disjoint'],'witness':valid and r['witness']==list(W),'anchors':r['event_anchors_passed']==24 and r['reversal_anchors_passed']==24,'corruptions':all(r['corruption_controls'].values()),'formal':r['formal_invocations']==1 and r['reruns']==0,'source_prove':h('prove.py')==f['sha256']['prove.py'],'source_audit':h('audit.py')==f['sha256']['audit.py'],'source_plan':h('PLAN.md')==f['sha256']['PLAN.md']}
 z={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'result_sha256':h(a.result),'freeze_sha256':h(a.freeze)};o.write_text(json.dumps(z,indent=2,sort_keys=True)+'\n');print(json.dumps(z,indent=2,sort_keys=True));raise SystemExit(0 if z['status']=='PASS' else 1)
if __name__=='__main__':main()
