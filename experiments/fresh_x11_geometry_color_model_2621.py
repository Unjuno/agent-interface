"""Fresh direct-X11 client geometry/color model preflight (#2621)."""
import hashlib,json,os,time
import numpy as np
from Xlib import X,display
def cap(d):
 raw=d.screen().root.get_image(0,0,320,180,X.ZPixmap,0xffffffff);return np.frombuffer(raw.data,dtype=np.uint8)[:230400].reshape(180,320,4)[:,:,:3].astype(np.float32)/255
def make(d,x,y,w,h,c):
 s=d.screen();q=s.root.create_window(x,y,w,h,0,s.root_depth,X.InputOutput,s.root_visual,background_pixel=c);q.map();d.sync();time.sleep(.02);f=cap(d);q.destroy();d.sync();return f
def main():
 os.environ.setdefault("DISPLAY",":99");d=display.Display();spec=[(20,20,80,50,0x22cc44),(100,20,60,40,0x55dd66),(220,20,30,20,0x33bb55),(20,110,50,30,0x66ee77),(180,90,90,60,0x22cc44)]
 fs=[];ys=[]
 for _ in range(3):
  for z in spec:fs.append(make(d,*z));ys.append(1)
  for i,z in enumerate(spec):fs.append(make(d,z[0],z[1],z[2],z[3],0x2244cc+(i%2)*0x111100));ys.append(0)
 x=np.stack(fs).reshape(30,-1);y=np.array(ys);r=np.random.default_rng(99);w=r.normal(0,.02,x.shape[1]);b=0.
 for _ in range(150):
  p=1/(1+np.exp(-np.clip(x@w+b,-30,30)));g=(p-y)/len(y);w-=.25*x.T@g;b-=.25*g.sum()
 rows=[]
 for name,z,fresh in [("green-heldout",(140,120,70,25,0x44cc66),1),("blue-heldout",(140,120,70,25,0x4455cc),1),("green-stale",(140,120,70,25,0x44cc66),0)]:
  f=make(d,*z);p=float(1/(1+np.exp(-np.clip(f.reshape(-1)@w+b,-30,30))));rows.append({"case":name,"p_target":p,"model_accept":p>=.75,"fresh":bool(fresh),"final_accept":bool(p>=.75 and fresh),"frame_sha256":hashlib.sha256(f.tobytes()).hexdigest()})
 print(json.dumps({"train_n":30,"rows":rows,"scope":"fresh direct X11 client geometry/color model"},indent=2,sort_keys=True))
if __name__=="__main__":main()
