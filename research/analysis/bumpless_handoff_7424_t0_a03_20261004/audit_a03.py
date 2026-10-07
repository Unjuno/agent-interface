import argparse,json,math,hashlib,os
KP=2.0;KI=0.1;A=0.25;RATE=0.2;N=20;R=1.0;LO=0.0;HI=1.0;ZLO=-1.0;ZHI=1.0
p=argparse.ArgumentParser();p.add_argument('--raw',required=True);p.add_argument('--freeze',required=True);p.add_argument('--source',required=True);a=p.parse_args();d=json.load(open(a.raw,encoding='utf-8'));freeze=json.load(open(a.freeze,encoding='utf-8'))
def sat(x,l,h):return min(h,max(l,x))
def oracle(y0,u0,seeded):
 e0=R-y0;z=u0-KP*e0 if seeded else 0.0;y=y0;u_prev=u0;states=[y];errors=[abs(R-y)];rows=[]
 for tick in range(N):
  err=R-y;raw=KP*err+z;cmd=sat(raw,LO,HI);u=sat(cmd,u_prev-RATE,u_prev+RATE)
  if (raw>=HI and err>0) or (raw<=LO and err<0):zn=z
  else:zn=sat(z+KI*err,ZLO,ZHI)
  yn=y+A*(u-y);rows.append({'tick':tick,'y':round(y,12),'error':round(err,12),'z_before':round(z,12),'raw':round(raw,12),'clamped_command':round(cmd,12),'previous_applied':round(u_prev,12),'applied':round(u,12),'jump':round(abs(u-(u0 if tick==0 else u_prev)),12),'z_after':round(zn,12),'y_after':round(yn,12)})
  y=yn;u_prev=u;z=zn;states.append(y);errors.append(abs(R-y))
 settle=None
 for i in range(len(errors)-2):
  if max(errors[i:i+3])<=0.05:settle=i;break
 return {'states':[round(x,12) for x in states],'abs_errors':[round(x,12) for x in errors],'commands':rows,'metrics':{'first_jump':rows[0]['jump'],'peak_abs_tracking_error':round(max(errors),12),'integrated_abs_error_21_samples':round(sum(errors),12),'max_state':round(max(states),12),'min_state':round(min(states),12),'overshoot':round(max(0,max(states)-R),12),'settle_tick_three_samples_le_0_05':settle}}
def close(x,y):return isinstance(x,(int,float)) and math.isclose(x,y,rel_tol=0,abs_tol=1e-11)
checks={};cases={c['case']:c for c in d['cases']};checks['three_cases']=set(cases)=={'no-disturbance','step-disturbance-at-switch','saturation-at-switch'}
for name,c in cases.items():
 inp=c['input'];rr={r['route']:r for r in c['routes']};checks[name+'_both_routes']=set(rr)=={'cold','conditioned'}
 for route,seeded in [('cold',False),('conditioned',True)]:
  expected=oracle(inp['y'],inp['applied_u'],seeded);actual=rr[route]
  for field in ('states','abs_errors','commands'):
   if field=='commands':
    ok=len(actual[field])==len(expected[field]) and all(all(close(g[k],e[k]) if isinstance(e[k],(int,float)) else g[k]==e[k] for k in e) for g,e in zip(actual[field],expected[field]))
   else:ok=len(actual[field])==len(expected[field]) and all(close(g,e) for g,e in zip(actual[field],expected[field]))
   checks[name+'_'+route+'_'+field+'_oracle']=ok
  checks[name+'_'+route+'_metrics_oracle']=all(actual['metrics'][k]==expected['metrics'][k] if expected['metrics'][k] is None else close(actual['metrics'][k],expected['metrics'][k]) for k in expected['metrics'])
 if name in ('no-disturbance','step-disturbance-at-switch'):
  cold=rr['cold']['metrics'];cond=rr['conditioned']['metrics'];checks[name+'_jump_margin']=cond['first_jump']<=cold['first_jump']*0.75 and cond['first_jump']<cold['first_jump'];checks[name+'_IAE_not_worse']=cond['integrated_abs_error_21_samples']<=cold['integrated_abs_error_21_samples']+1e-9
 checks[name+'_state_bound']=all(-1e-12<=r['metrics']['min_state'] and r['metrics']['max_state']<=1+1e-12 for r in rr.values())
g={x['case']:x for x in d['gates']}
for n in ('stale-state','missing-state','revoked-lease'):checks[n+'_denied_and_released']=not g[n]['receiver_actuations'] and g[n]['owner_final']=='none' and 'source_released' in g[n]['events']
checks['pre_quiescence_denied']=not g['pre-quiescence']['receiver_actuations'] and g['pre-quiescence']['owner_final']=='source'
checks['delay_event_order']=g['delayed-handoff']['events'].index('source_quiesced_after_delay')<g['delayed-handoff']['events'].index('transfer_accepted')<g['delayed-handoff']['events'].index('receiver_actuation');checks['delay_one_actuation']=len(g['delayed-handoff']['receiver_actuations'])==1
m={x['case']:x for x in d['mutation_controls']};checks['stale_mutation_observable']=not m['stale-state-accepted']['input']['state_fresh'] and bool(m['stale-state-accepted']['receiver_actuations']);checks['early_mutation_observable']=not m['receiver-before-quiescence']['input']['source_quiesced'] and bool(m['receiver-before-quiescence']['receiver_actuations']);checks['requested_state_mutation_observable']=m['seed-from-requested-not-applied']['first_jump']>0 and m['seed-from-requested-not-applied']['receiver_actuations'][0]!=m['seed-from-requested-not-applied']['input']['applied_u']
source_hashes={}
for item in freeze['source_sha256']:
 path=os.path.join(a.source,item['path']);source_hashes[item['path']]=hashlib.sha256(open(path,'rb').read()).hexdigest();checks['hash_'+item['path']]=source_hashes[item['path']]==item['sha256']
primary=all(v for k,v in checks.items() if not k.endswith('_IAE_not_worse'));utility=all(v for k,v in checks.items() if k.endswith('_IAE_not_worse'));result={'schema':'issue7424-bumpless-t0-a03-audit-v1','checks':checks,'passed':all(checks.values()),'classification':'METHOD_PASS_SCOPED' if all(checks.values()) else ('CONTINUITY_PASS_TRACKING_TRADEOFF' if primary and not utility else 'METHOD_FAIL_OR_HOLD'),'continuity_and_safety_gates_pass':primary,'IAE_gates_pass':utility,'scope':'synthetic scalar PI route; no runtime behavior'}
print(json.dumps(result,sort_keys=True,indent=2))
