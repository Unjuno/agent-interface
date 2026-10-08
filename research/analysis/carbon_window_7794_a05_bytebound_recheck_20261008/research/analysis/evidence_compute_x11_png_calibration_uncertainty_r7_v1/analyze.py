import argparse,json,random
from pathlib import Path
N=100000; SEED=1784001; P=0.25
def pct(v,q):
    s=sorted(v); return s[round((len(s)-1)*q)]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--ledger',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
    o=Path(a.output);assert not o.exists()
    x=json.loads(Path(a.ledger).read_text()); rows=x['rows']
    gs=[r['loss_ns'] for r in rows if r['loss_role']=='g']; ws=[r['loss_ns'] for r in rows if r['loss_role']=='w']
    assert (len(gs),sum(gs),len(ws),sum(ws))==(24,x['parent_result_g_sum_ns'],8,x['parent_result_w_sum_ns'])
    rng=random.Random(SEED); ps=[]; ds=[]; wait=0
    for _ in range(N):
        gb=[gs[rng.randrange(len(gs))] for _ in gs]; wb=[ws[rng.randrange(len(ws))] for _ in ws]
        g=sum(gb)/len(gb); w=sum(wb)/len(wb); pstar=g/(g+w)
        delta=P*w-(1-P)*g
        ps.append(pstar);ds.append(delta);wait+=int(P>pstar and delta>0)
    loo=[]
    for r in rows:
        g2=[z['loss_ns'] for z in rows if z['loss_role']=='g' and z['scenario_id']!=r['scenario_id']]
        w2=[z['loss_ns'] for z in rows if z['loss_role']=='w' and z['scenario_id']!=r['scenario_id']]
        g=sum(g2)/len(g2);w=sum(w2)/len(w2);pstar=g/(g+w);delta=P*w-(1-P)*g
        loo.append({'removed':r['scenario_id'],'p_star':pstar,'delta_run_minus_wait_ns':delta,'policy':'WAIT' if P>pstar and delta>0 else 'RUN_OR_UNCERTAIN'})
    result={'decision':None,'bootstrap_iterations':N,'seed':SEED,'p':P,'counts':{'g':len(gs),'w':len(ws),'rows':len(rows)},'sums':{'g_sum_ns':sum(gs),'w_sum_ns':sum(ws)},'p_star':{'lo95':pct(ps,.025),'median':pct(ps,.5),'hi95':pct(ps,.975)},'delta_run_minus_wait_ns':{'lo95':pct(ds,.025),'median':pct(ds,.5),'hi95':pct(ds,.975)},'bootstrap_wait_fraction':wait/N,'leave_one_out_wait':sum(z['policy']=='WAIT' for z in loo),'leave_one_out':loo,'invocations':1,'reruns':0,'replacements':0,'tuning':0}
    ok=result['p_star']['hi95']<P and result['delta_run_minus_wait_ns']['lo95']>0 and wait==N and result['leave_one_out_wait']==32
    result['decision']='PASS_X11_PNG_CALIBRATION_WAIT_ROBUST_SCOPED' if ok else 'HOLD_X11_PNG_POLICY_UNCERTAIN'
    o.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='leave_one_out'},indent=2,sort_keys=True))
if __name__=='__main__':main()
