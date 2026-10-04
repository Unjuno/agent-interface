"""Actual X11 perturbation pilot: opaque child overlays, separate from controller.

Overlays model same-surface appearance changes; they are not Inkscape objects.
"""
import hashlib,json,shutil,time,xml.etree.ElementTree as ET
from pathlib import Path
from Xlib import X,display
from session_v20 import Backend,suite
from executor_v3 import Executor
HERE=Path(__file__).resolve().parent
root=HERE/'results/servo-occlusion-01';root.mkdir(exist_ok=False)
rows=[]
for case in ('partial','hidden','replacement'):
    out=root/case;out.mkdir();s=suite.Session();backend=None;engine=None;output=None;events=[];overlays=[];perturb=None
    def emit(r):r['emitted_ns']=time.perf_counter_ns();events.append(r)
    def run(name,steps):
        engine.submit(name,steps,backend.sequence,time.perf_counter_ns()+8_000_000_000)
        end=time.monotonic()+10
        while engine.active is not None and time.monotonic()<end:time.sleep(.01)
        assert engine.active is None
        return next(r for r in reversed(events) if r['event']=='terminal')
    try:
        _,output,_=suite.prepare(s,'inkscape',991015,'unused');backend=Backend(s,out,emit);engine=Executor(backend,emit);backend.snapshot('initial',0)
        perturb=display.Display(s.name);parent=perturb.create_resource_object('window',backend.observed_pointer['surface'])
        gx,gy=backend.observed_pointer['geometry'][:2]
        original_snapshot=backend.snapshot;injected=False
        def snapshot(identifier,index):
            global_unused=None
            nonlocal_placeholder=None
            if identifier=='servo' and not overlays:
                specs=[(596,373,4,36,0xffffff)] if case=='partial' else [(592,369,56,44,0xffffff)]
                if case=='replacement':specs.append((620,373,48,36,0xff0000))
                for x,y,w,h,pixel in specs:
                    win=parent.create_window(x-gx,y-gy,w,h,0,X.CopyFromParent,X.InputOutput,X.CopyFromParent,background_pixel=pixel,override_redirect=True)
                    win.map();overlays.append(win)
                perturb.sync();time.sleep(.04)
                emit(dict(event='environment_overlay',case=case,rectangles=specs))
            return original_snapshot(identifier,index)
        backend.snapshot=snapshot
        step=dict(op='pointer_servo',source_sequence=backend.sequence,box=[592,369,56,44],target_delta=[24,0],points=[{'x':619,'y':390},{'x':631,'y':390}],duration_ms=100,max_corrections=3)
        terminal=run('servo',[step]);backend.snapshot=original_snapshot
        for win in overlays:win.destroy()
        perturb.sync();time.sleep(.08)
        assert run('save',[{'op':'chord','modifier':'Control_L','key':'s'},{'op':'settle','quiet_ms':100,'timeout_ms':1200}])['status']=='completed'
        rect=ET.parse(output).getroot().find('{http://www.w3.org/2000/svg}rect');actual={k:rect.get(k) for k in ('x','y','width','height','transform')}
        dx=(float(actual['x'])-50)*1.18
        row=dict(case=case,terminal=terminal,actual=actual,saved_dx=dx,precision_pass=abs(dx-24)<=1,controller=[r for r in events if r['event']=='servo_feedback'])
        rows.append(row);(out/'result.json').write_text(json.dumps(row,indent=2)+'\n')
    finally:
        if engine:engine.close()
        if backend:backend.close();(out/'owner-events.json').write_text(json.dumps(backend.owner.records,indent=2)+'\n')
        if perturb:perturb.close()
        (out/'events.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in events))
        if output and output.exists():shutil.copy2(output,out/'shape.svg')
        s.close();shutil.rmtree(s.tmp)
sources=[Path(__file__),HERE/'session_v20.py',HERE/'session_v15.py',HERE/'patch_servo_v4.py',HERE/'visual_anchor_v2.py',HERE/'visual_anchor_v3.py',HERE/'input_owner_v9.py',HERE/'pointer_reply_v2.py',HERE/'executor_v3.py']
(root/'sources.json').write_text(json.dumps({str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},indent=2)+'\n')
print(json.dumps(rows,indent=2))
