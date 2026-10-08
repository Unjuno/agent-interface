#!/usr/bin/python3
from __future__ import annotations
import argparse,json,time
from uno_common import document

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--pipe',required=True); ap.add_argument('--url',required=True); ap.add_argument('--text',default='boox'); a=ap.parse_args()
    c=document(a.pipe,a.url); t0=time.monotonic_ns(); before=str(c.Text.String); locked=bool(c.hasControllersLocked()); c.Text.String=a.text; end=time.monotonic_ns(); after=str(c.Text.String)
    print(json.dumps({'before':before,'after':after,'controllers_locked':locked,'start_ns':t0,'end_ns':end,'elapsed_ns':end-t0},ensure_ascii=True)); return 0
if __name__=='__main__': raise SystemExit(main())
