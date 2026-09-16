"""Real Inkscape integration of footprint reacquisition through unmodified adaptive caller v3.

Harness authors scene/mutations and scores persisted SVG. Controller adapters see X11 pixels only.
The candidate differs from comparator only by enabling one no-authority local repair.
"""
from pathlib import Path
import argparse, contextlib, json, math, os, signal, subprocess, threading, time
import cv2, numpy as np
from PIL import Image
from Xlib import X, XK, display
from Xlib.ext import xtest

from common import desktop, context, Inputs, screenshot, write, sha
from oracle import svg_snapshot
from reference_controller_v3 import Matcher
from resolver import resolve, MAX_AGE_NS
from adaptive_acquisition_caller_v3 import run as run_adaptive

cv2.setNumThreads(1)


def scene(seed,scenario):
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="700" viewBox="0 0 1000 700"><rect id="background" width="1000" height="700" fill="white"/>'
    for i in range(6):
        for j in range(5):
            x=30+i*150;y=40+j*125
            svg+=f'<g id="cell{i}-{j}" fill="none" stroke="black" stroke-width="2"><rect id="rect{i}-{j}" x="{x}" y="{y}" width="120" height="90"/><path id="path{i}-{j}" d="M{x+10},{y+10+j*5} L{x+90-i*5},{y+80} L{x+110},{y+10+i*4} Z"/></g><text id="text{i}-{j}" x="{x+5}" y="{y+35}" font-size="20">ID{i}-{j}-{seed+137*i+53*j}</text>'
    svg+='<rect id="clear-panel" x="360" y="300" width="260" height="100" fill="white"/>'
    def circle(ident,x):return f'<circle id="{ident}" cx="{x}" cy="350" r="20" fill="#f000b0"/>'
    if scenario in ('stable','duplicate'): svg+=circle('task-target',460)
    if scenario in ('moved_decoy','post_repair_pan'): svg+=circle('task-target',560)
    if scenario=='duplicate': svg+=circle('decoy',560)
    if scenario in ('moved_decoy','post_repair_pan','replaced_square'):
        svg+='<rect id="decoy" x="440" y="330" width="40" height="40" fill="#f000b0"/>'
    return svg+'</svg>'


def ready(s,source,path,events):
    app=s.spawn(['inkscape',str(path)],stdout=open(path.with_suffix('.stdout'),'w'),stderr=open(path.with_suffix('.stderr'),'w'))
    s.wait_window(path.name,10);time.sleep(.6);ctx=context(s,path.name)
    last=None;stable=0;deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        f=s.d.get_input_focus().focus;fid=getattr(f,'id',0);node=f;inside=False
        try:
            for _ in range(32):
                if node.id==ctx['surface']:inside=True;break
                if node.id==s.d.screen().root.id:break
                node=node.query_tree().parent
        except Exception:inside=False
        stable=stable+1 if fid==last and inside and fid!=ctx['surface'] else 0;last=fid
        if stable>=2:break
        time.sleep(.10)
    else: raise RuntimeError('GTK canvas focus not stable')
    ctx['focus']=fid;x,y,w,h=ctx['geometry'];box=[x+70,y+130,w-140,h-240]
    inp=Inputs(source,ctx,events)
    inp.press('Escape');inp.press('F1');inp.press('5');time.sleep(.2)
    inp.press(['Control_L','s']);time.sleep(.25)
    s.d.screen().root.warp_pointer(3,3);s.d.sync()
    return app,ctx,box,inp


def strict_template_at(image, template, point):
    th,tw=template.shape[:2]; x,y=[int(round(v)) for v in point]; rx,ry=tw//2,th//2
    h,w=image.shape[:2]
    if not(rx<=x<w-rx and ry<=y<h-ry): return False, float('inf')
    crop=image[y-ry:y-ry+th,x-rx:x-rx+tw]
    if crop.shape!=template.shape:return False,float('inf')
    rmse=float(np.sqrt(np.mean((crop.astype(np.float64)-template.astype(np.float64))**2)))
    return rmse<=20.0,rmse


