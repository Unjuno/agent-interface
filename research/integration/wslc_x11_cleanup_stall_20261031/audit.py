import json,sys
from pathlib import Path
b=Path(sys.argv[1]);summary={}
for n in ('a01','a02'):
 p=b/('wslc-x11-cleanup-stall-20261031-'+n);o=p/'output';assert (p/'container.exit').read_text().strip()=='0';owner=json.loads((o/'owner-outcome.json').read_text());cleanup=json.loads((o/'cleanup-outcome.json').read_text());timing=json.loads((o/'cleanup-timing.json').read_text());r=json.loads((o/'result.json').read_text());assert owner['status']=='unknown' and owner['reason']=='transaction_deadline' and owner['worker_retired'];assert cleanup['worker_retired'] and r['button_down_before_cleanup'] and not r['late_artifact_present'] and r['observed_after_scheduled_late_ns']>r['scheduled_late_ns'];assert all(x['window']==r['target'] and x['detail']==1 for x in r['target_events'])
 if n=='a01':
  assert timing['server_paused_during_cleanup'] is False and cleanup['owner_release_attempt']['status']=='readback_verified' and cleanup['cleanup_status']=='UNKNOWN' and cleanup['release_confirmed'] is False and not r['button_down_after_cleanup'] and not r['button_down_final'] and [x['type'] for x in r['target_events']]==[4,5] and not (o/'fallback-release.json').exists()
 else:
  fallback=json.loads((o/'fallback-release.json').read_text());assert timing['server_paused_during_cleanup'] is True and cleanup['status']=='unknown' and cleanup['reason']=='transaction_deadline' and timing['end_ns']>=timing['deadline_ns'] and r['button_down_after_cleanup'] and r['button_down_final'] and [x['type'] for x in r['target_events']]==[4] and fallback=={'performed':True,'button_down_after':False}
 summary[n]={'cleanup_status':cleanup['status'],'reason':cleanup.get('reason'),'elapsed_ms':round(timing['elapsed_ns']/1e6,3),'button_down_before_fallback':r['button_down_final'],'target_events_before_fallback':[x['type'] for x in r['target_events']]}
print(json.dumps(summary,indent=2))
