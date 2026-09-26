from __future__ import annotations
import argparse,copy,hashlib,json,math,sys
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text())
def parse_svg(p):
    root=ET.fromstring(p.read_bytes()); rs=root.findall('{http://www.w3.org/2000/svg}rect')
    return [{k:r.attrib.get(k) for k in ('id','x','y','width','height','transform')} for r in rs]
def red_components(p):
    arr=np.asarray(Image.open(p).convert('RGB'));m=(arr[:,:,0]>200)&(arr[:,:,1]<70)&(arr[:,:,2]<70)
    m[:150,:]=False;m[680:,:]=False;m[:,:100]=False;m[:,1100:]=False
    seen=np.zeros(m.shape,dtype=bool);out=[]
    for sy,sx in zip(*np.where(m)):
        if seen[sy,sx]:continue
        q=[(int(sy),int(sx))];seen[sy,sx]=1;xs=[];ys=[]
        for y,x in q:
            xs.append(x);ys.append(y)
            for yy,xx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                if 0<=yy<m.shape[0] and 0<=xx<m.shape[1] and m[yy,xx] and not seen[yy,xx]: seen[yy,xx]=1;q.append((yy,xx))
        bb=[min(xs),min(ys),max(xs)+1,max(ys)+1]
        if 36<=bb[2]-bb[0]<=44 and 26<=bb[3]-bb[1]<=34 and len(xs)>850:out.append(bb)
    return out

def apply_mut(obj,path,val):
    cur=obj
    for k in path[:-1]:cur=cur[k]
    cur[path[-1]]=val

