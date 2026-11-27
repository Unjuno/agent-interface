import json,sys
from pathlib import Path
b=Path(sys.argv[1]);result={}
for n in ('a01','a02'):
 p=b/('wslc-calc-hit-to-press-race-20261031-'+n);out=p/'output';events=json.loads((out/'hit-guard-events.json').read_text());late=json.loads((out/'late-check.json').read_text());buttons=json.loads((out/'overlay-events.json').read_text());click=json.loads((out/'click-result.json').read_text());neutral=json.loads((out/'final-neutral.json').read_text());assert [e['stage'] for e in events]==['before_admission','before_focus','before_move','before_press'] and all(e['eligible'] and not e['injected'] for e in events);assert late['eligible'] is False and late['target'] not in late['chain'];assert neutral['keys_down']==[] and neutral['buttons']==0;assert all(x['verified'] and x['keys_down']==[] and x['buttons_down']==[] for x in click['execution']['releases'])
 if n=='a01':assert late['reject_enabled'] is False and click['status']=='completed' and [x['type'] for x in buttons]==[4,5] and all(x['window']==late['overlay'] and x['detail']==1 for x in buttons)
 else:assert late['reject_enabled'] is True and click['status']=='execution_failed' and click['execution']['failed_op']==2 and click['execution']['emissions']==1 and buttons==[]
 result[n]={'initial_checks_passed':True,'late_target_eligible':False,'late_reject_enabled':late['reject_enabled'],'click_status':click['status'],'overlay_event_types':[x['type'] for x in buttons],'releases_verified':True}
print(json.dumps(result,indent=2))
