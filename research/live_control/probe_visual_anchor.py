"""Predeclared anchor fixture checks plus historical real-app replay, no input."""
import hashlib,json,time
from pathlib import Path
import numpy as np
from PIL import Image
from visual_anchor import VisualAnchor
HERE=Path(__file__).resolve().parent
out=HERE/'results/visual-anchor-01';out.mkdir(exist_ok=False)
rows=[]
rng=np.random.default_rng(991006)
patch=rng.integers(0,256,(16,20,3),dtype=np.uint8)
base=np.full((100,140,3),240,dtype=np.uint8);base[35:51,45:65]=patch
anchor=VisualAnchor(base,[45,35,20,16],1,'fixture',radius=32)
for name,dx,dy,duplicate,remove in [('right',19,0,False,False),('diagonal',-21,17,False,False),('duplicate',19,0,True,False),('lost',0,0,False,True)]:
    a=np.full_like(base,240)
    if not remove:a[35+dy:51+dy,45+dx:65+dx]=patch
    if duplicate:a[15:31,25:45]=patch
    t=time.perf_counter_ns();v=anchor.locate(a,2,'fixture');elapsed=(time.perf_counter_ns()-t)/1e6
    expected='lost' if remove else 'ambiguous' if duplicate else 'matched'
    assert v['status']==expected,v
    if expected=='matched':assert v['delta']==[dx,dy],v
    rows.append({'case':name,'expected':expected,'result':v,'ms':elapsed})
assert anchor.locate(base,2,'other')['status']=='invalid_frame'
assert anchor.locate(base,1,'fixture')['status']=='same_observation'
try:VisualAnchor(np.full_like(base,240),[45,35,20,16],1,'fixture')
except ValueError:pass
else:raise AssertionError('flat patch accepted')
# Declared historical replay region includes the object boundary, not only flat fill.
source=HERE/'results/guided-pointer-03/001.png'
with Image.open(source) as im:a=np.array(im.convert('RGB'))
real=VisualAnchor(a,[592,369,56,44],1,'inkscape',radius=32)
for n in (2,3):
    path=HERE/f'results/guided-pointer-03/{n:03d}.png'
    with Image.open(path) as im:b=np.array(im.convert('RGB'))
    t=time.perf_counter_ns();v=real.locate(b,n,'inkscape')
    rows.append({'case':f'historical_frame_{n}','result':v,'ms':(time.perf_counter_ns()-t)/1e6})
sources=[Path(__file__),HERE/'visual_anchor.py',source]+[HERE/f'results/guided-pointer-03/{n:03d}.png' for n in (2,3)]
(out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},indent=2)+'\n')
(out/'results.json').write_text(json.dumps({'numpy':np.__version__,'seed':991006,'rows':rows,'boundary_checks':3},indent=2)+'\n')
print(json.dumps(rows,indent=2))
