from __future__ import annotations
import json, math, statistics, time
from PIL import Image

W,H=140,100; P=8; PX=60; PY=45

def patch_image(jitter=False):
    patch=Image.new('RGB',(P,P)); pix=patch.load()
    for y in range(P):
        for x in range(P):
            pix[x,y]=((x*31+y*7)%256,(x*11+y*29)%256,(x*17+y*13)%256)
    if jitter:
        r,g,b=pix[2,3]; pix[2,3]=((r+1)%256,g,b)
    return patch
SRC=patch_image(False); SRC_BYTES=SRC.tobytes()

def canvas(locations,jitter=False,duplicate=False):
    im=Image.new('RGB',(W,H),(8,12,16)); im.paste(patch_image(jitter),locations[0])
    if duplicate: im.paste(SRC,locations[1])
    return im

def exact_search(image,predicted,radius):
    px,py=predicted; matches=[]
    for y in range(max(0,py-radius),min(image.height-P,py+radius)+1):
        for x in range(max(0,px-radius),min(image.width-P,px+radius)+1):
            if image.crop((x,y,x+P,y+P)).tobytes()==SRC_BYTES:
                matches.append((x,y))
    return matches

def q(v,p):
    s=sorted(v); return s[math.ceil(p*len(s))-1]

results={}
for radius in [0,6,12,24,48,64]:
    dx=min(radius,6) if radius else 0
    im=canvas([(PX+dx,PY)]); vals=[]; out=None
    reps=300 if radius<=24 else 80
    for _ in range(reps):
        t0=time.perf_counter_ns(); out=exact_search(im,(PX,PY),radius); vals.append((time.perf_counter_ns()-t0)/1000)
    results[str(radius)]={'matches':len(out),'resolved':out[0] if len(out)==1 else None,'median_us':statistics.median(vals),'p95_us':q(vals,.95),'candidates_nominal':(2*radius+1)**2}

cases={
 'stable':exact_search(canvas([(PX,PY)]),(PX,PY),12),
 'moved_6':exact_search(canvas([(PX+6,PY)]),(PX,PY),12),
 'one_pixel_render_jitter':exact_search(canvas([(PX+6,PY)],jitter=True),(PX,PY),12),
 'duplicate_same_patch':exact_search(canvas([(PX-6,PY),(PX+6,PY)],duplicate=True),(PX,PY),12),
}
print(json.dumps({'fixture':{'canvas':[W,H],'patch':[P,P],'predicted':[PX,PY]},'latency':results,'cases':{k:{'matches':len(v),'locations':v} for k,v in cases.items()}},indent=2))
