import json,pathlib,hashlib
R=pathlib.Path(__file__).resolve().parent;results=[]
for study in ['calc-partial-reply-comparison-4d74','calc-partial-delivery-comparison-4d74']:
 for i in range(4):
  p=R/study/'runs'/str(i)/'model-batch/HOST_RECORD.private.json';v=json.loads(p.read_text(encoding='utf-8'));events=[]
  for n,x in enumerate(v['received']):
   m=x.get('method','');a=x.get('params',{})
   if m=='thread/tokenUsage/updated':events.append(dict(index=n,method=m,total=a['tokenUsage']['total']))
   if m=='turn/completed':events.append(dict(index=n,method=m))
   if m in ['item/started','item/completed'] and a.get('item',{}).get('type')=='dynamicToolCall':
    item=a['item'];events.append(dict(index=n,method=m,keys=list(item),status=item.get('status'),success=item.get('success'),contentKinds=[y.get('type') for y in (item.get('contentItems') or [])]))
  usages=[x['params']['tokenUsage']['total'] for x in v['received'] if x.get('method')=='thread/tokenUsage/updated']
  results.append(dict(study=study,case=i,source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),events=events,reported_usage=v['usage'],final_retained_usage=usages[-1],reported_matches_final=v['usage']==usages[-1]))
out=dict(scope='POSTRUN_NOTIFICATION_ORDER_NO_MODEL_REPLAY',first_probe_failure='Ephemeral inspection TypeError because started contentItems null; no experiment rerun.',results=results)
target=R/'DELIVERY_NOTIFICATION_AUDIT_4d74.json'
with target.open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
print(json.dumps(out))
