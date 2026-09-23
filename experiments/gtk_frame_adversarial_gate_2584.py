"""Bounded local GTK/X11 adversarial gate preflight for #2584."""
import hashlib,json,os
import numpy as np
from Xlib import X,display
import gi
gi.require_version("Gtk","3.0")
from gi.repository import Gtk
def cap(w,d):
 w.get_window().process_all_updates();d.sync();raw=d.screen().root.get_image(0,0,320,180,X.ZPixmap,0xffffffff)
 return np.frombuffer(raw.data,dtype=np.uint8)[:320*180*4].reshape(180,320,4)[:,:,:3].astype(np.float32)/255
def main():
 os.environ.setdefault("DISPLAY",":99");Gtk.init([]);win=Gtk.Window();win.set_default_size(320,180);label=Gtk.Label(label="TARGET");win.add(label);win.show_all()
 for _ in range(10):Gtk.main_iteration_do(False)
 d=display.Display();pos=np.stack([cap(win,d) for _ in range(8)]);x=pos.reshape(8,-1);xx=np.r_[x,np.zeros_like(x)];y=np.r_[np.ones(8),np.zeros(8)]
 r=np.random.default_rng(12);w=r.normal(0,.02,x.shape[1]);b=0.
 for _ in range(80):
  p=1/(1+np.exp(-np.clip(xx@w+b,-30,30)));g=(p-y)/len(y);w-=.3*xx.T@g;b-=.3*g.sum()
 rows=[]
 for name,text,ok,fresh in [("valid","TARGET",1,1),("stale","TARGET",1,0),("tampered","TARGET",0,1),("other","OTHER",0,1)]:
  label.set_text(text);label.show()
  for _ in range(4):Gtk.main_iteration_do(False)
  p=float(1/(1+np.exp(-np.clip(cap(win,d).reshape(-1)@w+b,-30,30))))
  rec={"saved":bool(ok),"text":text};sha=hashlib.sha256(json.dumps(rec,sort_keys=True).encode()).hexdigest()
  rows.append({"case":name,"p":p,"model_accept":p>=.75,"receipt_ok":bool(ok),"fresh":bool(fresh),"final_accept":bool(p>=.75 and ok and fresh),"sha256":sha})
 print(json.dumps({"rows":rows,"scope":"local GTK/X11 captured frame adversarial gate"},sort_keys=True,indent=2))
if __name__=="__main__":main()
