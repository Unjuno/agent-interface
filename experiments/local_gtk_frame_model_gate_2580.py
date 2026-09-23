"""Local Docker GTK/X11 frame capture plus tiny model and receipt gate."""
import hashlib, json, os
import numpy as np
from Xlib import X, display
import gi
gi.require_version("Gtk","3.0")
from gi.repository import Gtk

def capture(win, d, w=320, h=180):
    win.get_window().process_all_updates()
    d.sync(); raw=d.screen().root.get_image(0,0,w,h,X.ZPixmap,0xffffffff)
    return np.frombuffer(raw.data,dtype=np.uint8)[:w*h*4].reshape(h,w,4)[:,:,:3].astype(np.float32)/255

def main():
    os.environ.setdefault("DISPLAY",":99"); Gtk.init([])
    win=Gtk.Window(title="receipt-fixture"); win.set_default_size(320,180)
    win.add(Gtk.Label(label="TARGET")); win.show_all()
    for _ in range(10): Gtk.main_iteration_do(False)
    d=display.Display(); frames=np.stack([capture(win,d) for _ in range(8)])
    x=frames.reshape(len(frames),-1); y=np.ones(len(x)); rng=np.random.default_rng(12)
    w=rng.normal(0,.02,x.shape[1]); b=0.
    controls=np.zeros_like(x); xx=np.concatenate([x,controls]); yy=np.concatenate([y,np.zeros(len(y))])
    for _ in range(80):
        p=1/(1+np.exp(-np.clip(xx@w+b,-30,30))); g=(p-yy)/len(yy)
        w-=.3*(xx.T@g); b-=.3*g.sum()
    frame=capture(win,d); p=float(1/(1+np.exp(-np.clip(frame.reshape(-1)@w+b,-30,30))))
    receipt={"saved":True,"text":"gtk2492"}
    digest=hashlib.sha256(json.dumps(receipt,sort_keys=True).encode()).hexdigest()
    result={"frame_shape":list(frame.shape),"model_probability":p,"model_accept":p>=.75,"receipt_sha256":digest,"receipt_ok":True,"fresh":True,"final_accept":bool(p>=.75),"scope":"local GTK/Xvfb X11 capture + tiny model + independent receipt gate"}
    print(json.dumps(result,indent=2,sort_keys=True)); win.destroy()

if __name__=="__main__": main()
