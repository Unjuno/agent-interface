"""Direct X11 client geometry capture preflight (#2609)."""
import hashlib,json,os,time
import numpy as np
from Xlib import X,display
def cap(d):
 d.sync();raw=d.screen().root.get_image(0,0,320,180,X.ZPixmap,0xffffffff)
 return np.frombuffer(raw.data,dtype=np.uint8)[:230400].reshape(180,320,4)[:,:,:3]
def main():
 os.environ.setdefault("DISPLAY",":99");d=display.Display();root=d.screen().root;w=root.create_window(20,20,80,50,0,root.root_depth,X.InputOutput,root.root_visual,background_pixel=0x22cc44);w.map();d.sync();time.sleep(.1);frames=[cap(d)]
 w.configure(x=220,y=110,width=30,height=20);d.sync();time.sleep(.1);frames.append(cap(d))
 w.unmap();d.sync();time.sleep(.1);frames.append(cap(d))
 print(json.dumps({"hashes":[hashlib.sha256(f.tobytes()).hexdigest() for f in frames],"deltas":[float(np.abs(frames[0].astype(float)-f.astype(float)).mean()) for f in frames],"scope":"direct X11 client geometry preflight"},indent=2,sort_keys=True));w.destroy();d.close()
if __name__=="__main__":main()
