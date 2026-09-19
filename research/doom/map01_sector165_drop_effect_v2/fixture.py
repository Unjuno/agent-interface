from pathlib import Path
import argparse,hashlib,json,math,os,struct,subprocess,sys,time
import numpy as np
from PIL import Image
import vizdoom as vd
from common import desktop,context,Inputs,screenshot,write
SRC=Path('/mnt/data/offline_lab_extract/source')
WAD=Path(vd.__file__).parent/'freedoom2.wad'
BOUNDARY_LINES={'drop':624,'wall':194}

def parse_wad():
    b=WAD.read_bytes();_,n,o=struct.unpack_from('<4sII',b,0);E=[]
    for i in range(n):
        p,s,nm=struct.unpack_from('<II8s',b,o+i*16);E.append((nm.rstrip(b'\0').decode(),p,s))
    mi=next(i for i,x in enumerate(E) if x[0]=='MAP01');D={x[0]:(x[1],x[2]) for x in E[mi+1:mi+11]}
    def R(nm,fmt):
        p,s=D[nm];z=struct.Struct(fmt);return [z.unpack_from(b,p+i) for i in range(0,s,z.size)]
    V=R('VERTEXES','<hh');LD=R('LINEDEFS','<HHHHHHH');SD=R('SIDEDEFS','<hh8s8s8sH');SG=R('SEGS','<HHHHHH');SS=R('SSECTORS','<HH');N=R('NODES','<hhhhhhhhhhhhHH')
    ss=[]
    for cnt,first in SS:
        vals=[]
        for j in range(first,first+cnt):
            ld=LD[SG[j][3]];si=ld[5] if SG[j][4]==0 else ld[6]
            if si!=65535:vals.append(SD[si][-1])
        if not vals or len(set(vals))!=1:raise RuntimeError('subsector sector ambiguity')
        ss.append(vals[0])
    def sector(x,y):
        k=len(N)-1
        while True:
            z=N[k];nx,ny,dx,dy=z[:4]
            if dx==0:s=int((dy>0) if x<=nx else (dy<0))
            elif dy==0:s=int((dx<0) if y<=ny else (dx>0))
            else:s=1 if ((x-nx)*dy-(y-ny)*dx)<0 else 0
            ch=z[-1] if s else z[-2]
            if ch&32768:return ss[ch&32767]
            k=ch
    return V,LD,sector
V,LD,sector=parse_wad()

def desc(im):
    a=np.asarray(im.convert('L'),np.float32)[35:325,55:585]
    a=np.asarray(Image.fromarray(a.astype(np.uint8)).resize((48,26),Image.Resampling.BILINEAR),np.float32)/255.0
    a=(a-a.mean())/(a.std()+1e-4);return a.ravel()
def derr(t,c):return ((t-c+180)%360)-180

def navigate_to_165(g,s,ctx,inp):
    last=None
    for i in range(45):
        x=float(g.get_game_variable(vd.GameVariable.POSITION_X));y=float(g.get_game_variable(vd.GameVariable.POSITION_Y))
        if sector(x,y)==165:return i
        pre=screenshot(s.name,ctx['geometry']);bd=desc(pre);inp.press('w',.35,.04,'setup_nav_forward');g.advance_action(1,True);post=screenshot(s.name,ctx['geometry']);ad=desc(post)
        npf=float(np.mean((ad-bd)**2))<.055
        if npf:
            inp.press('e',.04,.03,'setup_nav_use');rep=last is not None and i-last<=4
            for _ in range(6 if rep else 1):inp.press('Right',.19,.01,'setup_nav_repair')
            last=i
        elif (i+1)%9==0:
            inp.press('e',.04,.03,'setup_periodic_use')
            for _ in range(3):inp.press('Right',.19,.01,'setup_periodic_turn')
    raise RuntimeError('SETUP_DID_NOT_REACH_SECTOR165')

