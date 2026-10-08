"""One-shot frozen fixture runner; controllers receive PPM bytes and metadata only."""
from __future__ import annotations
import argparse, hashlib, json, math, os, random
from pathlib import Path
import candidate

ROOT = Path(__file__).resolve().parent
COLORS = ((255,0,0),(0,255,0),(0,0,255))
WORLD = ((-0.45,-0.25,1.0),(0.45,-0.20,1.0),(0.05,0.50,1.0))
ARMS = ("raw_pixels", "spherical_features", "viewstate_oracle")
SEEDS = tuple(range(30030,30060))


def normalize(v):
    n=math.sqrt(sum(x*x for x in v)); return tuple(x/n for x in v)


def camera(yaw,pitch):
    cy,sy=math.cos(yaw),math.sin(yaw); cp,sp=math.cos(pitch),math.sin(pitch)
    return ((cy,sy*sp,sy*cp),(0.0,cp,-sp),(-sy,cy*sp,cy*cp))


def render(yaw,pitch,focal=48.0, fault=None, width=96, height=96):
    q=camera(yaw,pitch); points=[]
    translation=(.35,0.0,0.0) if fault=="camera_translation" else (0.0,0.0,0.0)
    radial=(2.0,.7,1.4) if fault=="range_variation" else (1.0,1.0,1.0)
    for idx,p in enumerate(WORLD):
        moved=tuple(radial[idx]*p[k]-translation[k] for k in range(3))
        b=tuple(sum(q[k][i]*moved[k] for k in range(3)) for i in range(3))
        if b[2] <= .1: raise ValueError("landmark behind camera")
        points.append(((width-1)/2+focal*b[0]/b[2],(height-1)/2-focal*b[1]/b[2]))
    if fault=="move_third": points[2]=(points[2][0]+18.0,points[2][1]-14.0)
    if fault=="near_singular":
        # First two image rays become nearly parallel; this must force YIELD.
        points[1]=(points[0][0]+0.5,points[0][1]+0.5)
    image=bytearray([16,16,16]*(width*height))
    marker_size=1 if fault=="low_texture" else 3
    half=marker_size//2
    for idx,(x,y) in enumerate(points):
        if fault=="hide_second" and idx==1: continue
        color=COLORS[idx]
        if fault=="swap_ids" and idx<2: color=COLORS[1-idx]
        ix,iy=round(x),round(y)
        for yy in range(iy-half,iy+half+1):
            for xx in range(ix-half,ix+half+1):
                if 0<=xx<width and 0<=yy<height:
                    off=(yy*width+xx)*3; image[off:off+3]=bytes(color)
    return f"P6\n{width} {height}\n255\n".encode()+bytes(image),points


def write_ppm(path,data):
    path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(data)


