"""Archived Calc transition diagnostics and passive collector controls."""
import copy,hashlib,json
from pathlib import Path
from PIL import Image,ImageChops
from decision_pair_v1 import collect
H=Path(__file__).resolve().parent;R=H/'results/decision-pair-controls-01';R.mkdir(exist_ok=False)
P=H/'results/shared-phased-calc-01';rows=json.loads((P/'turns.json').read_text(encoding='utf-8'))
row=rows[1];old=row['source'];new=row['fresh']
initial={'observation':old,'image':str(P/'runtime'/Path(old['image']).name)}
fresh={'observation':new,'image':str(P/'runtime'/Path(new['image']).name),'clock':row['clock']}
with Image.open(initial['image']) as a,Image.open(fresh['image']) as b:
 diff=ImageChops.difference(a,b);crop=diff.crop(row['contract']['box'])
 counts=[sum(any(crop.getpixel((x,y))) for x in range(crop.width)) for y in range(crop.height)]
 diagnostic={'source_image':old['image'],'fresh_image':new['image'],'patch_box':row['contract']['box'],
             'changed_patch_pixels':sum(counts),'patch_changed_pixels_per_row':counts,
             'full_diff_bbox':diff.getbbox(),'binding_equal':old['pointer_binding']==new['pointer_binding'],
             'scope':'actual pixel changes; no claim of app-internal cause'}

def sample(number, image):
 value=copy.deepcopy(fresh);value['observation']['sequence']+=number
 value['observation']['capture_ns']+=number*1_000_000
 value['clock']['sequence']=value['observation']['sequence'];value['clock']['runtime_ns']=value['observation']['capture_ns']+1_000_000
 value['image']=image
 return value

cases=[]
def run(name, observations, status, count):
 seen=[]
 def capture():
  v=observations[len(seen)];seen.append(v);return v
 result=collect(initial,capture)
 assert result['status']==status and len(seen)==count
 assert result['observation']==seen[-1]['observation']
 cases.append({'name':name,'result':result})
run('archived_transition_then_equal_synthetic_sample',[fresh,sample(1,fresh['image'])],'received_pair_equal',2)
run('alternating_frames_bound',[fresh,sample(1,initial['image']),sample(2,fresh['image'])],'sample_limit',3)
held=[sample(i,fresh['image']) for i in range(3)]
for v in held:v['observation']['input_state_before']['owned_keycodes']=[50]
run('held_input_cannot_match',held,'sample_limit',3)
stale=[copy.deepcopy(fresh) for _ in range(3)]
for v in stale:v['clock']['runtime_ns']=v['observation']['capture_ns']+2_000_000_000
run('stale_cannot_match',stale,'sample_limit',3)
try:collect(initial,lambda:(_ for _ in ()).throw(AssertionError('unexpected capture')),0)
except ValueError:pass
else:raise AssertionError('invalid bound accepted')
sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),H/'decision_pair_v1.py',P/'turns.json',Path(initial['image']),Path(fresh['image'])]}
(R/'result.json').write_text(json.dumps({'sources':sources,'diagnostic':diagnostic,'cases':cases,'invalid_bound_presend':True},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'diagnostic':diagnostic,'cases':len(cases),'invalid_bound_presend':True},indent=2))
