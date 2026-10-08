import pathlib,json,hashlib,base64,xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parent
def require(v,m):
 if not v:raise ValueError(m)
def read(p):return json.loads(p.read_text())
def verify(root=ROOT):
 for n,h in read(root/'FROZEN.json')['files'].items():require(hashlib.sha256((root/n).read_bytes()).hexdigest()==h,'frozen '+n)
 c=root/'canvas';require([read(c/'commands'/f'{i:03d}.json')['op'] for i in range(1,7)]==['observe','mint','mint_rectangle','method','method','close'],'commands')
 require(len(list((c/'commands').glob('*.json')))==6,'extra command')
 require(read(c/'commands/002.json')['point']==[37,165] and read(c/'commands/003.json')['point']==[338,294],'grounded targets')
 reviews=[json.loads(x) for x in (c/'primary-decisions.jsonl').read_text().splitlines()];require([x['command'] for x in reviews]==[2,5,6],'review order')
 for i,k in [(1,0),(4,1),(5,2)]:
  v=read(c/'replies'/f'{i:03d}.json')['reply'];a=v['image_reference'];data=(c/'bridge/images'/pathlib.Path(a['path']).name).read_bytes()
  require(data==base64.b64decode(v['image']['data'],validate=True) and hashlib.sha256(data).hexdigest()==a['sha256']==reviews[k]['image_sha256'],'primary image bytes')
 selected=read(c/'selection-input.json');inputs=[selected,*read(c/'method-inputs.json')];require(len(inputs)==3,'three input programs')
 for v in inputs:
  require(v['status']=='completed' and v['recovery_required'] is False,'completed delivery')
  require([x['stage'] for x in v['guard_checks']][:2]==['before_admission','before_focus'],'minimum guard stages')
  releases=v['execution']['releases'];require(bool(releases) and all(x['verified'] is True and x['keys_down']==[] and x['buttons_down']==[] for x in releases),'input release')
 programs=[read(f)['ops'] for f in (c/'bridge').glob('program-*.json')];require(len(programs)==3,'program inventory')
 tails=[[x for x in ops if x['op'] not in ('focus','release_all')] for ops in programs]
 move=[{'op':'key_chord','keys':['Right']}]*15+[{'op':'wait_update','timeout_ms':100}]
 save=[{'op':'key_chord','keys':['CTRL','s']},{'op':'wait_update','timeout_ms':100}]
 require(move in tails and save in tails,'move/save exact suffix')
 clicks=[ops for ops in programs if any(x['op']=='pointer_button' for x in ops)];require(len(clicks)==1,'one explicit click')
 require([x['down'] for x in clicks[0] if x['op']=='pointer_button']==[True,False] and all(x.get('button')=='left' for x in clicks[0] if x['op']=='pointer_button'),'left click')
 require(not any(x['op']=='key_chord' for x in clicks[0]),'no hidden selection chord')
 m=read(c/'method-common.json');require(m['outcome']=='TASK_SUCCEEDED' and m['completed_transitions']==2 and m['inputs']==2,'method completion')
 trace=read(c/'method-trace.json');require([x['predicates']['moved_shape'] for x in trace]==[False,True,True],'pixel effect ordering')
 require(read(c/'replies/005.json')['started_ns']>read(c/'replies/004.json')['ended_ns'],'separate calls')
 svg=c/'two-rectangles.svg';tree=ET.parse(svg).getroot();rects=[{k:float(x.get(k)) for k in ('x','y','width','height')} for x in tree.iter('{http://www.w3.org/2000/svg}rect')]
 require(rects==[{'x':80.,'y':50.,'width':40.,'height':30.}] and not any(x.get('transform') for x in tree.iter()),'independent persisted geometry')
 require(tree.get('viewBox')=='0 0 400 240' and [x.get('fill') for x in tree.iter('{http://www.w3.org/2000/svg}rect')]==['#ff0000'],'document/shape integrity')
 require(hashlib.sha256(svg.read_bytes()).hexdigest()==read(c/'evaluation.json')['svg_sha256'] and read(c/'evaluation.json')['success'] is True,'saved hash/score')
 cleanup=read(c/'cleanup.json');require(cleanup['host_exit']==0 and cleanup['all_owned_processes_terminal'] is True,'terminal')
 release=read(c/'replies/006.json')['reply']['release'];require(release['verified'] is True and release['keys_down']==[] and release['buttons_down']==[],'close release')
 return {'status':'PASS_SCOPED_ORDINARY_CANVAS_RECIPE','task_successes':1,'task_attempts':1,'input_programs':3,'program_emissions':[v['execution']['program_emissions'] for v in inputs],'commands':6,'primary_original_image_files':3,'local_click_ms':read(c/'selection-common.json')['elapsed_ns']/1e6,'local_move_check_save_ms':m['elapsed_ns']/1e6,'svg_sha256':hashlib.sha256(svg.read_bytes()).hexdigest(),'scope':'one ordinary callback task; no compiled transfer, causal mechanism, token/cost or speed promotion'}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
