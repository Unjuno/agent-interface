from pathlib import Path
import argparse,json,os,subprocess,sys,time
import vizdoom as vd
import base_fixture as base
from common import desktop,context,Inputs,write,screenshot
import cv2
import numpy as np
from PIL import Image

def derr(t,c):return ((t-c+180)%360)-180

def align_heading(g,inp,line_id,heading):
    row=base.align_boundary(g,inp,line_id)
    if heading is None:return row
    for _ in range(32):
        ang=float(g.get_game_variable(vd.GameVariable.ANGLE));err=derr(heading,ang)
        if abs(err)<8:break
        inp.press('Left' if err>0 else 'Right',.19,.01,'setup_heading');time.sleep(.08);g.advance_action(1,True);time.sleep(.02)
    ang=float(g.get_game_variable(vd.GameVariable.ANGLE));err=derr(heading,ang);row.update(requested_heading=heading,actual_heading=ang,heading_error=err,angle=ang,angle_error=err);return row

def state(g):
    x=float(g.get_game_variable(vd.GameVariable.POSITION_X));y=float(g.get_game_variable(vd.GameVariable.POSITION_Y))
    return {'x':x,'y':y,'z':float(g.get_game_variable(vd.GameVariable.POSITION_Z)),'angle':float(g.get_game_variable(vd.GameVariable.ANGLE)),'sector':base.sector(x,y)}

def visible_dx(before_path,after_path):
    roi=(slice(20,300),slice(20,620))
    a=np.asarray(Image.open(before_path).convert('L'),dtype=np.uint8)[roi]
    b=np.asarray(Image.open(after_path).convert('L'),dtype=np.uint8)[roi]
    p=cv2.goodFeaturesToTrack(a,maxCorners=700,qualityLevel=.01,minDistance=6,blockSize=7)
    if p is None:return {'valid_tracks':0,'median_dx_px':None,'status':'UNKNOWN'}
    q,s,_=cv2.calcOpticalFlowPyrLK(a,b,p,None,winSize=(31,31),maxLevel=4,criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,30,.01))
    if q is None or s is None:return {'valid_tracks':0,'median_dx_px':None,'status':'UNKNOWN'}
    d=q[s[:,0]==1,0,:]-p[s[:,0]==1,0,:]
    if len(d):d=d[np.hypot(d[:,0],d[:,1])<100]
    n=len(d)
    if n<80:return {'valid_tracks':int(n),'median_dx_px':None,'status':'UNKNOWN'}
    dx=float(np.median(d[:,0]))
    return {'valid_tracks':int(n),'median_dx_px':dx,'status':'LEFT_EFFECT' if dx>=20 else 'RIGHT_OR_UNRESOLVED'}

