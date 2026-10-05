"""Saved-only tool/native-state/visual-postcondition reader; no producer imports."""
import hashlib,json,pathlib,sys
from PIL import Image
R=pathlib.Path('/src');P=json.loads((R/'PLAN.json').read_text());errors=[];rows=[];totals={};E=json.loads((R/'EXECUTION.json').read_text())
def need(v,msg):
 if not v:errors.append(msg)
for p,h in P['source_hashes'].items():need(hashlib.sha256((R/p).read_bytes()).hexdigest()==h,'source drift '+p)
for execution in E['rows']:
 i=execution['index'];spec=P['rows'][i];O=R/'runs'/('row'+str(i+1).zfill(2));host=json.loads((O/'HOST_RECORD.json').read_text());raw=json.loads((O/'raw.json').read_text()) if (O/'raw.json').exists() else {};tool=[e for e in host['received'] if e.get('method')=='item/tool/call'];done=[e for e in host['received'] if e.get('method')=='turn/completed'];usage=[e['params']['tokenUsage'] for e in host['received'] if e.get('method')=='thread/tokenUsage/updated'];row=dict(index=i,variant=spec['variant'],target=spec['target'],host_errors=host['errors'],raw_errors=raw.get('errors'),tool_calls=len(tool),completed_turns=len(done),usage_updates=len(usage),exact=False)
 if usage:
  row['usage']=usage[-1]['total'];need(host.get('usage')==row['usage'],'usage custody '+str(i))
  for k,v in row['usage'].items():
   if type(v) is int:totals[k]=totals.get(k,0)+v
 if tool and raw.get('proposal'):
  request=tool[0];params=request['params'];args=params['arguments'];args=json.loads(args) if isinstance(args,str) else args;keys=('x','y') if spec['variant']=='A' else ('horizontal','vertical');x,y=args[keys[0]],args[keys[1]];need(params['tool']==P['tools'][spec['variant']]['name'] and set(args)==set(keys),'registered tool schema '+str(i));need(type(x)==int and type(y)==int and 0<=x<640 and 0<=y<360,'native bounds '+str(i));label='GREEN' if 60<=x<280 and 140<=y<230 else 'BLUE' if 350<=x<570 and 140<=y<230 else 'NONE';history=raw.get('effect',{}).get('history',[]);need(len(history)==1 and history[0]['x']==x and history[0]['y']==y and history[0]['label']==label and history[0]['matching_press'],'native event reconstruction '+str(i));need(raw['canonical_program']['ops'][1]['x']==x and raw['canonical_program']['ops'][1]['y']==y,'canonical dispatch '+str(i))
  for stage in ['initial','final']:
   ar=raw[stage]['artifact'];image=O/'images'/pathlib.Path(ar['path']).name;need(hashlib.sha256(image.read_bytes()).hexdigest()==ar['sha256'],'exact PNG '+str(i)+stage)
  pixel=Image.open(O/'images'/pathlib.Path(raw['final']['artifact']['path']).name).convert('RGB').getpixel((100,285));row['footer_pixel']=pixel;row['selected']=raw.get('effect',{}).get('selected');row['coordinates']=[x,y];row['initial_png']=raw['initial']['artifact']['sha256'];row['final_png']=raw['final']['artifact']['sha256'];need(host.get('model_input_png_sha256')==row['initial_png'] and host.get('model_feedback_png_sha256')==row['final_png'],'model image links '+str(i))
  released=raw.get('cleanup_release',{}).get('verified') and not any(raw.get('physical_keys',[1])) and raw.get('physical_button_mask')==0;row['released']=bool(released);row['exact']=len(tool)==1 and len(done)==1 and host.get('native_exit')==0 and not host['errors'] and not raw['errors'] and raw['receipt']['status']=='completed' and len(history)==1 and label==spec['target'] and row['selected']==spec['target'] and pixel==((144,238,144) if spec['target']=='GREEN' else (135,206,250)) and released
 rows.append(row)
need(len({r.get('initial_png') for r in rows if r.get('initial_png')})<=1,'initial image drift')
out=dict(status='PASS_SAVED_EVIDENCE' if not errors else 'FAIL_AUDIT',errors=errors,planned_rows=8,attempted_rows=len(rows),rows=rows,exact=sum(r['exact'] for r in rows),total_usage=totals,hypothesis='UNCERTAIN_EXPLORATORY',scope='Actually registered function tools; custom native selection-state task with persisted and original-pixel postconditions. Not a real-app suite, immutable-provider snapshot or adequately powered causal schema effect. Usage notifications are not proof of exact provider request/generation counts.')
print(json.dumps(out,indent=2,sort_keys=True));sys.exit(bool(errors))
