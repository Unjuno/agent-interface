from __future__ import annotations
import argparse,json,signal,sys,tkinter as tk

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--display',required=True);a=ap.parse_args()
    root=tk.Tk(screenName=a.display);root.title('A');root.geometry('220x140+20+20')
    b=tk.Toplevel(root);b.title('B');b.geometry('220x140+320+20')
    root.update_idletasks();root.update()
    print(json.dumps({'aid':int(root.winfo_id()),'bid':int(b.winfo_id())}),flush=True)
    def stop(*_):
        try: root.after(0,root.destroy)
        except Exception: pass
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    try: root.mainloop()
    except Exception: pass
if __name__=='__main__': main()
