import base64,hashlib,json,pathlib,xml.etree.ElementTree as ET,copy
from predicate import retained_cue
ROOT=pathlib.Path(__file__).resolve().parent
def require(v,m):
 if not v:raise ValueError(m)
def read(p):return json.loads(p.read_text())
def neutral(r):return r.get('verified') is True and r.get('keys_down')==[] and r.get('buttons_down')==[]
def verify(root=ROOT):
 frozen=read(root/'FROZEN.json')
 for name,h in frozen['files'].items():require(hashlib.sha256((root/name).read_bytes()).hexdigest()==h,'frozen changed '+name)
 results=[];normalized={}
 for row in read(root/'schedule.json'):
  c=root/row['case'];positive=row['pair']==1;m=read(c/'method-common.json');cleanup=read(c/'cleanup.json')
  require(cleanup['host_exit']==0 and cleanup['all_owned_processes_terminal'] is True and len(cleanup['children'])==3,'terminal')
  require([x['name'] for x in cleanup['children']]==['inkscape','openbox','xvfb'],'children inventory')
  require([x['returncode'] for x in cleanup['children']]==[-15,0,0],'child exits')
  close=read(c/'replies/003.json')['reply'];require(close['status']=='closed' and close['release_attempted'] is True and neutral(close['release']),'close release')
  require(len(list((c/'commands').glob('*.json')))==3,'extra command')
  require([read(c/'commands'/f'{i:03d}.json')['op'] for i in (1,2,3)]==['observe','method','close'],'command order')
  reviews=[json.loads(line) for line in (c/'primary-decisions.jsonl').read_text().splitlines()];require([x['command'] for x in reviews]==[2,3],'review declarations')
  for i in (1,2):
   shown=read(c/'replies'/f'{i:03d}.json')['reply'];ref=shown['image_reference'];data=base64.b64decode(shown['image']['data'],validate=True)
   require(hashlib.sha256(data).hexdigest()==ref['sha256']==reviews[i-1]['review']['image_sha256'],'original image and primary review')
   require((c/'public/images'/pathlib.Path(ref['path']).name).read_bytes()==data,'image artifact')
  require(m['inputs']==(2 if positive else 1) and m['captures']==(3 if positive else 2),'method counts')
  require(m['save_dispatched'] is positive and m['save_completed'] is positive,'conditional Save')
  require(m['outcome']==('TASK_SUCCEEDED' if positive else 'SAFE_YIELD'),'outcome')
  require(m['reason']==('method_complete' if positive else 'effect_unavailable'),'reason')
  require(len(list(c.glob('method-dispatch-*.json')))==m['inputs'],'input inventory')
  programs=[];emissions=0
  for i in range(1,m['inputs']+1):
   d=read(c/f'method-dispatch-{i}.json');p=d['program'];actual=d['raw']['result'];require(actual['status']=='completed' and actual['recovery_required'] is False,'input result')
   releases=actual['execution']['releases'];require(releases and all(neutral(x) for x in releases),'input neutral')
   require(p['source']=={'observation_seq':i+1,'binding_revision':1},'source')
   require(actual['execution']['ended_ns']<p['authority']['expires_at_ns'],'input expiry')
   require(not actual['execution']['observations'],'unexpected inline observation')
   emissions+=actual['execution']['program_emissions'];p=copy.deepcopy(p);p['authority']['expires_at_ns']=0;programs.append(p)
  normalized[row['case']]=programs
  cues=[]
  for i in range(1,m['captures']+1):
   ob=read(c/f'method-observation-{i}.json')['observation'];a=ob['artifact'];data=(c/'public/images'/pathlib.Path(a['path']).name).read_bytes();cue=retained_cue(data,a['sha256'],row['layout']);cues.append(cue)
   if i>1:
    last=read(c/f'method-dispatch-{i-1}.json')['raw']['result']['execution'];require(ob['capture_started_ns']>last['ended_ns'],'not post-release capture')
  require(cues==([False,True,True] if positive else [False,None]),'cue sequence')
  request=read(c/'commands/002.json');require(len({p['authority']['expires_at_ns'] for p in request['programs'].values()})==1,'one frozen expiry')
  svg=c/'two-rectangles.svg';data=svg.read_bytes();tree=ET.fromstring(data);require(tree.get('viewBox')=='0 0 400 240','page')
  require(not any(el.get('transform') for el in tree.iter()),'transform')
  rects=[{k:float(el.get(k,'0')) for k in ('x','y','width','height')} for el in tree.iter('{http://www.w3.org/2000/svg}rect')]
  if positive:
   require(len(rects)==2,'saved rectangles')
   for v in rects:require(v['width']>0 and v['height']>0 and v['x']>=0 and v['y']>=0 and v['x']+v['width']<=400 and v['y']+v['height']<=240,'inside page')
   a,z=rects;require(a['x']+a['width']<=z['x'] or z['x']+z['width']<=a['x'] or a['y']+a['height']<=z['y'] or z['y']+z['height']<=a['y'],'overlap')
  else:require(not rects and hashlib.sha256(data).hexdigest()==read(c/'original-svg.json')['sha256'],'negative persisted change')
  require(read(c/'evaluation.json')['success'] is positive,'retained score')
  timing=read(c/'command-timing/002.json');duration=reviews[1]['declared_utc_ns']-timing['published_utc_ns'];require(duration>0,'review timing')
  results.append({'case':row['case'],'outcome':m['outcome'],'local_method_ms':m['elapsed_ns']/1e6,'publication_to_helper_read_ms':(timing['reply_read_ns']-timing['published_ns'])/1e6,'publication_to_later_primary_review_declaration_ms':duration/1e6,'semantic_model_latency':None,'program_physical_emissions':emissions,'backend_cumulative_emissions_at_last_input':read(c/f"method-dispatch-{m['inputs']}.json")['raw']['result']['execution']['emissions'],'saved_sha256':hashlib.sha256(data).hexdigest(),'saved_rectangles':rects})
 for a,z in [('positive-ordinary','positive-compiled'),('unknown-compiled','unknown-ordinary')]:
  require(normalized[a]==normalized[z],'paired inputs differ')
  require((root/a/'two-rectangles.svg').read_bytes()==(root/z/'two-rectangles.svg').read_bytes(),'paired SVG differs')
 return {'status':'PASS','cases':results,'commands':12,'input_programs':6,'primary_original_images':8,'local_method_captures':10,'all_native_captures':14,'scope':'finite retained bytes/independent SVG geometry. Timings descriptive; declaration proxy includes orchestration/reasoning, not ingestion/pure inference/semantic completion. No human or billing comparison.'}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