def external_pan(display_name, done):
    d=display.Display(display_name)
    try:
        ctrl=d.keysym_to_keycode(XK.string_to_keysym('Control_L'))
        right=d.keysym_to_keycode(XK.string_to_keysym('Right'))
        xtest.fake_input(d,X.KeyPress,ctrl);d.sync();time.sleep(.02)
        xtest.fake_input(d,X.KeyPress,right);d.sync();time.sleep(.05)
        xtest.fake_input(d,X.KeyRelease,right);xtest.fake_input(d,X.KeyRelease,ctrl);d.sync();time.sleep(.18)
    finally:
        d.close();done.set()


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True)
    p.add_argument('--scenario',choices=['stable_static','stable_pan','moved_decoy','replaced_square','missing','duplicate','post_repair_pan'],required=True)
    p.add_argument('--mode',choices=['baseline','candidate'],required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--pan',type=int,required=True)
    a=p.parse_args();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=False);s=inp=None
    score=dict(scenario=a.scenario,mode=a.mode,seed=a.seed,pan=a.pan,model_calls=0);events=[];journal=[]
    try:
        with open(out/'startup.stdout','w') as log,contextlib.redirect_stdout(log):s=desktop(a.source)
        refpath=out/'reference-board.svg';refpath.write_text(scene(a.seed,'stable'))
        refapp,rctx,rbox,inp=ready(s,a.source,refpath,events)
        ref=screenshot(s.name,rbox);ref.save(out/'reference.png');arr=np.asarray(ref)
        mask=(arr[:,:,0]>220)&(arr[:,:,1]<20)&(arr[:,:,2]>150)&(arr[:,:,2]<200);yy,xx=np.where(mask)
        if len(xx)<30: raise RuntimeError('source footprint not visible')
        source_point=[float(xx.mean()),float(yy.mean())];cx,cy=[int(round(v)) for v in source_point]
        radius=max(int(np.max(abs(xx-cx))),int(np.max(abs(yy-cy))))+5
        template=np.asarray(ref.crop((cx-radius,cy-radius,cx+radius+1,cy+radius+1)))
        Image.fromarray(template).save(out/'template.png')
        inp.close();score['reference_owner_records']=inp.owner.records;inp=None
        os.killpg(refapp.pid,signal.SIGTERM);refapp.wait(timeout=3);time.sleep(.2)
        current_scenario='stable' if a.scenario in ('stable_static','stable_pan') else ('moved_decoy' if a.scenario=='post_repair_pan' else a.scenario)
        path=out/'current-board.svg';path.write_text(scene(a.seed,current_scenario));(out/'authored-current.svg').write_bytes(path.read_bytes())
        app,ctx,box,inp=ready(s,a.source,path,events)
        for _ in range(abs(a.pan)): inp.press(['Control_L','Right' if a.pan>0 else 'Left'],.04,.18,'setup_pan')
        inp.close();score['setup_owner_records']=inp.owner.records;inp=None
        (out/'before.svg').write_bytes(path.read_bytes());screenshot(s.name,box).save(out/'current-before.png')
        matcher=Matcher(arr)
        index=0; controller_events=[]; task_inputs=Inputs(a.source,ctx,controller_events)
        race_done=threading.Event(); race_started=False
        cached={'source_point':source_point,'point':source_point,'template_shape':list(template.shape[:2])}

        def capture(kind):
            nonlocal index
            start=time.perf_counter_ns(); im=screenshot(s.name,box); end=time.perf_counter_ns(); ar=np.asarray(im)
            name=f'{index:03d}-{kind}.png';index+=1;im.save(out/name)
            controller_events.append(dict(kind=kind,image=name,capture_started_ns=start,capture_ns=end))
            return ar,end

        def project(image):
            match=matcher.locate(image)
            controller_events.append(dict(kind='scene_match',result=match))
            if not match['valid']: return None
            mat=np.asarray(match['homography']); return cv2.perspectiveTransform(np.float32(source_point).reshape(1,1,2),mat)[0,0].tolist()

        def reuse_revalidate(target):
            image,cap=capture('reuse_observation');pred=project(image)
            if pred is None:return {'status':'unavailable'}
            # Caller v3 reuse success preserves the cached target object; it does not
            # consume a replacement target from this stage. Therefore any geometry
            # shift must be typed as association_changed so the no-authority local
            # repair path is the only route that may update cached geometry.
            shift=max(abs(float(a)-float(b)) for a,b in zip(pred,target['point']))
            ok,rmse=strict_template_at(image,template,pred)
            controller_events.append(dict(kind='reuse_exact_footprint',point=pred,rmse=rmse,eligible=ok,projected_shift_px=shift))
            if shift>2 or not ok:return {'status':'association_changed'}
            return {'status':'revalidated','target':dict(target)}

        def local_repair(payload):
            nonlocal race_started
            image,cap=capture('local_repair_observation');pred=project(image)
            if pred is None:return {'status':'unavailable'}
            result=resolve(image,template,pred);controller_events.append(dict(kind='local_repair_evidence',result=result))
            if not result['eligible']:
                mapping={'MISSING':'missing','AMBIGUOUS':'ambiguous','OUT_OF_BOUNDS':'unavailable'}
                return {'status':mapping.get(result['status'],'unavailable')}
            target=dict(payload['target']);target['point']=result['point']
            receipt={'schema':'footprint-local-repair-integration-v1','capture_ns':cap,'result':result}
            if a.scenario=='post_repair_pan' and not race_started:
                race_started=True;threading.Thread(target=external_pan,args=(s.name,race_done),daemon=True).start()
                if not race_done.wait(1.0):raise RuntimeError('race mutation did not finish')
                controller_events.append(dict(kind='harness_external_pan_after_repair'))
            return {'status':'repaired','target':target,'receipt':receipt,'model_calls':0,
                    'grants_semantic_authority':False,'grants_input_authority':False}

        def final_revalidate(target):
            image,cap=capture('final_revalidation_observation')
            result=resolve(image,template,target['point']);age=time.perf_counter_ns()-cap
            controller_events.append(dict(kind='final_footprint_evidence',result=result,age_ns=age))
            if not result['eligible']:
                mapping={'MISSING':'missing','AMBIGUOUS':'ambiguous','OUT_OF_BOUNDS':'unavailable'}
                return {'status':mapping.get(result['status'],'unavailable')}
            moved=max(abs(float(a)-float(b)) for a,b in zip(result['point'],target['point']))
            if moved>2:return {'status':'association_changed'}
            if age>MAX_AGE_NS:return {'status':'stale'}
            target=dict(target);target['point']=result['point']
            return {'status':'revalidated','target':target}

        def execute(payload):
            x,y=payload['target']['point'];task_inputs.click(box[0]+x,box[1]+y)
            task_inputs.press('Delete',purpose='delete_target');task_inputs.press(['Control_L','s'],purpose='save_document')
            time.sleep(.25);capture('post_action_observation');return {'status':'completed'}

        def verify_effect(_execution):
            capture('effect_observation');return {'status':'succeeded'}

        adapters={
            'journal':lambda e:journal.append(e),
            'reuse_revalidate':reuse_revalidate,
            'local_repair':local_repair,
            'final_revalidate':final_revalidate,
            'execute':execute,
            'verify_effect':verify_effect,
        }
        spec={
            'target':'task-target','route':'reuse','coarse_origin':'caller_provided','provided_coarse':None,
            'cached_target':cached,
            'local_repair_on':['association_changed','missing'] if a.mode=='candidate' else [],
            'repair_on':[],'session_id':f'{a.seed}-{a.scenario}-{a.mode}',
        }
        result=run_adaptive(spec,adapters,id_factory=lambda:'no-model-call')
        task_inputs.close();score['controller_owner_records']=task_inputs.owner.records
        write(out/'caller-result.json',result);write(out/'controller-events.json',controller_events);write(out/'journal.json',journal)
        time.sleep(.2)
        before,ar=svg_snapshot(out/'before.svg');after,br=svg_snapshot(path)
        lost=sorted(set(before)-set(after));added=sorted(set(after)-set(before));changed=sorted(k for k in before.keys()&after.keys() if before[k]!=after[k]);unchanged=path.read_bytes()==(out/'before.svg').read_bytes()
        task_input_count=sum(1 for e in controller_events if e.get('kind') in ('pointer','input'))
        expected_edit=a.scenario in ('stable_static','stable_pan','moved_decoy') and not (a.mode=='baseline' and a.scenario in ('stable_pan','moved_decoy'))
        # candidate race must stop; baseline moved/race stops at reuse invalidation.
        if a.scenario=='post_repair_pan': expected_edit=False
        if a.mode=='baseline' and a.scenario in ('moved_decoy','replaced_square','missing','post_repair_pan'): expected_edit=False
        if a.scenario=='duplicate':expected_edit=False
        independent_success=((lost==['task-target'] and not added and not changed and ar==br) if expected_edit
                            else (unchanged and task_input_count==0))
        score.update(independent_success=bool(independent_success),expected_edit=expected_edit,removed_ids=lost,
                     added_ids=added,changed_ids=changed,bytes_unchanged=unchanged,task_input_count=task_input_count,
                     caller_outcome=result['outcome'],caller_reason=result['reason'],repair_path=result['repair_path'],
                     attempted_model_calls=result['accounting']['attempted_calls'],wrong_target_deleted='decoy' in lost,
                     race_mutation_exposed=race_started)
        screenshot(s.name,box).save(out/'final.png')
    except Exception as exc:
        score['error']=repr(exc)
    finally:
        try:
            if inp:inp.close()
        except Exception:pass
        try:
            if s:s.close()
        except Exception:pass
        score['setup_events']=events;write(out/'score.json',score)
        print(json.dumps({k:v for k,v in score.items() if k not in ('setup_events','reference_owner_records','setup_owner_records','controller_owner_records')}),flush=True)

if __name__=='__main__':main()
