#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, platform, statistics, sys, time
import numpy as np
from PIL import Image
import vizdoom as vd

SCHEMA='agent-interface/map01-door-action-effect-history-v2'
TRAIN_CASES=12
ALIAS_THRESHOLD=0.005
OPEN_TICS=range(1,8)
CLOSE_TICS=range(165,174)
YAW_SCHEDULE=[-2,-1,0,1,2,0,-1,1,0,2,-2,1, -2,2,-1,1,0,2,-2,0]
WAIT_SCHEDULE=[0,3,6,1,5,2,7,4,1,6,3,0, 5,2,7,4,0,6,1,3]
SEEDS=list(range(994200,994220))

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def descriptor(rgb):
    # Frozen task-relative viewport: excludes HUD/weapon and keeps doorway geometry.
    im=Image.fromarray(rgb[10:170,35:285]).convert('L').resize((32,20),Image.Resampling.BILINEAR)
    return np.asarray(im,dtype=np.float32)/255.0

def build_game(seed):
    p=pathlib.Path(vd.__file__).resolve().parent
    g=vd.DoomGame();g.set_doom_game_path(str(p/'freedoom2.wad'));g.set_doom_map('MAP01');g.set_mode(vd.Mode.PLAYER)
    g.set_seed(seed);g.set_doom_skill(1);g.set_episode_timeout(35*40);g.set_window_visible(False);g.set_sound_enabled(False)
    g.set_screen_resolution(vd.ScreenResolution.RES_320X240);g.set_screen_format(vd.ScreenFormat.RGB24)
    g.set_available_buttons([vd.Button.MOVE_FORWARD,vd.Button.USE,vd.Button.TURN_LEFT,vd.Button.TURN_RIGHT]);g.init();return g

def one_case(root,case_index,seed,yaw,wait):
    g=build_game(seed); samples=[]; case_dir=root/f'case-{case_index:02d}';case_dir.mkdir(parents=True)
    try:
        for _ in range(16): g.make_action([1,0,0,0],9)
        if yaw<0:g.make_action([0,0,1,0],-yaw)
        elif yaw>0:g.make_action([0,0,0,1],yaw)
        if wait:g.make_action([0,0,0,0],wait)
        prev=np.array(g.get_state().screen_buffer).copy(); g.make_action([0,1,0,0],1)
        for t in range(1,175):
            g.make_action([0,0,0,0],1);cur=np.array(g.get_state().screen_buffer).copy()
            if t in OPEN_TICS or t in CLOSE_TICS:
                label=0 if t in OPEN_TICS else 1; cd=descriptor(cur); pd=descriptor(prev); delta=cd-pd
                stem=f'{t:03d}-{"opening" if label==0 else "closing"}'
                name=stem+'.png'; prev_name=stem+'-prev.png'
                Image.fromarray(cur).save(case_dir/name); Image.fromarray(prev).save(case_dir/prev_name)
                samples.append({'case':case_index,'seed':seed,'yaw':yaw,'wait':wait,'tic':t,'label':label,
                    'current':cd,'delta':delta,'rgb_sha256':sha_bytes(cur.tobytes()),'prev_rgb_sha256':sha_bytes(prev.tobytes()),
                    'png':str(pathlib.Path(case_dir.name)/name),'prev_png':str(pathlib.Path(case_dir.name)/prev_name)})
            prev=cur
    finally:g.close()
    return samples