def align_boundary(g,inp,line_id):
    l=LD[line_id];p1,p2=V[l[0]],V[l[1]]
    x=float(g.get_game_variable(vd.GameVariable.POSITION_X));y=float(g.get_game_variable(vd.GameVariable.POSITION_Y))
    vx,vy=float(p2[0]-p1[0]),float(p2[1]-p1[1]);den=vx*vx+vy*vy
    t=max(0.0,min(1.0,((x-p1[0])*vx+(y-p1[1])*vy)/den));qx=p1[0]+t*vx;qy=p1[1]+t*vy
    nx,ny=qx-x,qy-y;nn=max(1e-6,math.hypot(nx,ny));tx=qx+40*nx/nn;ty=qy+40*ny/nn
    desired=math.degrees(math.atan2(ty-y,tx-x))%360
    for _ in range(32):
        ang=float(g.get_game_variable(vd.GameVariable.ANGLE));er=derr(desired,ang)
        if abs(er)<9:break
        inp.press('Left' if er>0 else 'Right',.19,.01,'setup_align');time.sleep(.10);g.advance_action(1,True);time.sleep(.03)
    x=float(g.get_game_variable(vd.GameVariable.POSITION_X));y=float(g.get_game_variable(vd.GameVariable.POSITION_Y));ang=float(g.get_game_variable(vd.GameVariable.ANGLE))
    return {'line_id':line_id,'segment':[list(p1),list(p2)],'x':x,'y':y,'angle':ang,'sector':sector(x,y),'desired_angle':desired,'angle_error':derr(desired,ang)}

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--class',dest='klass',choices=['drop','wall'],required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--source',default=str(SRC));p.add_argument('--controller-python',default='python');a=p.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=False);source=Path(a.source);events=[];s=desktop(source);g=inp=None;score={'seed':a.seed,'class':a.klass}
    try:
        cfg=s.tmp/'doom.ini';cfg.write_text('[Doom.Bindings]\nleftarrow=+left\nrightarrow=+right\nw=+forward\ne=+use\n')
        g=vd.DoomGame();g.set_doom_game_path(str(WAD));g.set_doom_map('MAP01');g.set_doom_config_path(str(cfg));g.add_game_args('-nomonsters');g.set_mode(vd.Mode.ASYNC_SPECTATOR);g.set_ticrate(35);g.set_seed(a.seed);g.set_doom_skill(1);g.set_episode_timeout(35*90);g.set_window_visible(True);g.set_sound_enabled(False);g.set_console_enabled(False);g.set_screen_resolution(vd.ScreenResolution.RES_640X480);g.set_render_all_frames(True);g.set_render_hud(True);g.set_available_buttons([vd.Button.TURN_LEFT,vd.Button.TURN_RIGHT,vd.Button.MOVE_FORWARD,vd.Button.USE]);g.set_available_game_variables([vd.GameVariable.POSITION_X,vd.GameVariable.POSITION_Y,vd.GameVariable.POSITION_Z,vd.GameVariable.ANGLE,vd.GameVariable.HEALTH]);g.init();time.sleep(.3);ctx=context(s,'doom');inp=Inputs(source,ctx,events);g.advance_action(1,True)
        score['setup_decisions']=navigate_to_165(g,s,ctx,inp);align=align_boundary(g,inp,BOUNDARY_LINES[a.klass]);score['setup_alignment']=align
        if align['sector']!=165 or abs(align['angle_error'])>=9:raise RuntimeError('SETUP_ALIGNMENT_INVALID')
        pre=screenshot(s.name,ctx['geometry']);pre.save(out/'pre.png');write(out/'controller-context.json',ctx)
        before={'x':float(g.get_game_variable(vd.GameVariable.POSITION_X)),'y':float(g.get_game_variable(vd.GameVariable.POSITION_Y)),'z':float(g.get_game_variable(vd.GameVariable.POSITION_Z)),'angle':float(g.get_game_variable(vd.GameVariable.ANGLE))};before['sector']=sector(before['x'],before['y']);score['before']=before
        cdir=out/'controller';cmd=[a.controller_python,str(Path(__file__).with_name('controller.py')),'--source',str(source),'--ctx',str(out/'controller-context.json'),'--pre',str(out/'pre.png'),'--out',str(cdir)]
        env=os.environ.copy();env.update({'DISPLAY':ctx['display']})
        cp=subprocess.run(cmd,env=env,text=True,capture_output=True,timeout=8);(out/'controller.stdout').write_text(cp.stdout);(out/'controller.stderr').write_text(cp.stderr);score['controller_returncode']=cp.returncode
        if cp.returncode!=0:raise RuntimeError('CONTROLLER_FAILED')
        result=json.loads((cdir/'result.json').read_text());score['controller_result']=result
        # scorer-only refresh after separate X11 controller; no input is active here
        time.sleep(.05);g.advance_action(1,True);time.sleep(.03)
        after={'x':float(g.get_game_variable(vd.GameVariable.POSITION_X)),'y':float(g.get_game_variable(vd.GameVariable.POSITION_Y)),'z':float(g.get_game_variable(vd.GameVariable.POSITION_Z)),'angle':float(g.get_game_variable(vd.GameVariable.ANGLE))};after['sector']=sector(after['x'],after['y']);score['after']=after
        score['hidden_effect']='DROP' if after['sector']==38 and after['z']<=-128 else ('NO_DROP' if after['sector']==165 and after['z']>=-64 else 'OTHER')
        score['setup_release_ok']=all(r.get('verified') and not r.get('keys_down') and not r.get('buttons_down') for r in inp.owner.records if r.get('event')=='owner_release')
        score['error']=None
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
