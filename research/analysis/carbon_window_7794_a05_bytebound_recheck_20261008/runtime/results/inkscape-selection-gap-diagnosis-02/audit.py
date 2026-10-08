import pathlib,json,hashlib,base64,xml.etree.ElementTree as ET
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parent
def require(v,m):
 if not v:raise ValueError(m)
def read(p):return json.loads(p.read_text())
def audit():
 for n,h in read(ROOT/'FROZEN.json')['files'].items():require(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h,'frozen '+n)
 rows=[]
 for name,gap in [('immediate',0),('selection-gap100',100)]:
  c=ROOT/name;cleanup=read(c/'cleanup.json');require(cleanup['host_exit']==0 and cleanup['all_owned_processes_terminal'] is True,'terminal')
  require(all(not pathlib.Path('/proc',str(x['pid'])).exists() for x in cleanup['children']),'owned PID still present')
  close=read(c/'replies/004.json')['reply']['release'];require(close['verified'] is True and close['keys_down']==[] and close['buttons_down']==[],'close release')
  m=read(c/'method-common.json');require(m['outcome']=='SAFE_YIELD' and m['reason']=='effect_failed' and m['inputs']==1 and m['completed_transitions']==1,'failure stop')
  inp=read(c/'method-inputs.json');require(len(inp)==1 and inp[0]['status']=='completed' and inp[0]['execution']['program_emissions']==34,'delivery count')
  require([x['stage'] for x in inp[0]['guard_checks']]==['before_admission','before_focus'],'guards')
  require(all(x['verified'] is True and x['keys_down']==[] and x['buttons_down']==[] for x in inp[0]['execution']['releases']),'input releases')
  programs=list((c/'bridge').glob('program-*.json'));require(len(programs)==1,'no save/replay')
  ops=read(programs[0])['ops'];expected=[{'op':'key_chord','keys':['CTRL','A']}]+([{'op':'wait_update','timeout_ms':gap}] if gap else [])+[{'op':'key_chord','keys':['Right']}]*15+[{'op':'wait_update','timeout_ms':100}]
  require(ops[1:-1]==expected and ops[0]['op']=='focus' and ops[-1]['op']=='release_all','exact gap intervention')
  for i in (1,3):
   v=read(c/'replies'/f'{i:03d}.json')['reply'];a=v['image_reference'];f=c/'bridge/images'/pathlib.Path(a['path']).name;data=f.read_bytes()
   require(data==base64.b64decode(v['image']['data'],validate=True) and hashlib.sha256(data).hexdigest()==a['sha256'],'image originals')
   im=Image.open(f).convert('RGB');left=list(im.crop((340,300,350,315)).getdata());right=list(im.crop((399,300,404,315)).getdata())
   require(sum(r>=240 and g<=16 and b<=16 for r,g,b in left)/len(left)>=.98 and sum(min(x)>=240 for x in right)/len(right)>=.98,'independent original pixel position')
  tree=ET.parse(c/'two-rectangles.svg').getroot();rects=[{k:float(x.get(k)) for k in ('x','y','width','height')} for x in tree.iter('{http://www.w3.org/2000/svg}rect')]
  require(rects==[{'x':50.,'y':50.,'width':40.,'height':30.}] and not any(x.get('transform') for x in tree.iter()),'persisted geometry')
  require(hashlib.sha256((c/'two-rectangles.svg').read_bytes()).hexdigest()==read(c/'original-svg.json')['sha256'],'persisted unchanged')
  require(read(c/'evaluation.json')['success'] is False,'independent task unsuccessful')
  rows.append({'case':name,'selection_gap_ms':gap,'outcome':m['outcome'],'reason':m['reason'],'local_method_ms':m['elapsed_ns']/1e6,'persisted_x':50,'task_success':False,'input_programs':1,'program_emissions':34,'save_programs':0})
 return {'status':'PASS_RETAINED_FAILED_DIAGNOSIS','normal_tasks_succeeded':0,'normal_tasks_attempted':2,'cases':rows,'scope':'100ms gap insufficient in these allocations; mechanism/performance/token benefit unproven'}
if __name__=='__main__':print(json.dumps(audit(),indent=2))
