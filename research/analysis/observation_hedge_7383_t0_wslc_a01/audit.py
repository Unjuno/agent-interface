import json
import math
from pathlib import Path

OUT=Path('/out')
CAL=(2,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,40)
Q=sorted(CAL)[math.ceil(0.90*len(CAL))-1]

def enumerate_cases():
    for f in ('heavy_tail','correlated','shared_queue','cancel_lag','generation_flip'):
        for n in range(40):
            if f=='heavy_tail': p,s,c,g=(80 if n%10==0 else 3+n%7),3+n%4,0,None
            elif f=='correlated': p,s,c,g=8+n%9,9+n%9,0,None
            elif f=='shared_queue': p,s,c,g=5+n%8,6+n%9,0,None
            elif f=='cancel_lag': p,s,c,g=18+n%13,3+n%5,8+n%9,None
            else: p,s,c,g=5+n%8,3+n%5,0,3
            yield {'id':f'{f}-{n:02d}','family':f,'p':p,'s':s,'cancel':c,'flip':g}

def oracle(x,arm):
    delay={'single':None,'delayed':Q,'immediate':0}[arm]
    duplicate=delay is not None and (delay==0 or x['p']>delay)
    primary=x['p']+(8 if duplicate and x['family']=='shared_queue' else 0)
    requests=[('primary',0,primary)]
    if duplicate: requests.append(('secondary',delay,x['s']))
    completions=[]
    for role,start,duration in requests:
        end=start+duration
        captured=1 if x['flip'] is not None and start>=x['flip'] else 0
        now=1 if x['flip'] is not None and end>=x['flip'] else 0
        if captured==now: completions.append((end,role,captured,duration,start))
    win=min(completions,key=lambda z:(z[0],z[1])) if completions else None
    amount=0
    for role,start,duration in requests:
        if win is None: amount+=duration
        elif role==win[1]: amount+=duration
        else: amount+=max(0,min(duration,win[0]-start+x['cancel']))
    response=[{'time':start+duration,'role':role,
       'epoch':(1 if x['flip'] is not None and start>=x['flip'] else 0),
       'current':((1 if x['flip'] is not None and start>=x['flip'] else 0)==(1 if x['flip'] is not None and start+duration>=x['flip'] else 0)),
       'complete':True,'service':duration,'start':start}
       for role,start,duration in requests]
    return {'id':x['id'],'family':x['family'],'arm':arm,'threshold':Q,
      'winner':win[1] if win else None,'epoch':win[2] if win else None,
      'latency':win[0] if win else None,'work':amount,'responses':response}

data=json.loads((OUT/'candidate.json').read_text())
expected=[oracle(c,a) for c in enumerate_cases() for a in ('single','delayed','immediate')]
errors=[]
if data.get('threshold')!=Q: errors.append('threshold')
if data.get('rows')!=expected: errors.append('independent-reconstruction')
if len(expected)!=600: errors.append('denominator')

def rejects(rows):
    return rows!=expected
mutations=[]
for name,edit in (
 ('partial_response',lambda r:r[0]['responses'][0].update({'complete':False})),
 ('old_generation_first',lambda r:r[(4*40+7)*3+1].update({'winner':'primary','epoch':0,'latency':r[(4*40+7)*3+1]['responses'][0]['time']})),
 ('double_admission',lambda r:r[0].update({'winner':'both'})),
 ('loser_work_omitted',lambda r:r[1].update({'work':0}))):
    copy=json.loads(json.dumps(expected)); edit(copy)
    mutations.append({'name':name,'rejected':rejects(copy)})

summaries={}
for fam in ('heavy_tail','correlated','shared_queue','cancel_lag','generation_flip'):
    summaries[fam]={}
    for arm in ('single','delayed','immediate'):
        rr=[r for r in expected if r['family']==fam and r['arm']==arm]
        good=sorted(r['latency'] for r in rr if r['latency'] is not None)
        rank=math.ceil(.95*len(rr))
        p95=good[rank-1] if len(good)>=rank else 'INF'
        summaries[fam][arm]={'n':len(rr),'valid':len(good),'unavailable':len(rr)-len(good),'p95_all_cases_ms':p95,'mean_work':sum(r['work'] for r in rr)/len(rr),'max_work':max(r['work'] for r in rr)}
if not all(m['rejected'] for m in mutations): errors.append('mutation_controls')
report={'status':'PASS_METHOD_SCOPED' if not errors else 'FAIL_AUDIT','errors':errors,'rows_reconstructed':len(expected),'threshold':Q,'mutations':mutations,'summary':summaries}
(OUT/'audit.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
print(json.dumps(report,sort_keys=True))
raise SystemExit(0 if not errors else 1)
