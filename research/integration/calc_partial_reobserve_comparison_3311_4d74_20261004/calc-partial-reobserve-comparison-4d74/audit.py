import json,pathlib,hashlib,base64
R=pathlib.Path('/data');O=pathlib.Path('/out');summary=json.loads((R/'SUMMARY.json').read_text());rows=[];errors=[]
e=json.loads((R/'EVIDENCE.json').read_text());expected=e['final']['native']['artifact']['sha256']
for s in summary:
 v=json.loads((R/'runs'/str(s['index'])/'model-batch/HOST_RECORD.private.json').read_text());requests=[x for x in v['received'] if x.get('method')=='item/tool/call'];reply=next(x['result'] for x in v['sent'] if x.get('id')==requests[0]['id'] and 'result' in x);items=reply['contentItems'];typed=json.loads(next(x['text'] for x in items if x['type']=='inputText'));image=next(x['imageUrl'] for x in items if x['type']=='inputImage');digest=hashlib.sha256(base64.b64decode(image.split(',',1)[1])).hexdigest()
 turns=[x for x in v['sent'] if x.get('method')=='turn/start'];second=turns[1]['params']['input'];local=[x for x in second if x['type']=='localImage']
 if len(requests)!=1 or reply['success'] is not False or digest!=expected or typed['reason']!='effect_unavailable' or len(turns)!=2:errors.append('first reply or turn count')
 if bool(local)!=(s['arm']=='image'):errors.append('second input arm')
 if local:
  p=R/'runs'/str(s['index'])/'guarded/images'/pathlib.Path(local[0]['path']).name
  if hashlib.sha256(p.read_bytes()).hexdigest()!=expected:errors.append('second image hash')
 messages=[x['params']['item'].get('text','') for x in v['received'] if x.get('method')=='item/completed' and x.get('params',{}).get('item',{}).get('type')=='agentMessage']
 completed=[x for x in v['received'] if x.get('method')=='turn/completed'];usage=[x['params']['tokenUsage']['total'] for x in v['received'] if x.get('method')=='thread/tokenUsage/updated']
 if len(completed)!=2 or usage[-1]!=v['usage']:errors.append('terminal/usage custody')
 rows.append(dict(index=s['index'],arm=s['arm'],messages=messages,usage=v['usage'],turns=len(turns),second_prompt=second[0]['text'],second_image_present=bool(local),feedback_sha256=digest))
out=dict(scope='FOUR_FRESH_TWO_TURN_CONTEXTS_RETAINED_IMAGE_REOBSERVATION',rows=rows,errors=errors,scoring='Primary semantic inspection separate from custody.')
with (O/'AUDIT.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out));raise SystemExit(bool(errors))
