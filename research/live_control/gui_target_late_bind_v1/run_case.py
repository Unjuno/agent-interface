from pathlib import Path
import argparse,contextlib,json,os,signal,time
import numpy as np
from PIL import Image
from common import desktop,context,Inputs,screenshot,write
from resolver import resolve,MAX_AGE_NS
from oracle import svg_snapshot

def scene(seed):
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="700" viewBox="0 0 1000 700"><rect id="background" width="1000" height="700" fill="white"/>'
    for i in range(6):
        for j in range(5):
            x=30+i*150;y=40+j*125
            svg+=f'<g id="cell{i}-{j}" fill="none" stroke="black" stroke-width="2"><rect id="rect{i}-{j}" x="{x}" y="{y}" width="120" height="90"/><path id="path{i}-{j}" d="M{x+10},{y+10+j*5} L{x+90-i*5},{y+80} L{x+110},{y+10+i*4} Z"/></g><text id="text{i}-{j}" x="{x+5}" y="{y+35}" font-size="20">ID{i}-{j}-{seed+137*i+53*j}</text>'
    svg+='<rect id="clear-panel" x="360" y="300" width="260" height="100" fill="white"/>'
    svg+='<circle id="task-target" cx="460" cy="350" r="20" fill="#f000b0"/>'
    svg+='<rect id="decoy" x="560" y="330" width="40" height="40" fill="#f000b0"/>'
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
    else:raise RuntimeError('GTK canvas focus not stable')
    ctx['focus']=fid;x,y,w,h=ctx['geometry'];box=[x+70,y+130,w-140,h-240]
    inp=Inputs(source,ctx,events);inp.press('Escape',purpose='setup');inp.press('F1',purpose='setup');inp.press('5',purpose='setup');time.sleep(.2);inp.press(['Control_L','s'],purpose='setup');time.sleep(.2)
    return app,ctx,box,inp

def target_template(im):
    arr=np.asarray(im);mask=(arr[:,:,0]>220)&(arr[:,:,1]<20)&(arr[:,:,2]>150)&(arr[:,:,2]<200);yy,xx=np.where(mask)
    # circle is leftmost magenta component; decoy is farther right
    if len(xx)<40:raise RuntimeError('magenta target missing')
    # cluster around leftmost half
    cutoff=float(np.median(xx)); sel=xx<cutoff
    xs=xx[sel];ys=yy[sel]
    if len(xs)<20: xs=xx;ys=yy
    cx,cy=int(round(float(xs.mean()))),int(round(float(ys.mean())))
    # fixed outline footprint 51x51
    r=25;arr=np.asarray(im)
    return [float(cx),float(cy)],arr[cy-r:cy+r+1,cx-r:cx+r+1].copy()

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);p.add_argument('--mode',choices=['snapshot_bound','late_bind'],required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--wait-s',type=float,default=6.5);p.add_argument('--pan',type=int,default=3);a=p.parse_args()
    out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=False);s=inp=None;app=None;events=[];score={'mode':a.mode,'seed':a.seed,'wait_s':a.wait_s,'pan':a.pan}
    try:
        with open(out/'startup.stdout','w') as log,contextlib.redirect_stdout(log):s=desktop(a.source)
        path=out/'board.svg';path.write_text(scene(a.seed));(out/'before.svg').write_bytes(path.read_bytes())
        app,ctx,box,inp=ready(s,a.source,path,events)
        ref=screenshot(s.name,box);ref.save(out/'prewait.png');point,template=target_template(ref);Image.fromarray(template).save(out/'template.png')
        pre_capture_ns=time.perf_counter_ns();score['source_point']=point;score['pre_capture_ns']=pre_capture_ns
        wait_start=time.perf_counter_ns();score['wait_started_ns']=wait_start
        # world changes during decision wait, same in both arms
        time.sleep(1.0)
        for _ in range(abs(a.pan)):inp.press(['Control_L','Right' if a.pan>0 else 'Left'],.04,.12,'harness_pan')
        elapsed=(time.perf_counter_ns()-wait_start)/1e9
        if elapsed<a.wait_s:time.sleep(a.wait_s-elapsed)
        wait_end=time.perf_counter_ns();score['wait_ended_ns']=wait_end;score['wait_ns']=wait_end-wait_start
        task_events=[];task=Inputs(a.source,ctx,task_events)
        if a.mode=='snapshot_bound':
            evidence_age=time.perf_counter_ns()-pre_capture_ns;score['evidence_age_ns']=evidence_age;score['fresh']=evidence_age<=MAX_AGE_NS
            if score['fresh']:
                res=resolve(np.asarray(ref),template,point);score['resolver']=res
                if res['eligible']:
                    x,y=res['point'];task.click(box[0]+x,box[1]+y);task.press('Delete');task.press(['Control_L','s'])
        else:
            cap_start=time.perf_counter_ns();cur=screenshot(s.name,box);cap_end=time.perf_counter_ns();cur.save(out/'postwait.png');score['post_capture_ns']=cap_end;score['evidence_age_ns']=time.perf_counter_ns()-cap_end;score['fresh']=score['evidence_age_ns']<=MAX_AGE_NS
            res=resolve(np.asarray(cur),template,point);score['resolver']=res
            if score['fresh'] and res['eligible']:
                x,y=res['point'];task.click(box[0]+x,box[1]+y);task.press('Delete');task.press(['Control_L','s'])
        task.close();score['task_owner_records']=task.owner.records;score['task_input_count']=sum(1 for e in task_events if e.get('purpose')=='task' or e.get('kind')=='pointer')
        time.sleep(.25)
        before,br=svg_snapshot(out/'before.svg');after,ar=svg_snapshot(path);lost=sorted(set(before)-set(after));added=sorted(set(after)-set(before));changed=sorted(k for k in before.keys()&after.keys() if before[k]!=after[k]);score['removed_ids']=lost;score['added_ids']=added;score['changed_ids']=changed;score['independent_success']=lost==['task-target'] and not added and not changed and br==ar
        score['safe_yield']=bool((not score['fresh']) and score['task_input_count']==0 and path.read_bytes()==(out/'before.svg').read_bytes())
        score['setup_owner_records']=inp.owner.records;score['release_ok']=all(r.get('verified') and not r.get('keys_down') and not r.get('buttons_down') for r in score['setup_owner_records']+score['task_owner_records'] if r.get('event')=='owner_release')
        screenshot(s.name,box).save(out/'final.png');score['error']=None
    except Exception as exc:score['error']=repr(exc)
    finally:
        try:
            if inp:inp.close()
        except Exception:pass
        try:
            if app and app.poll() is None:os.killpg(app.pid,signal.SIGTERM);app.wait(timeout=3)
        except Exception:pass
        try:
            if s:s.close()
        except Exception:pass
        write(out/'score.json',score);write(out/'events.json',events);print(json.dumps({k:v for k,v in score.items() if not k.endswith('_records')}))
if __name__=='__main__':main()
