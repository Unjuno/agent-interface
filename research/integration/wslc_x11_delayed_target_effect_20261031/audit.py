import json,sys
from pathlib import Path
b=Path(sys.argv[1]);summary={}
for n in ('a01','a02'):
 p=b/('wslc-x11-delayed-target-effect-20261031-'+n);o=p/'output';read=lambda name:json.loads((o/name).read_text());assert (p/'container.exit').read_text().strip()=='0';ready=read('target-ready.json');sup=read('supervisor-ready.json');sent=read('pair-synced.json');owner=read('owner-outcome.json');timing=read('timing.json');events=read('target-events.json');effect=read('target-effect.json');r=read('result.json');assert owner['status']=='unknown' and owner['reason']=='transaction_deadline' and owner['worker_retired'];assert sent['target']==ready['window']==sup['target_window'] and len(events)==2 and [x['type'] for x in events]==[4,5] and all(x['window']==ready['window'] and x['detail']==1 for x in events);assert timing['start_ns']<sent['sent_ns']<timing['deadline_ns']<=timing['returned_ns'] and r['buttons']==0 and r['target_exit']==0 and not r['late_artifact_present'] and r['observed_ns']>sent['scheduled_late_ns'] and not (o/'fallback.txt').exists();assert events[0]['handled_ns']<=events[1]['handled_ns']<=effect['effect_ns']
 if n=='a01':assert effect['effect_ns']<timing['deadline_ns'] and timing['effect_existed_at_return']
 else:
  stop=read('target-stopped.json');resume=read('target-resumed.json');assert stop['state']=='T' and stop['stopped_ns']<sent['sent_ns'] and not timing['effect_existed_at_return'] and timing['returned_ns']<resume['resumed_ns']<=events[0]['handled_ns']<=effect['effect_ns']
 summary[n]={'owner_status':owner['status'],'effect_existed_at_return':timing['effect_existed_at_return'],'effect_after_deadline':effect['effect_ns']>timing['deadline_ns'],'effect_after_return':effect['effect_ns']>timing['returned_ns'],'buttons':r['buttons'],'extra_late_artifact':r['late_artifact_present']}
print(json.dumps(summary,indent=2))
