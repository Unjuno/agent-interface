"""Bounded local GTK/X11 binary model and receipt gate preflight."""
import hashlib,json,os
import numpy as np
from Xlib import X,display
import gi
gi.require_version("Gtk","3.0");from gi.repository import Gtk
def cap(w,d):
 w.get_window().process_all_updates();d.sync();raw=d.screen().root.get_image(0,0,320,180,X.ZPixmap,0xffffffff)
 return np.frombuffer(raw.data,dtype=np.uint8)[:230400].reshape(180,320,4)[:,:,:3].astype(np.float32)/255
def main():
 os.environ.setdefault("DISPLAY",":99");Gtk.init([]);win=Gtk.Window();win.set_default_size(320,180);lab=Gtk.Label();win.add(lab);css=Gtk.CssProvider();win.get_style_context().add_provider(css,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION);win.show_all()
 for _ in range(10):Gtk.main_iteration_do(False)
 d=display.Display();frames=[];ys=[]
 for color,text,y in [("#22cc44","TARGET",1),("#2244cc","OTHER",0)]:
  css.load_from_data(("* { background-color: %s; color: #ffffff; }"%color).encode());lab.set_text(text);lab.show()
  for _ in range(8):Gtk.main_iteration_do(False)
  frames.extend([cap(win,d) for _ in range(8)]);ys.extend([y]*8)
 x=np.stack(frames).reshape(16,-1);y=np.array(ys);r=np.random.default_rng(22);w=r.normal(0,.02,x.shape[1]);b=0.
 for _ in range(100):
  p=1/(1+np.exp(-np.clip(x@w+b,-30,30)));g=(p-y)/len(y);w-=.3*x.T@g;b-=.3*g.sum()
 rows=[]
 for name,color,text,ok,fresh in [("target-valid","#22cc44","TARGET",1,1),("other-valid","#2244cc","OTHER",1,1),("target-stale","#22cc44","TARGET",1,0),("target-tampered","#22cc44","TARGET",0,1)]:
  css.load_from_data(("* { background-color: %s; color: #ffffff; }"%color).encode());lab.set_text(text);lab.show()
  for _ in range(8):Gtk.main_iteration_do(False)
  frame=cap(win,d);p=float(1/(1+np.exp(-np.clip(frame.reshape(-1)@w+b,-30,30))));rec={"saved":bool(ok),"text":text}
  rows.append({"case":name,"p_target":p,"model_accept":p>=.75,"receipt_ok":bool(ok),"fresh":bool(fresh),"final_accept":bool(p>=.75 and ok and fresh),"frame_sha256":hashlib.sha256(frame.tobytes()).hexdigest(),"receipt_sha256":hashlib.sha256(json.dumps(rec,sort_keys=True).encode()).hexdigest()})
 print(json.dumps({"train_frames":16,"rows":rows,"scope":"local GTK/X11 visually distinct binary model plus receipt/freshness gate"},indent=2,sort_keys=True));win.destroy()
if __name__=="__main__":main()
