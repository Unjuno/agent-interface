import json, argparse, math
p=argparse.ArgumentParser(); p.add_argument('--raw',required=True); a=p.parse_args(); d=json.load(open(a.raw,encoding='utf-8'))
checks={}
checks['schema']=d.get('schema')=='issue7424-bumpless-t0-raw-v1'
by={x['case']:x for x in d['episodes']}
checks['eligible_cases_present']=set(by)=={'no-disturbance','step-disturbance-at-switch','saturation-at-switch'}
for n in ('no-disturbance','step-disturbance-at-switch'):
 x=by[n]; cold,cond=x['routes']; checks[n+'_continuity_margin']=cond['discontinuity'] <= cold['discontinuity']*0.75 and cond['discontinuity'] < cold['discontinuity']
 checks[n+'_conditioned_output_matches_applied']=cond['first_applied']==x['input']['applied_u']
sat=by['saturation-at-switch']; checks['saturation_no_safety_regression']=max(r['peak_state'] for r in sat['routes']) <= 1.0 and all(r['discontinuity']==0 for r in sat['routes'])
g={x['case']:x for x in d['gates']}
for n in ('stale-state','missing-state','revoked-lease','pre-quiescence'):
 x=g[n]; checks[n+'_no_actuation']=x['receiver_actuations']==[]
checks['delayed_handoff_waits_for_ack']=g['delayed-handoff']['events'].index('source_quiesced_after_delay') < g['delayed-handoff']['events'].index('transfer_accepted') < g['delayed-handoff']['events'].index('receiver_actuation')
checks['delayed_handoff_one_actuation']=len(g['delayed-handoff']['receiver_actuations'])==1
m={x['case']:x for x in d['mutation_controls']}
checks['stale_mutation_detected']=not m['mutant-stale-state-accepted']['input']['state_fresh'] and m['mutant-stale-state-accepted']['receiver_actuations']!=[]
checks['early_actuation_mutation_detected']=not m['mutant-act-before-quiescence']['input']['source_quiesced'] and m['mutant-act-before-quiescence']['receiver_actuations']!=[]
checks['requested_vs_applied_mutation_detected']=m['mutant-condition-from-requested-input']['discontinuity']>0
result={'schema':'issue7424-bumpless-t0-audit-v1','checks':checks,'passed':all(checks.values()),'classification':'METHOD_PASS_SCOPED' if all(checks.values()) else 'METHOD_FAIL_OR_HOLD','scope':'synthetic finite simulator only'}
print(json.dumps(result,sort_keys=True,indent=2))


