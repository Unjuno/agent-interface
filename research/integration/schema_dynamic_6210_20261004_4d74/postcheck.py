"""Additional saved-only full-cohort/feedback-image custody check."""
import base64,copy,hashlib,json,pathlib,sys
from PIL import Image
R=pathlib.Path('/src');P=json.loads((R/'PLAN.json').read_text());records=[]
def check(rows):
 errors=[];threads=[]
 if len(rows)!=8 or [r['host']['spec']['index'] for r in rows]!=list(range(8)):errors.append('cohort')
 for r in rows:
  h,raw=r['host'],r['raw'];spec=h['spec'];threads.append(h['thread_start']['thread']['id']);tool=[e for e in h['received'] if e.get('method')=='item/tool/call'];turn=[e for e in h['sent'] if e.get('method')=='turn/start'];responses=[e for e in h['sent'] if 'result' in e and 'method' not in e];ends=[e for e in h['received'] if e.get('method')=='turn/completed'];usage=[e['params']['tokenUsage'] for e in h['received'] if e.get('method')=='thread/tokenUsage/updated']
  if len(tool)!=1 or len(turn)!=1 or len(responses)!=1 or len(ends)!=1:errors.append('request/turn cohort')
  else:
   imageItems=[x for x in responses[0]['result']['contentItems'] if x['type']=='inputImage'];imagePath=[x['path'] for x in turn[0]['params']['input'] if x['type']=='localImage']
   if responses[0]['id']!=tool[0]['id'] or not responses[0]['result']['success']:errors.append('tool result identity')
   if len(imageItems)!=1 or len(imagePath)!=1:errors.append('model image count')
   else:
    returned=base64.b64decode(imageItems[0]['imageUrl'].split(',',1)[1],validate=True)
    if returned!=r['final_bytes'] or pathlib.Path(imagePath[0]).name!=pathlib.Path(raw['initial']['artifact']['path']).name:errors.append('original feedback/input delivery')
  if not usage or h['usage']!=usage[-1]['total']:errors.append('all usage')
  if h['errors'] or raw['errors'] or h['native_exit']!=0 or h['app_server_exit']!=0 or h.get('app_server_forced_terminate'):errors.append('terminal custody')
  if raw['effect']['selected']!=spec['target'] or r['footer_pixel']!=((144,238,144) if spec['target']=='GREEN' else (135,206,250)):errors.append('persisted/visible state')
  if any(e.get('method','').startswith('mcpServer/') for e in h['received']):errors.append('MCP startup exposure')
 if len(set(threads))!=8:errors.append('fresh thread identity')
 return errors
for i in range(8):
 O=R/'runs'/('row'+str(i+1).zfill(2));h=json.loads((O/'HOST_RECORD.json').read_text());raw=json.loads((O/'raw.json').read_text());image=O/'images'/pathlib.Path(raw['final']['artifact']['path']).name;records.append(dict(host=h,raw=raw,final_bytes=image.read_bytes(),footer_pixel=Image.open(image).convert('RGB').getpixel((100,285))))
errors=check(records);controls={}
for name,alter in [('missing_row',lambda r:r.pop()),('feedback_bytes',lambda r:r[0].update(final_bytes=b'wrong')),('selected_state',lambda r:r[0]['raw']['effect'].update(selected='BLUE')),('footer_pixel',lambda r:r[0].update(footer_pixel=(255,255,255))),('usage',lambda r:r[0]['host']['usage'].update(inputTokens=0)),('duplicate_thread',lambda r:r[1]['host']['thread_start']['thread'].update(id=r[0]['host']['thread_start']['thread']['id']))]:
 mutated=copy.deepcopy(records);alter(mutated);controls[name]=bool(check(mutated))
if not all(controls.values()):errors.append('corruption survived')
print(json.dumps(dict(status='PASS_SAVED_SUPPLEMENT' if not errors else 'FAIL_SUPPLEMENT',errors=errors,controls=controls,rows=8,model_replays=0,native_replays=0,formal_auditor_replays=0),indent=2));sys.exit(bool(errors))
