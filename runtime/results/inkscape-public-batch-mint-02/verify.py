import pathlib,json,hashlib,base64,xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parent
def require(v,m):
 if not v:raise ValueError(m)
def read(p):return json.loads(p.read_text())
def verify(root=ROOT):
 for n,h in read(root/'FROZEN.json')['files'].items():require(hashlib.sha256((root/n).read_bytes()).hexdigest()==h,'frozen '+n)
 rows=[];clicks=[]
 for name,success,reason,ninputs,emissions,selected in [('normal-ordinary',True,'method_complete',3,37,[False,True,'unknown','unknown']),('normal-compiled',True,'method_complete',3,37,[False,True,'unknown','unknown']),('short-compiled',False,'effect_unavailable',2,13,[False,True,'unknown']),('short-ordinary',False,'effect_unavailable',2,13,[False,True,'unknown'])]:
  c=root/name;bridge=c/read(c/'owner.json')['bridge_relative'];require(bridge.resolve().is_relative_to(c.resolve()),'owned bridge directory');m=read(c/'method-common.json');inputs=read(c/'method-inputs.json');require(len(inputs)==ninputs and m['inputs']==ninputs and m['reason']==reason and m['outcome']==('TASK_SUCCEEDED' if success else 'SAFE_YIELD'),'outcome/input inventory')
  raw_inputs=[read(f) for f in bridge.glob('result-*.json') if 'execution' in read(f)];require(sorted(json.dumps(x,sort_keys=True) for x in raw_inputs)==sorted(json.dumps(x,sort_keys=True) for x in inputs),'raw input correspondence')
  require(sum(v['execution']['program_emissions'] for v in inputs)==emissions,'emissions')
  for v in inputs:
   require(v['status']=='completed' and v['recovery_required'] is False,'input completed');releases=v['execution']['releases'];require(bool(releases) and all(x['verified'] is True and x['keys_down']==[] and x['buttons_down']==[] for x in releases),'input release')
  require(len(list((c/'commands').glob('*.json')))==4 and [read(c/'commands'/f'{i:03d}.json')['op'] for i in range(1,5)]==['observe','mint_many','method','close'],'command order')
  batch=read(c/'replies/002.json')['reply'];require(batch['status']=='minted' and batch['source_sequence']==1 and batch['input_dispatched'] is False and [(v['alias'],v['offset']) for v in batch['minted']]==[('context',[8,8]),('rectangle',[16,16])],'complete exact public batch');
  reviews=[json.loads(x) for x in (c/'primary-decisions.jsonl').read_text().splitlines()];require([x['command'] for x in reviews]==[2,4],'primary review order')
  for i,k in [(1,0),(3,1)]:
   v=read(c/'replies'/f'{i:03d}.json')['reply'];a=v['image_reference'];parts=pathlib.Path(a['path']).parts;rel=pathlib.Path(*parts[parts.index(name)+1:]);require((c/rel).resolve().is_relative_to(c.resolve()),'owned PNG');data=(c/rel).read_bytes();require(v['image_status']=='image','delivered PNG');expected_root=bridge/'images' if i==1 else c/'method-call/images';require((c/rel).resolve().is_relative_to(expected_root.resolve()),'image call root');require(data==base64.b64decode(v['image']['data'],validate=True) and hashlib.sha256(data).hexdigest()==a['sha256']==reviews[k]['image_sha256'],'original primary PNG')
  programs=[read(f)['ops'] for f in bridge.glob('program-*.json')];require(len(programs)==ninputs,'program inventory');click=[ops for ops in programs if any(x['op']=='pointer_button' for x in ops)];require(len(click)==1,'one click');clicks.append(click[0]);require([x for x in click[0] if x['op']=='pointer_move']==[{'op':'pointer_move','frame':'screen_physical_px','x':353,'y':305}],'interior click point');require(read(c/'method-plan.json')['bindings']['select']['offset']==[16,16],'selection offset')
  chords=[x['keys'] for ops in programs for x in ops if x['op']=='key_chord'];require(chords.count(['CTRL','s'])==int(success),'Save count');require(chords.count(['Right'])==(15 if success else (0 if name=='normal-compiled' else 5)),'movement count')
  trace=read(c/'method-trace.json');require([x['predicates']['selected_shape'] for x in trace]==selected,'selection effect trace')
  svg=c/'two-rectangles.svg';tree=ET.parse(svg).getroot();rects=[{k:float(x.get(k)) for k in ('x','y','width','height')} for x in tree.iter('{http://www.w3.org/2000/svg}rect')];require(rects==[{'x':80. if success else 50.,'y':50.,'width':40.,'height':30.}] and not any(x.get('transform') for x in tree.iter()),'saved geometry')
  sha=hashlib.sha256(svg.read_bytes()).hexdigest();require(sha==read(c/'evaluation.json')['svg_sha256'] and read(c/'evaluation.json')['success'] is success,'independent score/hash')
  if not success:require(sha==read(c/'original-svg.json')['sha256'],'unchanged persisted original')
  if name.endswith('compiled') and success:
   g=read(c/'method-raw.json');require(len(g['transitions'])==3 and g['pending_effect'] is None and [e['action'] for e in g['critical_events'] if e['event']=='effect_checked' and e['status']=='succeeded']==['select','move','save'],'graph semantic completion')
  if name.endswith('compiled') and not success:
   g=read(c/'method-raw.json');require(len(g['transitions'])==ninputs and isinstance(g.get('pending_effect'),dict) and g['pending_effect'].get('action')=='move','graph prefix and pending effect')
  cleanup=read(c/'cleanup.json');require(cleanup['host_exit']==0 and cleanup['all_owned_processes_terminal'] is True,'terminal');require(sorted(x['name'] for x in cleanup['children'])==['inkscape','openbox','xvfb'] and all(type(x['returncode']) is int for x in cleanup['children']),'owned child termination records');release=read(c/'replies/004.json')['reply']['release'];require(release['verified'] is True and release['keys_down']==[] and release['buttons_down']==[],'close release')
  rows.append({'case':name,'task_success':success,'outcome':m['outcome'],'reason':reason,'input_programs':ninputs,'emissions':emissions,'captures':len(list(bridge.glob('observation-*.json'))),'commands':4,'primary_images':2,'persisted_x':80 if success else 50,'local_method_ms':m['elapsed_ns']/1e6})
 require(all(x==clicks[0] for x in clicks),'click programs differ')
 return {'status':'PASS_SCOPED_CORRECTNESS_HOLD_EFFICIENCY','normal_tasks_succeeded':2,'normal_tasks_attempted':2,'control_noSave_stops':2,'controls_not_completed_tasks':True,'pending_cases':[],'cases':rows,'scope':'actual public Python batch owner and same bridge; scoped normal2/2 and noSave controls2/2; prior adapter root mismatch preserved; no MCP transport or efficiency/default qualification'}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
