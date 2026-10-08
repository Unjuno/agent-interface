import argparse,json
p=argparse.ArgumentParser();p.add_argument('--raw',required=True);a=p.parse_args();d=json.load(open(a.raw,encoding='utf-8'))
def clamp(x,lo,hi):return min(hi,max(lo,x))
rows=[]
for e in d['episodes']:
 i=e['input'];y0=i['y'];u0=i['applied_u'];ref=i['ref'];kp=i['kp'];rate=i['rate_limit_per_tick'];r={'case':e['case']}
 for conditioned in (False,True):
  z=u0-kp*(ref-y0) if conditioned else 0.0;u=clamp(clamp(kp*(ref-y0)+z,0,1),u0-rate,u0+rate);iae=abs(ref-y0)
  for _ in range(20):
   y0=y0+0.25*(u-y0);iae+=abs(ref-y0);u=clamp(clamp(kp*(ref-y0)+z,0,1),u-rate,u+rate)
  r['conditioned' if conditioned else 'cold']={'final_y':round(y0,12),'final_abs_error':round(abs(ref-y0),12),'sum_abs_error_21_samples':round(iae,12)}
 rows.append(r)
print(json.dumps({'schema':'issue7424-bumpless-t0-posthoc-dynamics-v1','classification':'POSTHOC_SAVED_INPUT_ANALYSIS','candidate_rerun':False,'episodes':rows,'interpretation':'The held offset was frozen in the preregistered toy model; this posthoc calculation quantifies the tracking tradeoff and does not change the first-output decision gate.'},sort_keys=True,indent=2))
