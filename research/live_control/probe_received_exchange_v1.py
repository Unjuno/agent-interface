import json
from pathlib import Path
from received_continuation_v1 import start,advance
from received_exchange_v1 import request_once
HERE=Path(__file__).resolve().parent
r=HERE/'results/inkscape-guarded-click-01';events=[json.loads(l) for l in (r/'runtime/events.jsonl').read_text().splitlines()];failed=json.loads((r/'focus-x-current/calls.json').read_text());first=failed[0];session='recorded-socket';a=first['request']['after']
state=advance(start(session),session,0,{'status':'boundary','cursor':a,'records':events[:a]});seen=[]
def exchange(socket,q,**kwargs):
 seen.append(q)
 if len(seen)==1:return first['reply']
 index=next(i for i,e in enumerate(events) if e['event']=='command' and e['command'].get('transport_request_id')==first['request']['request_id'])
 return {'status':'boundary','cursor':index+2,'records':events[q['after']:index+2]}
spec={k:v for k,v in first['request'].items() if k!='after'}
one=request_once(session,state,spec,exchange);assert one['matched_clock'] is None
two=request_once(session,one['continuation'],{'events':['clock'],'timeout':2,'clock_request_id':one['requested_clock_id']},exchange)
assert two['matched_clock']['record']['runtime_ns']==106455132483
assert len(seen)==2 and sum('command' in q for q in seen)==1 and seen[1]['after']==25
out=HERE/'results/received-exchange-01';out.mkdir(exist_ok=False)
(out/'report.json').write_text(json.dumps({'scope':'injected recorded replies through actual caller function, no network','requests':seen,'first_matched_clock':one['matched_clock'],'final_matched_clock':two['matched_clock'],'image_sequence':two['continuation']['observation']['sequence']},indent=2)+'\n');print('Recorded stale-clock caller replay: one command, one read-only followup, current clock matched; image retained.')
