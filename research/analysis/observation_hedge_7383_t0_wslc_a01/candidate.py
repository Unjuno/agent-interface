import json
import math
from pathlib import Path

OUT = Path('/out')
CAL = [2,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,40]
THRESHOLD = sorted(CAL)[math.ceil(.90 * len(CAL))-1]

def cases():
    result=[]
    for family in ('heavy_tail','correlated','shared_queue','cancel_lag','generation_flip'):
        for i in range(40):
            if family=='heavy_tail': p=(80 if i%10==0 else 3+i%7); s=3+i%4; cancel=0; flip=None
            elif family=='correlated': p=8+i%9; s=p+1; cancel=0; flip=None
            elif family=='shared_queue': p=5+i%8; s=6+i%9; cancel=0; flip=None
            elif family=='cancel_lag': p=18+i%13; s=3+i%5; cancel=8+i%9; flip=None
            else: p=5+i%8; s=3+i%5; cancel=0; flip=3
            result.append({'id':f'{family}-{i:02d}','family':family,'p':p,'s':s,'cancel':cancel,'flip':flip})
    return result

def run(case, arm):
    launch = {'single':None,'delayed':THRESHOLD,'immediate':0}[arm]
    p=case['p']
    hedged = launch is not None and (launch==0 or p>launch)
    if hedged and case['family']=='shared_queue': p += 8
    starts=[(0,p,0,'primary')]
    if hedged: starts.append((launch,case['s'],launch,'secondary'))
    finishes=[]
    for start,service,_,role in starts:
        complete=start+service
        epoch=1 if case['flip'] is not None and start>=case['flip'] else 0
        gen_at_complete=1 if case['flip'] is not None and complete>=case['flip'] else 0
        finishes.append({'time':complete,'role':role,'epoch':epoch,'current':epoch==gen_at_complete,'complete':True,'service':service,'start':start})
    valid=[x for x in finishes if x['current'] and x['complete']]
    winner=min(valid,key=lambda x:(x['time'],x['role'])) if valid else None
    observed=winner['time'] if winner else None
    work=0
    for x in finishes:
        if winner is None: work += x['service']
        elif x is winner: work += x['service']
        else: work += max(0,min(x['service'],winner['time']-x['start']+case['cancel']))
    return {'id':case['id'],'family':case['family'],'arm':arm,'threshold':THRESHOLD,'winner':winner['role'] if winner else None,'epoch':winner['epoch'] if winner else None,'latency':observed,'work':work,'responses':finishes}

rows=[run(c,a) for c in cases() for a in ('single','delayed','immediate')]
(OUT/'candidate.json').write_text(json.dumps({'threshold':THRESHOLD,'rows':rows},sort_keys=True,separators=(',',':'))+'\n')
print(json.dumps({'status':'CANDIDATE_COMPLETE','threshold':THRESHOLD,'cases':len(cases()),'rows':len(rows)}))
