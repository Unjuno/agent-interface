import json,sys
from pathlib import Path
b=Path(sys.argv[1]);summary={}
for n in ('a01','a02','a03','a04'):
 p=b/('wslc-calc-live-hit-guard-20261031-'+n);events=json.loads((p/'output/hit-guard-events.json').read_text());click=json.loads((p/'output/click-result.json').read_text());assert [e['stage'] for e in events]==['before_admission','before_focus','before_move','before_press'];assert all(e['eligible'] for e in events[:3]);assert events[-1]['eligible']==(n=='a01');releases=click['execution']['releases'];assert releases and all(x['verified'] and x['keys_down']==[] and x['buttons_down']==[] for x in releases)
 if n=='a01':
  assert click['status']=='completed';r=json.loads((p/'output/result.json').read_text());assert r['method']['method_receipt']['outcome']=='TASK_SUCCEEDED' and r['keys_down']==[] and r['buttons']==0
 else:
  neutral=json.loads((p/'output/final-neutral.json').read_text());assert neutral['keys_down']==[] and neutral['buttons']==0
  if n in ('a02','a03'):assert click['status']=='execution_failed' and click['execution']['failed_op']==2 and click['execution']['emissions']==1
  if n=='a03':assert json.loads((p/'output/overlay-events.json').read_text())==[]
  if n=='a04':
   assert click['status']=='completed';overlay=json.loads((p/'output/overlay-events.json').read_text());assert [e['type'] for e in overlay]==[4,5] and [e['detail'] for e in overlay]==[1,1] and len({e['window'] for e in overlay})==1
 summary[n]={'click_status':click['status'],'before_press_eligible':events[-1]['eligible'],'emissions':click['execution']['emissions']}
print(json.dumps(summary,indent=2))
