"""Fresh Inkscape documents; mutations and persisted SVG oracle are harness-only.
Reference/current surfaces are explicitly rebound. No mutation after admission.
"""
from pathlib import Path
import argparse, contextlib, json, os, signal, subprocess, sys, time
import numpy as np
from common import desktop,context,Inputs,screenshot,write,sha
from oracle import svg_snapshot


def scene(seed,scenario):
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="700" viewBox="0 0 1000 700"><rect id="background" width="1000" height="700" fill="white"/>'
    for i in range(6):
        for j in range(5):
            x=30+i*150;y=40+j*125
            svg+=f'<g id="cell{i}-{j}" fill="none" stroke="black" stroke-width="2"><rect id="rect{i}-{j}" x="{x}" y="{y}" width="120" height="90"/><path id="path{i}-{j}" d="M{x+10},{y+10+j*5} L{x+90-i*5},{y+80} L{x+110},{y+10+i*4} Z"/></g><text id="text{i}-{j}" x="{x+5}" y="{y+35}" font-size="20">ID{i}-{j}-{seed+137*i+53*j}</text>'
    svg+='<rect id="clear-panel" x="360" y="300" width="260" height="100" fill="white"/>'
    def circle(ident,x):return f'<circle id="{ident}" cx="{x}" cy="350" r="20" fill="#f000b0"/>'
    if scenario in ('stable','duplicate'):svg+=circle('task-target',460)
    if scenario=='moved_decoy':svg+=circle('task-target',560)
    if scenario=='duplicate':svg+=circle('decoy',560)
    if scenario in ('moved_decoy','replaced_square'):svg+='<rect id="decoy" x="440" y="330" width="40" height="40" fill="#f000b0"/>'
    return svg+'</svg>'


