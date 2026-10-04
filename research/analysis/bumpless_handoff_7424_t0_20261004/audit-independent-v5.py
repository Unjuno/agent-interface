import argparse,json,math
p=argparse.ArgumentParser();p.add_argument('--raw',required=True);a=p.parse_args();d=json.load(open(a.raw,encoding='utf-8'))
def clamp(x,lo,hi): return min(hi,max(lo,x))
def oracle(y,applied,ref,kp,rate,conditioned):
 z=(applied-kp*(ref-y)) if conditioned else 0.0
 raw=kp*(ref-y)+z; command=clamp(raw,0.0,1.0); u=clamp(command,applied-rate,applied+rate); first=u
 peak=abs(ref-y); maximum=y
 for _ in range(20):
  y=y+0.25*(u-y); peak=max(peak,abs(ref-y));maximum=max(maximum,y)
  command=clamp(kp*(ref-y)+z,0.0,1.0);u=clamp(command,u-rate,u+rate)
 return {'first_applied':round(first,12),'first_raw':round(raw,12),'first_command':round(command if False else clamp(raw,0.0,1.0),12),'discontinuity':round(abs(first-applied),12),'peak_abs_tracking_error':round(peak,12),'peak_state':round(maximum,12)}
def same(a,b): return all(math.isclose(float(a[k]),float(b[k]),rel_tol=0,abs_tol=1e-12) for k in b)
checks={}; episodes={x['case']:x for x in d['episodes']};checks['three_cases']=len(episodes)==3
for name,x in episodes.items():
 i=x['input']; by={r['route']:r for r in x['routes']}
 checks[name+'_has_both_routes']=set(by)=={'cold','conditioned'}
 for route,flag in [('cold',False),('conditioned',True)]:
  checks[name+'_'+route+'_matches_independent_oracle']=same(by[route],oracle(i['y'],i['applied_u'],i['ref'],i['kp'],i['rate_limit_per_tick'],flag))
 checks[name+'_all_routes_within_state_bounds']=all(-1e-12<=r['peak_state']<=1.0 for r in by.values())
 checks[name+'_conditioned_peak_not_worse']=by['conditioned']['peak_state']<=by['cold']['peak_state']
for n in ('stale-state','missing-state','revoked-lease'):
 g={x['case']:x for x in d['gates']}[n];checks[n+'_release_event']=g['owner_final']=='none' and 'source_released' in g['events'] and not g['receiver_actuations']
gates={x['case']:x for x in d['gates']};checks['pre_quiescence_keeps_source_owner']=gates['pre-quiescence']['owner_final']=='source' and not gates['pre-quiescence']['receiver_actuations']
mut={x['case']:x for x in d['mutation_controls']};checks['stale_mutation_is_counterexample']=mut['mutant-stale-state-accepted']['input']['state_fresh'] is False and bool(mut['mutant-stale-state-accepted']['receiver_actuations']);checks['early_mutation_is_counterexample']=mut['mutant-act-before-quiescence']['input']['source_quiesced'] is False and bool(mut['mutant-act-before-quiescence']['receiver_actuations'])
mreq=mut['mutant-condition-from-requested-input'];i=mreq['input'];z=i['requested_u']-2*(1.0-0.4);raw=2*(1.0-0.4)+z;cmd=clamp(raw,0,1);first=clamp(cmd,i['applied_u']-0.2,i['applied_u']+0.2);checks['requested_mutation_recomputed']=math.isclose(first,mreq['receiver_actuations'][0],abs_tol=1e-12) and math.isclose(abs(first-i['applied_u']),mreq['discontinuity'],abs_tol=1e-12)
result={'schema':'issue7424-bumpless-t0-independent-audit-v3','checks':checks,'passed':all(checks.values()),'classification':'METHOD_PASS_SCOPED' if all(checks.values()) else 'METHOD_FAIL_OR_HOLD','method':'separate saved-trace numerical oracle; candidate not rerun','scope':'scalar synthetic plant only'}
print(json.dumps(result,sort_keys=True,indent=2))



