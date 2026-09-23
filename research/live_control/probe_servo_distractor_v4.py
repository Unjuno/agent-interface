"""Pinned real-app two-object pilot. Fixture creation and XML scoring are separate from control."""
import hashlib,json,shutil,time,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from session_v19 import Backend,suite
from executor_v3 import Executor
HERE=Path(__file__).resolve().parent
root=HERE/'results/servo-distractor-04';root.mkdir(exist_ok=False)
rows=[]
for color in ('blue','red'):
    out=root/color;out.mkdir();s=suite.Session();backend=None;engine=None;output=None;events=[]
    original_spawn=s.spawn
    def spawn(args,*pos,**kw):
        if args[0]=='inkscape':
            svg='<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200"><rect id="target" x="50" y="50" width="12" height="10" fill="red"/><rect id="distractor" x="74" y="50" width="12" height="10" fill="'+color+'"/></svg>'
            Path(args[1]).write_text(svg);(out/'fixture.svg').write_text(svg)
        return original_spawn(args,*pos,**kw)
    s.spawn=spawn
    def emit(r):r['emitted_ns']=time.perf_counter_ns();events.append(r)
    def run(name,steps):
        engine.submit(name,steps,backend.sequence,time.perf_counter_ns()+8_000_000_000)
        end=time.monotonic()+10
        while engine.active is not None and time.monotonic()<end:time.sleep(.01)
        assert engine.active is None
        return next(r for r in reversed(events) if r['event']=='terminal')
    try:
        original_ready=suite.red_bbox
        def small_fixture_ready(frame):
            a=np.frombuffer(frame.pixels,np.uint8).reshape(frame.height,frame.width,3)[360:415,580:665]
            return [0,0,1,1] if ((a[:,:,0]>200)&(a[:,:,1]<60)&(a[:,:,2]<60)).sum()>=100 else None
        suite.red_bbox=small_fixture_ready
        try:_,output,_=suite.prepare(s,'inkscape',991012,'unused')
        finally:suite.red_bbox=original_ready
        backend=Backend(s,out,emit);engine=Executor(backend,emit);backend.snapshot('initial',0)
        # Scripted planner identifies the leftmost red component in the declared canvas ROI.
        f=backend.decoder.frame;a=np.frombuffer(f.pixels,np.uint8).reshape(f.height,f.width,3)
        roi=a[360:415,580:665];mask=(roi[:,:,0]>200)&(roi[:,:,1]<60)&(roi[:,:,2]<60)
        columns=np.where(mask.any(axis=0))[0];first=int(columns[0]);last=first
        while last+1<mask.shape[1] and mask[:,last+1].any():last+=1
        ys=np.where(mask[:,first:last+1].any(axis=1))[0]
        x0=580+first;y0=360+int(ys[0]);w=last-first+1;h=int(ys[-1]-ys[0]+1)
        box=[x0-3,y0-3,w+6,h+6];x=x0+w//2;y=y0+h//2
        step=dict(op='pointer_servo',source_sequence=backend.sequence,box=box,target_delta=[12,0],points=[{'x':x,'y':y},{'x':x+6,'y':y}],duration_ms=100,max_corrections=3)
        try:terminal=run('servo',[step])
        except ValueError as exc:
            terminal={'status':'rejected','error':str(exc)}
            events.append(dict(event='probe_rejected',reason=str(exc)))
        assert run('save',[{'op':'chord','modifier':'Control_L','key':'s'},{'op':'settle','quiet_ms':100,'timeout_ms':1200}])['status']=='completed'
        attrs={r.get('id'):{k:r.get(k) for k in ('x','y','width','height','transform')} for r in ET.parse(output).getroot().findall('{http://www.w3.org/2000/svg}rect')}
        target=attrs['target'];other=attrs['distractor'];dx=(float(target['x'])-50)*1.18
        preserved=target['y']=='50' and target['width']=='12' and target['height']=='10' and target['transform'] is None and other==dict(x='74',y='50',width='12',height='10',transform=None)
        row={'distractor_color':color,'source_box':box,'terminal':terminal,'target_dx':dx,'precision_pass':abs(dx-12)<=1,'collateral_preserved':preserved,'saved':attrs,'controller':[r for r in events if r['event']=='servo_feedback']}
        rows.append(row);(out/'result.json').write_text(json.dumps(row,indent=2)+'\n')
    finally:
        if engine:engine.close()
        if backend:backend.close();(out/'owner-events.json').write_text(json.dumps(backend.owner.records,indent=2)+'\n')
        (out/'events.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in events))
        if output and output.exists():shutil.copy2(output,out/'shape.svg')
        s.close();shutil.rmtree(s.tmp)
sources=[Path(__file__),HERE/'session_v19.py',HERE/'session_v15.py',HERE/'patch_servo_v3.py',HERE/'visual_anchor_v3.py',HERE/'input_owner_v9.py',HERE/'pointer_reply_v2.py',HERE/'executor_v3.py']
(root/'sources.json').write_text(json.dumps({str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},indent=2)+'\n')
print(json.dumps(rows,indent=2))
