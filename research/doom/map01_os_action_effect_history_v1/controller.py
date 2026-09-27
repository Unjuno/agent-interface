from pathlib import Path
import argparse,json,time,hashlib
import numpy as np
from PIL import Image
from common import Inputs,write

def desc_img(p):
    arr=np.asarray(Image.open(p).convert('RGB'));im=Image.fromarray(arr[20:340,70:570]).convert('L').resize((32,20),Image.Resampling.BILINEAR);return np.asarray(im,dtype=np.float32).ravel()/255.0,hashlib.sha256(arr.tobytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--context',required=True);p.add_argument('--evidence',required=True);p.add_argument('--calibration',required=True);p.add_argument('--mode',choices=['current','history'],required=True);p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
 ctx=json.loads(Path(a.context).read_text());ev=json.loads(Path(a.evidence).read_text());cal=np.load(a.calibration);events=[];inp=Inputs(a.source,ctx,events);decision='UNSET';pred=None;use=0
 try:
  now=time.perf_counter_ns();age=now-int(ev['current_capture_ns'])
  if age>500_000_000: raise RuntimeError('stale_observation')
  pd,ph=desc_img(ev['previous_path']);cd,ch=desc_img(ev['current_path'])
  if ph!=ev['previous_rgb_sha256'] or ch!=ev['current_rgb_sha256']:raise RuntimeError('image_hash_mismatch')
  feat=cd if a.mode=='current' else cd-pd;cents=[cal['current_open'],cal['current_close']] if a.mode=='current' else [cal['history_open'],cal['history_close']];mse=[float(np.mean((feat-c)**2)) for c in cents];pred=int(np.argmin(mse))
  if pred==0:time.sleep(15/35)
  else:inp.press('e',.03,0,'state_repair');use=1
  inp.press('w',.5,0,'door_transit');inp.press('w',.5,0,'door_transit');decision='PROGRAM_COMPLETE'
 except Exception as exc:
  age=locals().get('age');mse=locals().get('mse');decision='YIELD';events.append({'kind':'error','detail':repr(exc)})
 finally:
  inp.close();rs=[r for r in inp.owner.records if r['event']=='owner_release'];write(out/'trace.json',{'mode':a.mode,'decision':decision,'predicted_label':pred,'use_count':use,'centroid_mse':mse,'observation_age_ns_at_start':age,'evidence':ev,'events':events,'owner_records':inp.owner.records,'all_release_verified':all(r.get('verified') and not r.get('keys_down') and not r.get('buttons_down') for r in rs)});print(json.dumps({'decision':decision,'predicted_label':pred,'use_count':use,'age_ns':age}))
if __name__=='__main__':main()
