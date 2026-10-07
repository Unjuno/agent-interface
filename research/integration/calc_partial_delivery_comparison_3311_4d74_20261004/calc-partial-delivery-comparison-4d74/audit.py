import json,pathlib,hashlib,base64
R=pathlib.Path('/data');O=pathlib.Path('/out');summary=json.loads((R/'SUMMARY.json').read_text());rows=[];errors=[]
expected=json.loads((R/'EVIDENCE.json').read_text())['final']['native']['artifact']['sha256']
for s in summary:
 v=json.loads((R/'runs'/str(s['index'])/'model-batch/HOST_RECORD.private.json').read_text());requests=[x for x in v['received'] if x.get('method')=='item/tool/call'];replies=[x['result'] for x in v['sent'] if x.get('id')==requests[0]['id'] and 'result' in x];reply=replies[0];items=reply['contentItems'];typed=json.loads(next(x['text'] for x in items if x['type']=='inputText'));image=next(x['imageUrl'] for x in items if x['type']=='inputImage');digest=hashlib.sha256(base64.b64decode(image.split(',',1)[1])).hexdigest()
 if len(requests)!=1 or reply['success'] != (s['arm']=='delivered') or digest!=expected or typed['completed_transitions']!=1 or typed['reason']!='effect_unavailable':errors.append('feedback custody '+str(s['index']))
 messages=[x['params']['item'].get('text','') for x in v['received'] if x.get('method')=='item/completed' and x.get('params',{}).get('item',{}).get('type')=='agentMessage']
 rows.append(dict(index=s['index'],arm=s['arm'],messages=messages,usage=v['usage'],feedback_sha256=digest,typed=typed,outer_success=reply['success']))
out=dict(scope='FOUR_FRESH_MODEL_CONTEXTS_RETAINED_IMAGE_REPLY_ONLY',rows=rows,errors=errors,scoring='Final text requires independent semantic inspection; custody PASS does not imply reporting correctness.')
with (O/'AUDIT.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out));raise SystemExit(bool(errors))