def audit(root:Path, mutation=None):
    errs=[];checks=0
    freeze=load(root/'FREEZE.json');schedule=load(root/'SCHEDULE.json')['cases']
    for rel,h in freeze['sha256'].items():
        checks+=1
        if not (root/rel).exists() or sha(root/rel)!=h:errs.append('source:'+rel)
    if len(schedule)!=12:errs.append('schedule_count')
    formal=root/'formal'
    cases=[]
    for i,spec in enumerate(schedule):
        p=formal/f'case-{i:02d}'/'CASE.json';w=formal/f'WRAPPER-{i:02d}.json'
        checks+=2
        if not p.exists() or not w.exists():errs.append(f'missing:{i}');continue
        d=load(p);wr=load(w)
        if mutation and mutation.get('case')==i: d=copy.deepcopy(d);apply_mut(d,mutation['path'],mutation['value'])
        cases.append(d)
        if wr.get('returncode')!=0 or wr.get('timeout') is not False:errs.append(f'wrapper:{i}')
        if d.get('status')!='complete' or d.get('worker_returncode')!=0:errs.append(f'complete:{i}')
        for k in ('policy','first_dx','first_dy','rep'):
            checks+=1
            observed=d.get(k) if k in d else d.get('first_step',[None,None])[0 if k=='first_dx' else 1] if k.startswith('first_') else None
            expected=spec[k]
            if observed!=expected:errs.append(f'spec:{i}:{k}')
        if d.get('authority')!='none' or d.get('model_calls')!=0:errs.append(f'authority:{i}')
        if d.get('process_exits')!={'inkscape':-15,'openbox':0,'xvfb':0}:errs.append(f'exits:{i}')
        for key in ('final','cleanup'):
            st=d.get(key,{})
            if st.get('button1') or any(bytes.fromhex(st.get('keymap_hex','00'))):errs.append(f'neutral:{i}:{key}')
        ev=d.get('events',[]); presses=[e for e in ev if e.get('kind')=='button' and e.get('down') is True]; releases=[e for e in ev if e.get('kind')=='button' and e.get('down') is False]
        if len(presses)!=1 or len(releases)!=1:errs.append(f'button_count:{i}')
        held=d.get('events',[])
        if not any(e.get('kind')=='state' and e.get('label')=='held' and e.get('observed',{}).get('button1') for e in held):errs.append(f'held:{i}')
        svgs=parse_svg(formal/f'case-{i:02d}'/'after.svg');checks+=1
        if len(svgs)!=1:errs.append(f'svg_count:{i}');continue
        r=svgs[0]
        try: delta=[float(r['x'])-50,float(r['y'])-50]
        except Exception: errs.append(f'svg_parse:{i}');continue
        if abs(float(r['width'])-40)>.001 or abs(float(r['height'])-30)>.001 or r.get('transform') not in (None,''):errs.append(f'collateral:{i}')
        if any(abs(delta[j]-d.get('saved_effect_delta',[999,999])[j])>.001 for j in (0,1)):errs.append(f'saved_record:{i}')
        source_comps=red_components(formal/f'case-{i:02d}'/'source.png');checks+=1
        if len(source_comps)!=1:errs.append(f'source_components:{i}');continue
        if spec['policy']!='SERVO_OBSERVER_UNAVAILABLE':
            mid_comps=red_components(formal/f'case-{i:02d}'/'mid_hold.png');checks+=1
            if len(mid_comps)!=1:errs.append(f'mid_components:{i}')
            else:
                sc=[(source_comps[0][0]+source_comps[0][2])//2,(source_comps[0][1]+source_comps[0][3])//2]
                mc=[(mid_comps[0][0]+mid_comps[0][2])//2,(mid_comps[0][1]+mid_comps[0][3])//2]
                obs=[mc[0]-sc[0],mc[1]-sc[1]]
                if obs!=d.get('observed_effect_delta'):errs.append(f'mid_observation:{i}')
        f=(spec['first_dx'],spec['first_dy'])
        if spec['policy']=='OPEN_LOOP':
            exp={(5,3):[45.0,27.0],(10,6):[40.0,24.0]}[f]
            if d.get('correction_count')!=0 or d.get('decision')!='OPEN_LOOP':errs.append(f'open_policy:{i}')
            if d.get('pointer_delta_final')!=[50,30]:errs.append(f'open_pointer:{i}')
            if any(abs(delta[j]-exp[j])>.1 for j in (0,1)):errs.append(f'open_effect:{i}')
        elif spec['policy']=='MID_EFFECT_SERVO':
            expobs={(5,3):[25,15],(10,6):[20,12]}[f]
            expend={(5,3):[55,33],(10,6):[60,36]}[f]
            if d.get('observed_effect_delta')!=expobs:errs.append(f'servo_mid:{i}')
            if d.get('correction_count')!=1 or d.get('decision')!='CORRECT_ONCE':errs.append(f'servo_policy:{i}')
            if d.get('pointer_delta_final')!=expend:errs.append(f'servo_pointer:{i}')
            if any(abs(delta[j]-[50.0,30.0][j])>.1 for j in (0,1)):errs.append(f'servo_effect:{i}')
        else:
            if d.get('observed_effect_delta') is not None or d.get('correction_count')!=0 or d.get('decision')!='YIELD_OBSERVER_UNAVAILABLE':errs.append(f'unavail_policy:{i}')
            if d.get('pointer_delta_final')!=[30,18]:errs.append(f'unavail_pointer:{i}')
    # paired error improvement
    for rep in (0,1):
        for f in ((5,3),(10,6)):
            rows=[d for d in cases if d.get('rep')==rep and tuple(d.get('first_step',[]))==f]
            by={d.get('policy'):d for d in rows}
            if 'OPEN_LOOP' in by and 'MID_EFFECT_SERVO' in by:
                oe=sum(abs(x) for x in by['OPEN_LOOP'].get('saved_effect_error',[999,999]));se=sum(abs(x) for x in by['MID_EFFECT_SERVO'].get('saved_effect_error',[999,999]));checks+=1
                if not se<oe:errs.append(f'improvement:{rep}:{f}')
    return {'checks':checks,'errors':sorted(set(errs)),'audit_pass':not errs,'cases_loaded':len(cases)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path,nargs='?',default=HERE);args=ap.parse_args();o=audit(args.root.resolve());print(json.dumps(o,sort_keys=True));return 0 if o['audit_pass'] else 1
if __name__=='__main__':raise SystemExit(main())