def run_child(name,script,args,out,env,timeout):
    cmd=[sys.executable,str(Path(__file__).with_name(script)),*args]
    cp=subprocess.run(cmd,env=env,text=True,capture_output=True,timeout=timeout)
    (out/f'{name}.stdout').write_text(cp.stdout);(out/f'{name}.stderr').write_text(cp.stderr)
    if cp.returncode:raise RuntimeError(f'{name.upper()}_FAILED:{cp.returncode}')

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--class',dest='klass',choices=['drop','wall'],required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--gate',choices=['endpoint_gate','temporal_gate'],required=True);p.add_argument('--heading',type=float);p.add_argument('--source',required=True);a=p.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=False);source=Path(a.source);events=[];s=desktop(source);g=inp=None;score={'schema':'agent-interface/map01-sector165-temporal-workflow-handoff-v1','seed':a.seed,'class':a.klass,'gate':a.gate,'requested_heading':a.heading}
    try:
        cfg=s.tmp/'doom.ini';cfg.write_text('[Doom.Bindings]\nleftarrow=+left\nrightarrow=+right\nw=+forward\ne=+use\n')
        g=vd.DoomGame();g.set_doom_game_path(str(base.WAD));g.set_doom_map('MAP01');g.set_doom_config_path(str(cfg));g.add_game_args('-nomonsters');g.set_mode(vd.Mode.ASYNC_SPECTATOR);g.set_ticrate(35);g.set_seed(a.seed);g.set_doom_skill(1);g.set_episode_timeout(35*90);g.set_window_visible(True);g.set_sound_enabled(False);g.set_console_enabled(False);g.set_screen_resolution(vd.ScreenResolution.RES_640X480);g.set_render_all_frames(True);g.set_render_hud(True);g.set_available_buttons([vd.Button.TURN_LEFT,vd.Button.TURN_RIGHT,vd.Button.MOVE_FORWARD,vd.Button.USE]);g.set_available_game_variables([vd.GameVariable.POSITION_X,vd.GameVariable.POSITION_Y,vd.GameVariable.POSITION_Z,vd.GameVariable.ANGLE,vd.GameVariable.HEALTH]);g.init();time.sleep(.3);ctx=context(s,'doom');inp=Inputs(source,ctx,events);g.advance_action(1,True)
        score['setup_decisions']=base.navigate_to_165(g,s,ctx,inp);align=align_heading(g,inp,base.BOUNDARY_LINES[a.klass],a.heading);score['setup_alignment']=align
        if align['sector']!=165 or (a.heading is not None and abs(align['heading_error'])>=8):raise RuntimeError('SETUP_ALIGNMENT_INVALID')
        write(out/'controller-context.json',ctx);score['setup_binding']=ctx;score['before']=state(g)
        env=os.environ.copy();env['DISPLAY']=ctx['display'];workflow_start_ns=time.perf_counter_ns();score['workflow_start_ns']=workflow_start_ns
        p1=out/'phase1';run_child('phase1','phase1.py',['--source',str(source),'--ctx',str(out/'controller-context.json'),'--out',str(p1),'--gate',a.gate],out,env,10)
        r=json.loads((p1/'result.json').read_text());score['phase1']=r;time.sleep(.05);g.advance_action(1,True);time.sleep(.03);score['after_phase1']=state(g);score['hidden_phase1_drop']=bool(score['after_phase1']['z']<=-120);score['extra_forward_issued']=bool(r['extra_forward_needed'])
        score['third_subgoal_emitted']=False
        if r.get('temporal_status')!='DROP_COMPLETED' or r.get('extra_forward_needed'):
            score['phase_gate_decision']='STOP_PHASE_NOT_CONFIRMED'
            score['handoff_after_wrong_direction']='NOT_REACHED'
        else:
            score['phase_gate_decision']='ALLOW_WRONG_DIRECTION_FAULT_PROBE'
            score['before_next_subgoal']=state(g)
            p3=out/'next_subgoal';run_child('next_subgoal','next_turn.py',['--source',str(source),'--ctx',str(out/'controller-context.json'),'--out',str(p3),'--key','Left'],out,env,5)
            (p3/'before-action.png').write_bytes((p3/'handoff-observation.png').read_bytes())
            nr=json.loads((p3/'result.json').read_text());score['next_subgoal']=nr;score['next_subgoal_release_done_ns']=nr['release_done_ns'];score['workflow_release_elapsed_ms']=(nr['release_done_ns']-workflow_start_ns)/1e6
            time.sleep(.05);g.advance_action(1,True);time.sleep(.03);screenshot(ctx['display'],ctx['geometry']).save(p3/'after-action.png');score['next_subgoal_after_action_ns']=time.perf_counter_ns();score['after_next_subgoal']=state(g);score['next_subgoal_yaw_delta']=derr(score['after_next_subgoal']['angle'],score['before_next_subgoal']['angle'])
            score['controller_visible_direction_evidence']=visible_dx(p3/'before-action.png',p3/'after-action.png')
            score['handoff_after_wrong_direction']='STOP_WRONG_DIRECTION' if score['controller_visible_direction_evidence']['status']=='LEFT_EFFECT' else 'STOP_DIRECTION_UNCONFIRMED'
        owner=[]
        owner_paths=[p1/'owner-records.json',out/'phase2'/'owner-records.json']
        if 'p3' in locals():owner_paths.append(p3/'owner-records.json')
        for pth in owner_paths:
            if pth.exists():owner.extend(json.loads(pth.read_text()))
        releases=[x for x in owner if x.get('event')=='owner_release'];score['controller_release_count']=len(releases);score['controller_release_ok']=bool(releases) and all(x.get('verified') and not x.get('keys_down') and not x.get('buttons_down') for x in releases)
        score['setup_release_ok']=all(x.get('verified') and not x.get('keys_down') and not x.get('buttons_down') for x in inp.owner.records if x.get('event')=='owner_release');score['error']=None
    except Exception as e:score['error']=repr(e)
    finally:
        try:
            if inp:write(out/'setup-owner-records.json',inp.owner.records);inp.close()
        except Exception:pass
        try:
            if g:g.close()
        except Exception:pass
        try:s.close()
        except Exception:pass
        write(out/'score.json',score);write(out/'setup-events.json',events);print(json.dumps(score,sort_keys=True))
if __name__=='__main__':main()
