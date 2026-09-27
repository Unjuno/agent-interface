#!/usr/bin/env python3
"""Bounded real Writer transfer. Scoring occurs in another process after input."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from odf.opendocument import OpenDocumentText
from odf.text import P, S
from Xlib import X
from Xlib.protocol import event
from run import PrivateDisplay, Consumer, load_baseline, dump, baseline_text, prepared_text, owner
from preflight import keyboard_mapping, fingerprint

HERE=Path(__file__).resolve().parent

def find_writer(d):
    end=time.monotonic()+15
    def walk(w):
        for c in w.query_tree().children:
            try:
                cls=c.get_wm_class()
                if cls and any('libreoffice-writer' in x.lower() for x in cls):return c
                found=walk(c)
                if found:return found
            except Exception:continue
        return None
    while time.monotonic()<end:
        found=walk(d.screen().root)
        if found:return found
        time.sleep(.1)
    raise RuntimeError('Writer window not found')

def activate(b,win):
    b.root.send_event(event.ClientMessage(window=win,client_type=b.d.intern_atom('_NET_ACTIVE_WINDOW'),data=(32,[1,X.CurrentTime,0,0,0])),event_mask=X.SubstructureRedirectMask|X.SubstructureNotifyMask)
    b.d.sync(); time.sleep(.2)
    win.set_input_focus(X.RevertToParent,X.CurrentTime); b.d.sync()
    b.key_chord(['CTRL','End']); time.sleep(.15)
    target=getattr(b.d.get_input_focus().focus,'id',None)
    if target != win.id:raise RuntimeError('unexpected Writer input focus')
    return target

def arm(out,Backend,text,method):
    out.mkdir()
    odt=out/'task.odt'
    doc=OpenDocumentText(); p=P(text='sentinel'); p.addElement(S()); doc.text.addElement(p); doc.save(str(odt))
    with PrivateDisplay(out) as x:
        c=Consumer(out,x.env); b=None
        try:
            initial=c.ask('reset'); b=Backend(x.display,{})
            x.spawn('writer',['libreoffice', '-env:UserInstallation='+(out/'profile').as_uri(),'--nologo','--nodefault','--nofirststartwizard','--norestore',str(odt)],env=x.env)
            win=find_writer(b.d); time.sleep(.4); target=activate(b,win)
            before={'owner':owner(b.d),'mapping':fingerprint(keyboard_mapping(b.d))}
            receipt=baseline_text(b,text) if method=='baseline' else prepared_text(b,text,target)
            after={'owner':owner(b.d),'mapping':fingerprint(keyboard_mapping(b.d))}
            clip=c.ask('observe')['clipboard']
            # Save is an explicitly separate fixture operation, not a text emission.
            b.key_chord(['CTRL','s']); time.sleep(1)
            allowed=all(32<=ord(ch)<=126 for ch in text)
            expected='sentinel '+(text if allowed else '')
            raw=subprocess.run([sys.executable,str(HERE/'score_odt.py'),str(odt),'--expected',expected],capture_output=True,text=True,check=True)
            score=json.loads(raw.stdout)
            controls=(before==after and clip==initial['clipboard'] and receipt['release_verified'])
            behavior=score['exact'] and ((receipt['accepted'] and not receipt['error']) if allowed else (not receipt['accepted'] and receipt['emissions']==0))
            row={'method':method,'text':text,'receipt':receipt,'score':score,'side_state_before':before,'side_state_after':after,'controls_pass':controls,'behavior_correct':behavior}
            dump(out/'receipt.json',row)
            return row
        finally:
            if b is not None:b.close()
            c.close()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--baseline',type=Path,required=True); ap.add_argument('--source-commit',required=True); a=ap.parse_args()
    out=a.out.resolve(); out.mkdir(parents=True,exist_ok=False)
    dump(out/'started.json',{'source_commit':a.source_commit,'conditions':['office_tail','office\ntail','office!tail'],'methods':['baseline','prepared'],'order':'case-major; baseline then prepared; one session each'})
    Backend=load_baseline(a.baseline); rows=[]
    for i,text in enumerate(['office_tail','office\ntail','office!tail']):
        for method in ['baseline','prepared']:
            row=arm(out/f'{i}-{method}',Backend,text,method); rows.append(row)
            print(json.dumps({'case':i,'method':method,'actual':row['score']['actual'],'pass':row['behavior_correct']},ensure_ascii=True),flush=True)
    summary={'rows':rows,'prepared_pass':all(r['behavior_correct'] and r['controls_pass'] for r in rows if r['method']=='prepared'),'all_controls_pass':all(r['controls_pass'] for r in rows)}
    dump(out/'summary.json',summary)
    return 0 if summary['prepared_pass'] and summary['all_controls_pass'] else 1

if __name__=='__main__':raise SystemExit(main())