def ready(s,source,path,events):
    app=s.spawn(['inkscape',str(path)],stdout=open(path.with_suffix('.stdout'),'w'),stderr=open(path.with_suffix('.stderr'),'w'))
    s.wait_window(path.name,10);time.sleep(.6);ctx=context(s,path.name)
    receipts=[];last=None;stable=0;deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        f=s.d.get_input_focus().focus;fid=getattr(f,'id',0);node=f;inside=False
        try:
            for _ in range(32):
                if node.id==ctx['surface']:inside=True;break
                if node.id==s.d.screen().root.id:break
                node=node.query_tree().parent
        except Exception:inside=False
        receipts.append(dict(time_ns=time.perf_counter_ns(),focus=fid,inside=inside))
        stable=stable+1 if fid==last and inside and fid!=ctx['surface'] else 0;last=fid
        if stable>=2:break
        time.sleep(.10)
    else:raise RuntimeError('GTK canvas focus not stable')
    ctx['focus']=fid;x,y,w,h=ctx['geometry'];box=[x+70,y+130,w-140,h-240]
    inp=Inputs(source,ctx,events)
    inp.press('Escape');inp.press('F1');inp.press('5');time.sleep(.2)
    inp.press(['Control_L','s']);time.sleep(.25)
    s.d.screen().root.warp_pointer(3,3);s.d.sync()
    return app,ctx,box,inp,receipts


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True)
    p.add_argument('--scenario',choices=['stable','moved_decoy','replaced_square','missing','duplicate'],required=True)
    p.add_argument('--mode',choices=['center','footprint'],required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--pan',type=int,required=True)
    a=p.parse_args();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=False);s=inp=None
    score=dict(scenario=a.scenario,mode=a.mode,seed=a.seed,pan=a.pan,model_calls=0);events=[]
    try:
        with open(out/'startup.stdout','w') as log,contextlib.redirect_stdout(log):s=desktop(a.source)
        refpath=out/'reference-board.svg';refpath.write_text(scene(a.seed,'stable'))
        refapp,rctx,rbox,inp,ready1=ready(s,a.source,refpath,events)
        ref=screenshot(s.name,rbox);ref.save(out/'reference.png');arr=np.asarray(ref)
        mask=(arr[:,:,0]>220)&(arr[:,:,1]<20)&(arr[:,:,2]>150)&(arr[:,:,2]<200);yy,xx=np.where(mask)
        if len(xx)<30:raise RuntimeError('source footprint not visible')
        point=[float(xx.mean()),float(yy.mean())];cx,cy=[int(round(v)) for v in point]
        radius=max(int(np.max(abs(xx-cx))),int(np.max(abs(yy-cy))))+5
        if not 7<=radius<=40:raise RuntimeError('unsupported source footprint size')
        ref.crop((cx-radius,cy-radius,cx+radius+1,cy+radius+1)).save(out/'template.png')
        inp.close();score['reference_owner_records']=inp.owner.records;inp=None
        os.killpg(refapp.pid,signal.SIGTERM);refapp.wait(timeout=3);time.sleep(.2)
        path=out/'current-board.svg';path.write_text(scene(a.seed,a.scenario));(out/'authored-current.svg').write_bytes(path.read_bytes())
        app,ctx,box,inp,ready2=ready(s,a.source,path,events)
        score.update(reference_focus_receipts=ready1,current_focus_receipts=ready2,reference_context=rctx,current_context=ctx)
        for _ in range(abs(a.pan)):inp.press(['Control_L','Right' if a.pan>0 else 'Left'],.04,.18,'setup_pan')
        inp.close();score['setup_owner_records']=inp.owner.records;inp=None
        (out/'before.svg').write_bytes(path.read_bytes());screenshot(s.name,box).save(out/'current-before.png')
        c=dict(mode=a.mode,context=ctx,box=box,reference=str(out/'reference.png'),template=str(out/'template.png'),point=point)
        write(out/'config.json',c)
        t0=time.perf_counter_ns();r=subprocess.run([sys.executable,str(Path(__file__).with_name('controller.py')),'--source',a.source,'--config',str(out/'config.json'),'--out',str(out/'controller')],capture_output=True,text=True,timeout=20)
        score['controller_wall_ns']=time.perf_counter_ns()-t0;score['controller_exit_code']=r.returncode
        (out/'controller.stdout').write_text(r.stdout);(out/'controller.stderr').write_text(r.stderr);time.sleep(.25)
        before,ar=svg_snapshot(out/'before.svg');after,br=svg_snapshot(path)
        lost=sorted(set(before)-set(after));added=sorted(set(after)-set(before));changed=sorted(k for k in before.keys()&after.keys() if before[k]!=after[k]);unchanged=path.read_bytes()==(out/'before.svg').read_bytes()
        trace=json.loads((out/'controller/trace.json').read_text());pointers=[e for e in trace['events'] if e['kind']=='pointer'];mutations=[e for e in trace['events'] if e['kind']=='input' and e['purpose'] in ('delete_target','save_document')]
        expected_edit=a.scenario in ('stable','moved_decoy')
        ok=(lost==['task-target'] and not added and not changed and ar==br) if expected_edit else (unchanged and not pointers and not mutations)
        score.update(independent_success=bool(ok),expected_edit=expected_edit,removed_ids=lost,added_ids=added,changed_ids=changed,canvas_unchanged=ar==br,bytes_unchanged=unchanged,decision=trace['decision'],pointer_actions=len(pointers),mutation_actions=len(mutations),observations=sum('image' in e for e in trace['events']),wrong_target_deleted='decoy' in lost)
        screenshot(s.name,box).save(out/'final.png')
    except Exception as exc:
        score['error']=repr(exc)
        if s:
            from PIL import ImageGrab
            ImageGrab.grab(xdisplay=s.name).save(out/'failure-root.png')
    finally:
        if inp:inp.close()
        if s:s.close()
        score['setup_events']=events;score['sources']={p.name:sha(p) for p in Path(__file__).parent.glob('*.py')};write(out/'score.json',score)
        print(json.dumps({k:v for k,v in score.items() if k not in ('setup_events','reference_owner_records','setup_owner_records','reference_focus_receipts','current_focus_receipts','sources')}),flush=True)

if __name__=='__main__':main()
