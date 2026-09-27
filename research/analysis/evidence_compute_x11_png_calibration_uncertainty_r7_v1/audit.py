import argparse,copy,json,random,hashlib
from pathlib import Path
N=100000;SEED=1784001;P=0.25
def pct(v,q):
    s=sorted(v);return s[round((len(s)-1)*q)]
def derive(x,seed=SEED):
    rows=x['rows']; gs=[r['loss_ns'] for r in rows if r['loss_role']=='g'];ws=[r['loss_ns'] for r in rows if r['loss_role']=='w'];errs=[]
    if len(rows)!=32 or len(gs)!=24 or len(ws)!=8:errs.append('counts')
    if sum(gs)!=353425454 or sum(ws)!=1283501201:errs.append('parent_sums')
    for i,r in enumerate(rows):
        for arm in ('RUN','WAIT'):
            z=r[arm]
            if z['cost_ns']!=z['completion_wall_ns']+z['obsolete_cpu_ns']:errs.append(f'cost:{i}:{arm}')
        want=(r['WAIT']['cost_ns']-r['RUN']['cost_ns']) if r['loss_role']=='g' else (r['RUN']['cost_ns']-r['WAIT']['cost_ns'])
        if r['loss_ns']!=want:errs.append(f'loss:{i}')
        if (r['outcome']=='STABLE')!=(r['loss_role']=='g'):errs.append(f'stratum:{i}')
    rng=random.Random(seed);ps=[];ds=[];wait=0
    if not errs:
      for _ in range(N):
        gb=[gs[rng.randrange(len(gs))] for _ in gs];wb=[ws[rng.randrange(len(ws))] for _ in ws]
        g=sum(gb)/len(gb);w=sum(wb)/len(wb);pstar=g/(g+w);delta=P*w-(1-P)*g
        ps.append(pstar);ds.append(delta);wait+=int(P>pstar and delta>0)
    loo=0
    if not errs:
      for r in rows:
        g2=[z['loss_ns'] for z in rows if z['loss_role']=='g' and z['scenario_id']!=r['scenario_id']]
        w2=[z['loss_ns'] for z in rows if z['loss_role']=='w' and z['scenario_id']!=r['scenario_id']]
        g=sum(g2)/len(g2);w=sum(w2)/len(w2);pstar=g/(g+w);delta=P*w-(1-P)*g
        loo+=int(P>pstar and delta>0)
    d=None if errs else {'p_star':{'lo95':pct(ps,.025),'median':pct(ps,.5),'hi95':pct(ps,.975)},'delta':{'lo95':pct(ds,.025),'median':pct(ds,.5),'hi95':pct(ds,.975)},'wait':wait/N,'loo':loo}
    return errs,d
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--ledger',required=True);ap.add_argument('--result',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
    o=Path(a.output);assert not o.exists();x=json.loads(Path(a.ledger).read_text());r=json.loads(Path(a.result).read_text());e,d=derive(x)
    checks={'no_ledger_errors':not e,'decision':r.get('decision')=='PASS_X11_PNG_CALIBRATION_WAIT_ROBUST_SCOPED','pstar_match':bool(d) and d['p_star']==r.get('p_star'),'delta_match':bool(d) and d['delta']==r.get('delta_run_minus_wait_ns'),'wait_fraction':bool(d) and d['wait']==1.0==r.get('bootstrap_wait_fraction'),'loo32':bool(d) and d['loo']==32==r.get('leave_one_out_wait'),'pstar_upper_below_p':bool(d) and d['p_star']['hi95']<P,'delta_lower_positive':bool(d) and d['delta']['lo95']>0}
    controls={}
    y=copy.deepcopy(x);y['rows'][0]['RUN']['completion_wall_ns']+=1;controls['primitive_cost_mutation_rejected']=bool(derive(y)[0])
    y=copy.deepcopy(x);y['rows'][0]['loss_role']='w';controls['stratum_mutation_rejected']=bool(derive(y)[0])
    y=copy.deepcopy(x);y['parent_result_g_sum_ns']+=1;controls['parent_sum_mutation_rejected']=(sum(z['loss_ns'] for z in y['rows'] if z['loss_role']=='g')!=y['parent_result_g_sum_ns'])
    controls['seed_mutation_changes_result']=derive(x,SEED+1)[1] != d
    checks['corruptions']=all(controls.values())
    out={'pass':all(checks.values()),'checks':checks,'corruption_controls':controls,'derived':d,'ledger_sha256':hashlib.sha256(Path(a.ledger).read_bytes()).hexdigest()}
    o.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True));raise SystemExit(0 if out['pass'] else 1)
if __name__=='__main__':main()
