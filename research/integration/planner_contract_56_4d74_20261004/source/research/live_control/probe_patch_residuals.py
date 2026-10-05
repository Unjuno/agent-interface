"""Offline diagnostic: raw versus trimmed errors and declared local search.

Known image pairs only; this is not a controller benchmark or identity proof.
"""
import hashlib,json,time
from pathlib import Path
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
out=HERE/'results/patch-residuals-01';out.mkdir(exist_ok=False)
cases=[('servo-distractor-02/red',2,0),('servo-distractor-02/blue',3,12),('servo-distractor-03/blue',2,0)]
rows=[];inputs=set()
for name,seq,reference_dx in cases:
    root=HERE/'results'/name
    events=[json.loads(x) for x in (root/'events.jsonl').read_text().splitlines()]
    source=next(r for r in events if r['event']=='observation' and r['sequence']==1)
    current=next(r for r in events if r['event']=='observation' and r['sequence']==seq)
    paths=[root/Path(r['image']).name for r in (source,current)];inputs.update(paths)
    arrays=[]
    for p in paths:
        with Image.open(p) as im:arrays.append(np.array(im.convert('RGB'),dtype=np.int16))
    x,y,w,h=json.loads((root/'result.json').read_text())['source_box'];patch=arrays[0][y:y+h,x:x+w]
    start=time.perf_counter_ns();scores={trim:[] for trim in (0,.1,.2)}
    for dy in range(-32,33):
        for dx in range(-32,33):
            residual=np.abs(arrays[1][y+dy:y+dy+h,x+dx:x+dx+w]-patch).mean(axis=2).ravel()/255
            residual.sort()
            for trim in scores:
                k=max(1,int(len(residual)*(1-trim)));scores[trim].append((float(residual[:k].mean()),dx,dy))
    for trim,all_scores in scores.items():
        for radius in (32,8):
            # Local window is centered on annotated expected position solely to diagnose
            # appearance versus identity. It is NOT an available online estimate.
            allowed=[v for v in all_scores if abs(v[1]-reference_dx)<=radius and abs(v[2])<=radius]
            best,dx,dy=min(allowed)
            rival=min(v[0] for v in allowed if max(abs(v[1]-dx),abs(v[2]-dy))>2)
            actual=next(v[0] for v in all_scores if v[1]==reference_dx and v[2]==0)
            neighbor=next(v[0] for v in all_scores if v[1]==28 and v[2]==0)
            rows.append(dict(case=name,sequence=seq,trim=trim,radius=radius,best_delta=[dx,dy],best_error=best,rival_margin=rival-best,reference_dx=reference_dx,reference_error=actual,neighbor_error=neighbor))
    rows[-1]['diagnostic_total_ms']=(time.perf_counter_ns()-start)/1e6
sources=inputs|{Path(__file__)}
(out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},indent=2)+'\n')
(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows,indent=2))
