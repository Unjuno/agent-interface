import pathlib,json,hashlib,base64,xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parent
def require(v,m):
 if not v:raise ValueError(m)
def read(p):return json.loads(p.read_text())
def verify(root=ROOT):
 for n,h in read(root/'FROZEN.json')['files'].items():require(hashlib.sha256((root/n).read_bytes()).hexdigest()==h,'frozen '+n)
 rows=[]
 for row in read(root/'schedule.json'):
  c=root/row['case'];positive=row['steps']==15;method=read(c/'method-common.json');inputs=[read(c/'selection-input.json'),*read(c/'method-inputs.json')]
  require(method['outcome']==('TASK_SUCCEEDED' if positive else 'SAFE_YIELD') and method['reason']==('method_complete' if positive else 'effect_unavailable'),'outcome')
  require(len(inputs)==(3 if positive else 2),'input inventory')
  require([v['execution']['program_emissions'] for v in inputs]==([3,30,4] if positive else [3,10]),'program emission counts')
  for v in inputs:
   require(v['status']=='completed' and v['recovery_required'] is False,'completed input')
   releases=v['execution']['releases'];require(bool(releases) and all(x['verified'] is True and x['keys_down']==[] and x['buttons_down']==[] for x in releases),'input release')
  require(len(list((c/'commands').glob('*.json')))==6 and [read(c/'commands'/f'{i:03d}.json')['op'] for i in range(1,7)]==['observe','mint','mint_rectangle','method','method','close'],'commands')
  reviews=[json.loads(x) for x in (c/'primary-decisions.jsonl').read_text().splitlines()];require([x['command'] for x in reviews]==[2,5,6],'reviews')
  for i,k in [(1,0),(4,1),(5,2)]:
   v=read(c/'replies'/f'{i:03d}.json')['reply'];a=v['image_reference'];data=(c/'bridge/images'/pathlib.Path(a['path']).name).read_bytes();require(data==base64.b64decode(v['image']['data'],validate=True) and hashlib.sha256(data).hexdigest()==a['sha256']==reviews[k]['image_sha256'],'original image')
  programs=[read(f)['ops'] for f in (c/'bridge').glob('program-*.json')];require(len(programs)==len(inputs),'extra program')
  tails=[[x for x in ops if x['op'] not in ('focus','release_all')] for ops in programs];move=[{'op':'key_chord','keys':['Right']}]*row['steps']+[{'op':'wait_update','timeout_ms':100}];save=[{'op':'key_chord','keys':['CTRL','s']},{'op':'wait_update','timeout_ms':100}];require(move in tails and (save in tails)==positive,'exact move/Save')
  svg=c/'two-rectangles.svg';tree=ET.parse(svg).getroot();rects=[{k:float(x.get(k)) for k in ('x','y','width','height')} for x in tree.iter('{http://www.w3.org/2000/svg}rect')];require(rects==[{'x':80. if positive else 50.,'y':50.,'width':40.,'height':30.}] and not any(x.get('transform') for x in tree.iter()),'independent saved geometry')
  sha=hashlib.sha256(svg.read_bytes()).hexdigest();require(read(c/'evaluation.json')['success'] is positive and sha==read(c/'evaluation.json')['svg_sha256'],'score/hash')
  if not positive:require(sha==read(c/'original-svg.json')['sha256'],'negative persisted original')
  trace=read(c/'method-trace.json');require([x['predicates']['moved_shape'] for x in trace]==([False,True,True] if positive else [False,'unknown']),'effect gate')
  if row['route']=='compiled':
   g=read(c/'method-raw.json');require(len(g['transitions'])==(2 if positive else 1),'graph prefix')
   if not positive:require(g['pending_effect']['action']=='move','pending effect')
  cleanup=read(c/'cleanup.json');require(cleanup['host_exit']==0 and cleanup['all_owned_processes_terminal'] is True,'cleanup')
  release=read(c/'replies/006.json')['reply']['release'];require(release['verified'] is True and release['keys_down']==[] and release['buttons_down']==[],'close release')
  captures=len(list((c/'bridge').glob('observation-*.json')));require(captures==(14 if positive else 11),'capture count')
  rows.append({'case':row['case'],'success':positive,'programs':len(inputs),'captures':captures,'emissions':sum(x['execution']['program_emissions'] for x in inputs),'saved_sha256':sha})
 require(rows[0]['saved_sha256']==rows[1]['saved_sha256'] and rows[2]['saved_sha256']==rows[3]['saved_sha256'],'pair persisted bytes')
 return {'status':'PASS_SCOPED_CANVAS_PREPARED_TRANSFER_EFFICIENCY_HOLD','cases':rows,'scope':'retained evidence only; no model usage/speed gain'}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
