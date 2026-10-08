from __future__ import annotations
import argparse, json
from collections import defaultdict
from common import *
EXPECTED_A0 = EXPECTED_B1000
def make_trace(age_ms:int, post_dir:int, phase_us:int, traj_id:str, accel_ppm:int):
    ts=sample_times_us(phase_us); exact=[position_accel_u(t,age_ms,post_dir,accel_ppm) for t in ts]
    jit=[jitter_u(traj_id,t) for t in ts]; obs=[x+j for x,j in zip(exact,jit)]; return ts,exact,jit,obs
def row(age_ms,post_dir,phase_us,arm,traj_id):
    accel=ACCEL_ARMS[arm]; ts,exact,jit,obs=make_trace(age_ms,post_dir,phase_us,traj_id,accel)
    pred,ops=bounded_estimator(obs,ASSUMED_BOUND_U)
    return {'trajectory_id':traj_id,'age_ms':age_ms,'post_dir':post_dir,'phase_us':phase_us,'arm':arm,'accel_ppm_per_100ms':accel,
      'assumed_position_bound_u':ASSUMED_BOUND_U,'sample_times_us':ts,'exact_positions_u':exact,'jitter_u':jit,'observed_positions_u':obs,
      'd_new_u':obs[0]-obs[1],'d_prev_u':obs[1]-obs[2],'prediction':pred,'oracle':post_dir,'correct':pred==post_dir,'unknown':pred==UNKNOWN,
      'wrong_direction':pred not in (UNKNOWN,post_dir),'ops':ops,'authority_granted':False,'task_input_granted':False}
def summarize(rows):
    cells=defaultdict(lambda:[0,0,0,0])
    for r in rows:
        a=cells[(r['arm'],r['age_ms'])]; a[0]+=1; a[1]+=int(r['correct']); a[2]+=int(r['unknown']); a[3]+=int(r['wrong_direction'])
    out={}
    for (arm,age),(n,c,u,w) in sorted(cells.items()):
        out.setdefault(arm,{})[str(age)]={'n':n,'accuracy':c/n,'unknown_rate':u/n,'wrong_direction_rate':w/n}
    return out
def run(mode,out):
    rows=[]
    if mode=='formal': ages=FORMAL_AGES_MS; phases=[i*1000 for i in range(100)]; invocation=1; prefix='F'
    else: ages=(40,110,175); phases=(500,33_500,66_500,99_500); invocation=0; prefix='C8'
    for age in ages:
      for post in (-1,1):
       for phase in phases:
        traj=(f'F|a={age}|d={post}|p={phase//1000}' if mode=='formal' else f'{prefix}|a={age}|d={post}|p_us={phase}')
        for arm in ACCEL_ARMS: rows.append(row(age,post,phase,arm,traj))
    p={'task':'TEMPORAL-REVERSAL-BOUNDED-ACCELERATION-R1-20260918-008','mode':mode,'formal_invocation':invocation,'reruns':0,'row_count':len(rows),'summary':summarize(rows),'rows':rows}
    with open(out,'w') as f: json.dump(p,f,separators=(',',':'),sort_keys=True)
    print(json.dumps({'mode':mode,'rows':len(rows),'summary':p['summary']},sort_keys=True))
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('mode',choices=['construction','formal']); ap.add_argument('out'); a=ap.parse_args(); run(a.mode,a.out)
