import pathlib,json,hashlib,base64,xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parent
def require(v,m):
 if not v:raise ValueError(m)
def read(p):return json.loads(p.read_text())
def verify(root=ROOT):
 for name,h in read(root/'FROZEN.json')['files'].items():require(hashlib.sha256((root/name).read_bytes()).hexdigest()==h,'frozen '+name)
 normalized=[];rows=[]
 for name in ['positive-ordinary','positive-compiled']:
  c=root/name;cleanup=read(c/'cleanup.json');require(cleanup['host_exit']==0 and cleanup['all_owned_processes_terminal'] is True,'terminal')
  require([x['returncode'] for x in cleanup['children']]==[-15,0,0],'children')
  require(len(list((c/'commands').glob('*.json')))==4,'command inventory')
  require([read(c/'commands'/f'{i:03d}.json')['op'] for i in range(1,5)]==['observe','mint','method','close'],'command order')
  mint=read(c/'commands/002.json');require(mint['point']==[37,165] and mint['source_sequence']==1,'grounding')
  reviews=[json.loads(x) for x in (c/'primary-decisions.jsonl').read_text().splitlines()];require([x['command'] for x in reviews]==[2,4],'primary reviews')
  for i,j in [(1,0),(3,1)]:
   v=read(c/'replies'/f'{i:03d}.json')['reply'];a=v['image_reference'];data=base64.b64decode(v['image']['data'],validate=True)
   require(hashlib.sha256(data).hexdigest()==a['sha256']==reviews[j]['review']['image_sha256'],'primary image')
   require((c/'bridge/images'/pathlib.Path(a['path']).name).read_bytes()==data,'original artifact')
  close=read(c/'replies/004.json')['reply'];require(close['release']['verified'] is True and close['release']['keys_down']==[] and close['release']['buttons_down']==[],'close release')
  m=read(c/'method-common.json');require(m['outcome']=='SAFE_YIELD' and m['reason']=='effect_failed' and m['completed_transitions']==1 and m['inputs']==1,'effect stop')
  inputs=read(c/'method-inputs.json');require(len(inputs)==1,'input count');actual=inputs[0];e=actual['execution']
  require(actual['status']=='completed' and actual['recovery_required'] is False and e['program_emissions']==34,'input terminal/count')
  require(e['releases'] and all(x.get('verified') is True and x.get('keys_down')==[] and x.get('buttons_down')==[] for x in e['releases']),'input release')
  require([x['stage'] for x in actual['guard_checks']]==['before_admission','before_focus'],'guard stages')
  plans=read(c/'method-plan.json');normalized.append(plans['bindings']);require(set(plans['bindings'])=={'move','save'},'bindings')
  programs=list((c/'bridge').glob('program-*.json'));require(len(programs)==1,'Save or replay program');p=read(programs[0]);require(len(p['ops'])==19 and [x['keys'] for x in p['ops'] if x['op']=='key_chord']==[['CTRL','A']]+[['Right']]*15,'exact input tail')
  tree=ET.parse(c/'two-rectangles.svg').getroot();require(not any(x.get('transform') for x in tree.iter()),'transform')
  rects=[{k:float(x.get(k)) for k in ['x','y','width','height']} for x in tree.iter('{http://www.w3.org/2000/svg}rect')];require(rects==[{'x':50.0,'y':50.0,'width':40.0,'height':30.0}],'persisted original')
  require(hashlib.sha256((c/'two-rectangles.svg').read_bytes()).hexdigest()==read(c/'original-svg.json')['sha256'],'saved file changed')
  require(read(c/'evaluation.json')['success'] is False,'false independent success')
  trace=read(c/'method-trace.json');require(len(trace)==2 and all(x['predicates']['initial_shape'] is True and x['predicates']['moved_shape'] is False for x in trace),'pixel effect')
  if name.endswith('compiled'):
   graph=read(c/'method-raw.json');require(graph['pending_effect']['action']=='move' and len(graph['transitions'])==1,'graph prefix/pending effect')
  rows.append({'case':name,'outcome':m['outcome'],'reason':m['reason'],'local_ms':m['elapsed_ns']/1e6,'program_emissions':34,'saved_x':50,'intended_x':80,'Save_programs':0})
 require(normalized[0]==normalized[1],'paired programs differ')
 for name in ['short-compiled','short-ordinary']:require(not (root/name).exists(),'censored case executed')
 return {'status':'PASS_EVIDENCE_OF_FAILED_TASK','normal_task_successes':0,'normal_attempts':2,'normal_commands':8,'normal_original_image_files':4,'cases':rows,'scope':'retained evidence only; graph success/guarded transfer/performance NOT qualified'}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
