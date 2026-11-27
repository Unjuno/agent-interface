import json,sys
from pathlib import Path
b=Path(sys.argv[1]);out={}
for n in ('a01','a02','a03'):
 p=b/('wslc-x11-grab-supervisor-20261031-'+n);root=p/'output';owner=json.loads((root/'owner-outcome.json').read_text());r=json.loads((root/'result.json').read_text());ready=json.loads((root/'ready.json').read_text());assert ready['owner_supervisor_pid']!=ready['cleanup_supervisor_pid'] and owner['worker_retired'] is True;assert all(e['window']==r['target'] and e['detail']==1 for e in r['target_events'])
 if n in ('a01','a02'):
  assert owner['status']=='unknown' and owner['reason']=='transaction_deadline' and r['observed_after_scheduled_late_ns']>r['scheduled_late_ns'] and r['late_artifact_present'] is False;clean=json.loads((root/'cleanup-outcome.json').read_text());assert clean['release_confirmed'] is False and clean['cleanup_status']=='UNKNOWN' and r['button_down_before_cleanup'] is True
  if n=='a01':
   assert clean['owner_client_disconnect']['status']=='disconnected' and clean['owner_release_attempt']['status']=='readback_verified' and r['button_down_after_cleanup'] is False and r['button_down_final'] is False and [e['type'] for e in r['target_events']]==[4,5] and not (root/'fallback-release.txt').exists()
  else:
   f=json.loads((root/'fallback-release.json').read_text());assert clean['status']=='unknown' and clean['reason']=='invalid_cleanup_request' and 'owner_generation.child_pid' in clean['invalid_fields'] and r['button_down_after_cleanup'] is True and r['button_down_final'] is True and [e['type'] for e in r['target_events']]==[4] and f=={'performed':True,'button_down_after':False}
 else:assert owner['status']=='unknown' and owner['reason']=='stale_or_mismatched_receipt' and r['late_artifact_present'] and r['observed_ns']>=r['scheduled_late_ns'] and not r['button_down_final'] and [e['type'] for e in r['target_events']]==[4,5,4,5]
 out[n]={'owner_status':owner['status'],'owner_reason':owner.get('reason'),'target_event_types':[e['type'] for e in r['target_events']],'late_artifact_present':r['late_artifact_present']}
print(json.dumps(out,indent=2))