def scenario(seed,condition):
    rng=random.Random(seed*37 + (0 if condition=="pure_yaw" else 1 if condition=="combined_rotation" else 2 if condition=="focal_shift" else 3))
    yaw=rng.uniform(-.28,.28); pitch=0.0; focal=48.0; fault=None
    if condition=="combined_rotation": pitch=rng.uniform(-.24,.24)
    elif condition=="focal_shift": pitch=rng.uniform(-.20,.20); focal=43.0 if seed%2 else 53.0
    elif condition=="feature_loss":
        pitch=rng.uniform(-.18,.18)
        faults=("hide_second","swap_ids","move_third","near_singular","low_texture","camera_translation","stale_frame","viewport_resize","range_variation")
        fault=faults[seed%len(faults)]
    return yaw,pitch,focal,fault


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default=str(ROOT/"results/a02-outcome")); a=ap.parse_args()
    out=Path(a.output)
    if out.exists() and any(out.iterdir()): raise SystemExit("refusing nonempty output: formal run is one-shot")
    out.mkdir(parents=True,exist_ok=True)
    frames=out/"frames"; events_path=out/"events.jsonl"; truth_path=out/"scorer_truth.jsonl"
    conditions=("pure_yaw","combined_rotation","focal_shift","feature_loss")
    with events_path.open("x") as events, truth_path.open("x") as truths:
      for condition in conditions:
       for seed in SEEDS:
        y0,p0,focal,fault=scenario(seed,condition)
        ref_data,_=render(0.0,0.0,48.0)
        refpath=frames/"reference.ppm"
        if not refpath.exists(): write_ppm(refpath,ref_data)
        ref_xy=candidate.detect(96,96,ref_data.split(b"\n255\n",1)[1])
        refhash=hashlib.sha256(ref_data).hexdigest()
        # Pair scheduling is fixed and seed/stratum derived before execution.
        order=list(ARMS); random.Random(seed+len(condition)).shuffle(order)
        for arm in order:
         yaw,pitch=y0,p0; actions=[]; terminal="STEP_LIMIT"; stopped=False; loss=False
         for step in range(13):
          active_fault=fault if step==0 else None
          width,height=(112,112) if active_fault=="viewport_resize" else (96,96)
          image,world_points=render(yaw,pitch,focal,active_fault,width,height)
          case=f"{condition}-{seed:05d}-{arm}"; frame_rel=Path("frames")/case/f"{step:02d}.ppm"
          framepath=out/frame_rel; write_ppm(framepath,image)
          framehash=hashlib.sha256(image).hexdigest()
          meta={"width":width,"height":height,"target_generation":seed,"viewport_generation":seed+(1 if active_fault=="stale_frame" else 0)}
          pts=None; fv=None; reason=None
          try:
           pts=candidate.detect(width,height,image.split(b"\n255\n",1)[1])
           fv=candidate.feature_vector(arm,pts,ref_xy)
           if step>=12: action=None
           elif arm=="viewstate_oracle": action=(max(-.08,min(.08,-.72*yaw)),max(-.08,min(.08,-.72*pitch)))
           else: action=candidate.choose_action(arm,pts,ref_xy,meta)
           status=("STEP_LIMIT" if step>=12 else "STOP") if action is None else "ACTION"
          except (ValueError,ZeroDivisionError) as exc:
           action=None; status="YIELD"; terminal="UNKNOWN_YIELD"; loss=True
           reason=str(exc)
          if status=="YIELD" and fault=="range_variation":
           raise RuntimeError("projection-null range control unexpectedly invalidated the image")
          row={"event_type":"OBSERVATION","trial":case,"condition":condition,"seed":seed,"arm":arm,"step":step,"frame":str(frame_rel),"frame_sha256":framehash,"reference_sha256":refhash,"width":width,"height":height,"fault":active_fault,"target_generation":seed,"viewport_generation":meta["viewport_generation"],"action":action,"status":status,"points":pts,"feature_vector":fv,"yield_reason":reason if status=="YIELD" else None}
          events.write(json.dumps(row,separators=(",",":"))+"\n")
          if status=="YIELD": stopped=True; break
          if status=="STOP": terminal="STOP_TOLERANCE"; stopped=True; break
          if status=="STEP_LIMIT": terminal="STEP_LIMIT"; stopped=True; break
          actions.append(tuple(action)); yaw+=action[0]; pitch+=action[1]
         # Synthetic actuator's neutral receipt; it is not physical OS release evidence.
         released=True
         events.write(json.dumps({"event_type":"RELEASE","trial":case,"condition":condition,"seed":seed,"arm":arm,"step":step+1,"action":[0.0,0.0],"status":"RELEASE","release_verified":released},separators=(",",":"))+"\n")
         success=(not loss and abs(yaw)<=.025 and abs(pitch)<=.025)
         truths.write(json.dumps({"trial":case,"condition":condition,"seed":seed,"arm":arm,"initial_yaw":y0,"initial_pitch":p0,"focal":focal,"fault":fault,"final_yaw":yaw,"final_pitch":pitch,"corrections":len(actions),"success":success,"target_loss":loss,"terminal":terminal,"release_verified":released,"actions":actions},separators=(",",":"))+"\n")
    print(json.dumps({"allocation":"UNJUNO-8636-ROTATION-FEATURES-T0-A02-20261009","trials":len(conditions)*len(SEEDS)*len(ARMS),"candidate_invocation":1,"output":str(out)},sort_keys=True))

if __name__=="__main__": main()
