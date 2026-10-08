#!/usr/bin/env python3
import argparse, json, os, time, tkinter as tk
from pathlib import Path
from Xlib import display

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--display',required=True); ap.add_argument('--text',required=True); ap.add_argument('--ready',type=Path,required=True); a=ap.parse_args()
    os.environ['DISPLAY']=a.display
    root=tk.Tk(); root.withdraw(); root.clipboard_clear(); root.clipboard_append(a.text); root.update()
    d=display.Display(a.display); owner=d.get_selection_owner(d.intern_atom('CLIPBOARD')); oid=getattr(owner,'id',None); d.close()
    a.ready.write_text(json.dumps({'owner_id':oid,'text':a.text},ensure_ascii=False)+'\n',encoding='utf-8')
    try:
        while True:
            root.update(); time.sleep(.01)
    except (tk.TclError, KeyboardInterrupt):
        pass
if __name__=='__main__': main()
