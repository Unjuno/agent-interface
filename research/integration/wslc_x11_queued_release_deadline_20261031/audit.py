import json,sys
from pathlib import Path
b=Path(sys.argv[1]);summary={}
for n in ('a01','a02','a03'):
 p=b/('wslc-x11-queued-release-20261031-'+n);o=p/'output';assert (p/'container.exit').read_text().strip()=='0';owner=json.loads((o/'owner-outcome.json').read_text());ready=json.loads((o/'cleanup-ready.json').read_text());stop=json.loads((o/'server-stopped.json').read_text());sent=json.loads((o/'release-queued.json').read_text());resume=json.loads((o/'server-resumed.json').read_text());cleanup=json.loads((o/'cleanup-outcome.json').read_text());timing=json.loads((o/'cleanup-timing.json').read_text());r=json.loads((o/'result.json').read_text());assert owner['status']=='unknown' and owner['reason']=='transaction_deadline' and owner['worker_retired'] and stop['state']=='T' and stop['pid']==resume['pid'] and sent['pid']==ready['pid'] and ready['ready_ns']<stop['stopped_ns']<sent['flushed_ns']<resume['resumed_ns'];assert timing['pauser_exit']==0 and cleanup['worker_retired'] and r['button_down_before_cleanup'] and r['observed_after_scheduled_late_ns']>r['scheduled_late_ns'] and not r['late_artifact_present'];assert all(e['window']==r['target'] and e['detail']==1 for e in r['target_events'])
 if n=='a01':assert cleanup['status']=='completed' and cleanup['synced_ns']>resume['resumed_ns'] and not cleanup['button_down_after'] and not r['button_down_final'] and [e['type'] for e in r['target_events']]==[4,5] and not (o/'fallback-release.json').exists()
 else:
  fallback=json.loads((o/'fallback-release.json').read_text());assert cleanup['status']=='unknown' and cleanup['reason']=='transaction_deadline' and cleanup['worker_exitcode']==-15 and r['button_down_after_cleanup'] and r['button_down_final'] and [e['type'] for e in r['target_events']]==[4] and fallback=={'performed':True,'button_down_after':False}
  if n=='a03':
   returned=json.loads((o/'cleanup-returned.json').read_text());assert returned['worker_retired'] and returned['status']=='unknown' and sent['flushed_ns']<returned['returned_ns']<resume['resumed_ns']
 summary[n]={'cleanup_status':cleanup['status'],'target_events_before_fallback':[e['type'] for e in r['target_events']],'button_down_before_fallback':r['button_down_final'],'worker_retired_before_resume_verified':n=='a03'}
print(json.dumps(summary,indent=2))
