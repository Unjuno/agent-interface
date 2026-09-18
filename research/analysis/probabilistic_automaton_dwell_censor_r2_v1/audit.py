from fractions import Fraction as F
from collections import defaultdict
import argparse,hashlib,json,math
from pathlib import Path
T=4;M=8;N=8
def comps(total,k,p=()):
 if k==1:yield p+(total,);return
 for x in range(total+1):yield from comps(total-x,k-1,p+(x,))
def rec():
 g=defaultdict(list);s={'N':N,'distributions':0,'observable_groups':0,'group_range_mismatch':0,'endpoint_sharpness_failures':0,'ambiguous_mean_groups':0,'completion_mean_defined_rows':0,'completion_mean_not_full_rows':0,'completion_underestimate_sign_mismatch':0,'censor_at_horizon_underestimate_rows':0,'censor_at_horizon_sign_mismatch':0,'all_censored_rows':0}
 for c in comps(N,8):
  s['distributions']+=1;obs=c[:4]+(sum(c[4:]),);mean=F(sum((i+1)*n for i,n in enumerate(c)),N);g[obs].append(mean);co=sum(c[:4]);z=sum(c[4:])
  if co==0:s['all_censored_rows']+=1
  if co>0 and z>0:
   cm=F(sum((i+1)*c[i] for i in range(4)),co);s['completion_mean_defined_rows']+=1;s['completion_mean_not_full_rows']+=int(cm!=mean);s['completion_underestimate_sign_mismatch']+=int(not(cm<mean))
  if z>0:
   base=F(sum((i+1)*c[i] for i in range(4)),N);imp=base+F(z,N)*T;s['censor_at_horizon_underestimate_rows']+=int(imp!=mean);s['censor_at_horizon_sign_mismatch']+=int(not(imp<mean))
 s['observable_groups']=len(g)
 for obs,ms in g.items():
  z=obs[4];base=F(sum((i+1)*obs[i] for i in range(4)),N);L=base+F(z,N)*(T+1);U=base+F(z,N)*M;s['group_range_mismatch']+=int((L,U)!=(min(ms),max(ms)));s['endpoint_sharpness_failures']+=int(L not in ms or U not in ms);s['ambiguous_mean_groups']+=int(len(set(ms))>1)
 return s
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--freeze',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();o=Path(a.output);assert not o.exists();R=json.loads(Path(a.result).read_text());Z=json.loads(Path(a.freeze).read_text());S=rec();rs=R['stats'];checks={'decision':R['decision']=='PASS_PROBABILISTIC_AUTOMATON_DWELL_CENSOR_SCOPED','stats':rs==S,'count':rs['distributions']==6435==math.comb(15,7),'range':rs['group_range_mismatch']==0,'sharp':rs['endpoint_sharpness_failures']==0,'ambiguous':rs['ambiguous_mean_groups']>0,'completion':rs['completion_mean_not_full_rows']>0 and rs['completion_underestimate_sign_mismatch']==0,'horizon':rs['censor_at_horizon_underestimate_rows']>0 and rs['censor_at_horizon_sign_mismatch']==0,'unbounded':R['unbounded_control']['strictly_increasing'],'directed':all(R['directed'].values()),'corruptions':all(R['corruptions'].values()),'formal':R['formal_invocations']==1 and R['reruns']==0 and R['replacements']==0 and R['tuning']==0,'source_plan':h('PLAN.md')==Z['sha256']['PLAN.md'],'source_formal':h('formal.py')==Z['sha256']['formal.py'],'source_audit':h('audit.py')==Z['sha256']['audit.py']};out={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'audit_stats':S,'result_sha256':h(a.result),'freeze_sha256':h(a.freeze)};o.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True));raise SystemExit(0 if out['status']=='PASS' else 1)
if __name__=='__main__':main()
