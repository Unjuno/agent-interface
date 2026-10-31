import json,sys
from pathlib import Path
b=Path(sys.argv[1]);summary={}
for n in ('a01','a02','a03'):
 p=b/('wslc-x11-app-barrier-20261031-'+n);o=p/'output';read=lambda name:json.loads((o/name).read_text());assert (p/'container.exit').read_text().strip()=='0';ready=read('target-ready.json');sent=read('pair-synced.json');owner=read('owner-outcome.json');timing=read('timing.json');marker=read('barrier-send.json');ack=read('barrier-ack.json');events=read('target-events.json');effect=read('target-effect.json');r=read('result.json');assert owner['status']=='unknown' and owner['reason']=='transaction_deadline' and owner['worker_retired'];assert sent['target']==ready['window']==marker['window']==ack['window'] and ack['target_pid']==ready['pid'] and ack['nonce']==marker['nonce']==97131;assert len(events)==2 and [e['type'] for e in events]==[4,5] and all(e['window']==ready['window'] and e['detail']==1 for e in events);assert sent['sent_ns']<timing['deadline_ns']<=timing['returned_ns']<marker['sent_ns']<=ack['ack_ns'] and events[-1]['handled_ns']<=ack['ack_ns'] and ack['release_seen'];assert r['buttons']==0 and r['target_exit']==0 and not r['late_artifact_present'] and r['observed_ns']>sent['scheduled_late_ns'] and not (o/'fallback.txt').exists()
 if n=='a01':assert marker['early_ack'] and ack['effect_exists_at_ack'] and effect['effect_ns']<=ack['ack_ns']
 elif n=='a02':
  stop=read('target-stopped.json');resume=read('target-resumed.json');assert stop['state']=='T' and stop['stopped_ns']<sent['sent_ns'] and not marker['early_ack'] and marker['checked_ns']<resume['resumed_ns']<=events[0]['handled_ns']<=ack['ack_ns'] and ack['effect_exists_at_ack'] and effect['effect_ns']<=ack['ack_ns']
 else:assert marker['early_ack'] and not ack['effect_exists_at_ack'] and ack['ack_ns']<effect['effect_ns']
 summary[n]={'early_ack':marker['early_ack'],'release_seen_at_ack':ack['release_seen'],'effect_exists_at_ack':ack['effect_exists_at_ack'],'effect_after_ack':effect['effect_ns']>ack['ack_ns'],'buttons':r['buttons']}
print(json.dumps(summary,indent=2))