def centroid_predict(X, centroids):
    return np.array([int(np.argmin([np.mean((row-c)**2) for c in centroids])) for row in X])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=pathlib.Path,required=True);args=ap.parse_args();root=args.out;root.mkdir(parents=True,exist_ok=False)
    all_samples=[]; started=time.time()
    for i,(seed,yaw,wait) in enumerate(zip(SEEDS,YAW_SCHEDULE,WAIT_SCHEDULE)):
        all_samples.extend(one_case(root,i,seed,yaw,wait))
    train=[s for s in all_samples if s['case']<TRAIN_CASES];test=[s for s in all_samples if s['case']>=TRAIN_CASES]
    Xc=np.array([s['current'].ravel() for s in train]);Xd=np.array([s['delta'].ravel() for s in train]);y=np.array([s['label'] for s in train])
    current_cent=[Xc[y==lab].mean(0) for lab in (0,1)];delta_cent=[Xd[y==lab].mean(0) for lab in (0,1)]
    Tc=np.array([s['current'].ravel() for s in test]);Td=np.array([s['delta'].ravel() for s in test]);ty=np.array([s['label'] for s in test])
    cp=centroid_predict(Tc,current_cent);dp=centroid_predict(Td,delta_cent)
    alias_obs=[];alias_pairs=[]
    for case in range(TRAIN_CASES,len(SEEDS)):
        rows=[s for s in test if s['case']==case];opens=[s for s in rows if s['label']==0];closes=[s for s in rows if s['label']==1]
        for o in opens:
            q=min(closes,key=lambda z:float(np.sqrt(np.mean((o['current']-z['current'])**2))))
            dist=float(np.sqrt(np.mean((o['current']-q['current'])**2)))
            if dist<=ALIAS_THRESHOLD:
                alias_pairs.append({'case':case,'open_tic':o['tic'],'close_tic':q['tic'],'current_rmse':dist,
                    'delta_rmse':float(np.sqrt(np.mean((o['delta']-q['delta'])**2))),
                    'open_rgb_sha256':o['rgb_sha256'],'close_rgb_sha256':q['rgb_sha256']})
                alias_obs.extend([o,q])
    Ac=np.array([s['current'].ravel() for s in alias_obs]) if alias_obs else np.zeros((0,Xc.shape[1]));Ad=np.array([s['delta'].ravel() for s in alias_obs]) if alias_obs else np.zeros((0,Xd.shape[1]));ay=np.array([s['label'] for s in alias_obs],dtype=int)
    acp=centroid_predict(Ac,current_cent) if len(alias_obs) else np.array([],dtype=int);adp=centroid_predict(Ad,delta_cent) if len(alias_obs) else np.array([],dtype=int)
    current_acc=float((cp==ty).mean());history_acc=float((dp==ty).mean());alias_current=float((acp==ay).mean()) if len(ay) else None;alias_history=float((adp==ay).mean()) if len(ay) else None
    # Hash collisions in semantic histories. History bytes are exact descriptor pairs, not labels.
    history_hash_labels={}
    current_hash_labels={}
    for s in all_samples:
        ch=sha_bytes(s['current'].tobytes());hh=sha_bytes(np.concatenate([s['current'].ravel(),s['delta'].ravel()]).tobytes())
        current_hash_labels.setdefault(ch,set()).add(s['label']);history_hash_labels.setdefault(hh,set()).add(s['label'])
    cross_current=sum(len(v)>1 for v in current_hash_labels.values());cross_history=sum(len(v)>1 for v in history_hash_labels.values())
    gates={'alias_pairs_at_least_6':len(alias_pairs)>=6,'alias_current_accuracy_le_0_75':alias_current is not None and alias_current<=0.75,
           'alias_history_accuracy_ge_0_95':alias_history is not None and alias_history>=0.95,'history_cross_label_hash_collisions_zero':cross_history==0}
    decision='SUPPORT_ACTION_EFFECT_HISTORY' if all(gates.values()) else 'FAIL_ACTION_EFFECT_HISTORY_HYPOTHESIS'
    summary={'schema':SCHEMA,'decision':decision,'development_seeds_excluded':[994001,*range(994010,994015),*range(994100,994120)],'formal_seeds':SEEDS,'train_cases':TRAIN_CASES,
      'test_cases':len(SEEDS)-TRAIN_CASES,'samples':len(all_samples),'test_samples':len(test),'alias_threshold':ALIAS_THRESHOLD,'alias_pairs':alias_pairs,
      'current_only_test_accuracy':current_acc,'delta_history_test_accuracy':history_acc,'alias_current_accuracy':alias_current,'alias_history_accuracy':alias_history,
      'current_descriptor_cross_label_exact_collisions':cross_current,'history_descriptor_cross_label_exact_collisions':cross_history,'gates':gates,'wall_seconds':time.time()-started,
      'environment':{'python':sys.version.split()[0],'platform':platform.platform(),'vizdoom':vd.__version__,'numpy':np.__version__},
      'scope':'Direct ViZDoom teacher/evaluator mechanics study. Deployment claim forbidden; no OS-input/model/MAP01-clear claim.'}
    # Compact samples omit arrays but retain identities.
    compact=[{k:v for k,v in s.items() if k not in ('current','delta')} for s in all_samples]
    (root/'samples.json').write_text(json.dumps(compact,indent=2)+'\n');(root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2));raise SystemExit(0 if decision.startswith('SUPPORT') else 2)
if __name__=='__main__':main()
