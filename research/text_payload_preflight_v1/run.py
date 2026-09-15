#!/usr/bin/env python3
"""Finite real-X11 comparison; no model, network, clipboard or keymap mutation."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import secrets
import select
import subprocess
import sys
import time
import traceback
from preflight import deliver, keyboard_mapping, fingerprint, physical_state

HERE = Path(__file__).resolve().parent
BASELINE_BLOB = 'b4f8e043ce4f8929d446e038418ea0fd3655bab0'

def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=True)+'\n')

def load_baseline(path):
    b=path.read_bytes()
    actual=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
    if actual != BASELINE_BLOB:
        raise ValueError('baseline blob mismatch')
    spec=importlib.util.spec_from_file_location('frozen_backend',path)
    m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m)
    class Paced(m.X11Backend):
        def text(self, value):
            for char in value:
                super().text(char)
                time.sleep(.012)
    return Paced

class PrivateDisplay:
    def __init__(self, out): self.out=out; self.procs=[]; self.logs=[]
    def spawn(self, name, cmd, **kw):
        f=(self.out/(name+'.log')).open('w'); self.logs.append(f)
        p=subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, **kw); self.procs.append(p); return p
    def __enter__(self):
        try:
            auth=self.out/'Xauthority'; auth.touch(mode=0o600); self.auth=auth
            cookie=secrets.token_hex(16)
            subprocess.run(['xauth','-f',str(auth),'add',':65500','MIT-MAGIC-COOKIE-1',cookie],check=True,capture_output=True)
            r,w=os.pipe()
            try:
                self.spawn('xvfb',['Xvfb','-displayfd',str(w),'-screen','0','1024x768x24','-nolisten','tcp','-auth',str(auth)],pass_fds=(w,))
                os.close(w); w=-1
                if not select.select([r],[],[],10)[0]: raise TimeoutError('private X server startup')
                number=os.read(r,64).decode().strip()
            finally:
                os.close(r)
                if w>=0: os.close(w)
            self.display=':'+str(int(number))
            subprocess.run(['xauth','-f',str(auth),'add',self.display,'MIT-MAGIC-COOKIE-1',cookie],check=True,capture_output=True)
            self.env=os.environ.copy(); self.env.update(DISPLAY=self.display,XAUTHORITY=str(auth),TERM='dumb')
            self.old_auth=os.environ.get('XAUTHORITY'); os.environ['XAUTHORITY']=str(auth)
            self.spawn('openbox',['openbox'],env=self.env)
            time.sleep(.2)
            return self
        except BaseException:
            self.__exit__(None,None,None); raise
    def __exit__(self,*exc):
        for p in reversed(self.procs):
            if p.poll() is None: p.terminate()
            try:p.wait(timeout=3)
            except subprocess.TimeoutExpired: p.kill(); p.wait()
        for f in self.logs: f.close()
        if hasattr(self,'old_auth'):
            if self.old_auth is None: os.environ.pop('XAUTHORITY',None)
            else: os.environ['XAUTHORITY']=self.old_auth
        if hasattr(self,'auth'): self.auth.unlink(missing_ok=True)

class Consumer:
    def __init__(self, out, env):
        self.log=(out/'receiver.stderr').open('w')
        self.p=subprocess.Popen([sys.executable,str(HERE/'receiver.py')],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.log,text=True,bufsize=1)
    def ask(self, op):
        self.p.stdin.write(json.dumps({'op':op})+'\n'); self.p.stdin.flush()
        if not select.select([self.p.stdout],[],[],8)[0]: raise TimeoutError('receiver IPC')
        line=self.p.stdout.readline()
        if not line: raise RuntimeError('receiver exited')
        return json.loads(line)
    def close(self):
        self.p.terminate()
        try:self.p.wait(timeout=3)
        except subprocess.TimeoutExpired:self.p.kill(); self.p.wait()
        self.log.close()

def owner(d):
    return getattr(d.get_selection_owner(d.intern_atom('CLIPBOARD')), 'id', 0)

def baseline_text(b, text):
    start=b.emissions; error=None
    try:b.execute({'ops':[{'op':'text','text':text},{'op':'release_all'}]})
    except Exception as e:error=str(e)
    state=physical_state(b.d)
    return {'accepted':error is None,'error':error,'emissions':b.emissions-start,
            'physical_after':state,'release_verified':not state['keys'] and not state['mask']}

def prepared_text(b,text,xid,case='valid'):
    return deliver(b,text,target=xid if case!='focus' else 1,observation=4 if case=='stale' else 5,
                   current_observation=5,revision=1 if case=='binding' else 2,current_revision=2,
                   expires_ns=time.monotonic_ns()+(-1 if case=='expired' else 30_000_000_000))

def trial(b,c,text,method,case='valid'):
    initial=c.ask('reset')
    # Tk's internal widget focus is not necessarily the X input-focus window.
    window=b.d.create_resource_object('window',initial['xid'])
    ancestors=[]
    while window.id != b.root.id:
        ancestors.append(window.id); window=window.query_tree().parent
    xid=getattr(b.d.get_input_focus().focus,'id',None)
    if xid not in ancestors: raise RuntimeError('fixture focus outside receiver ancestry')
    before={'mapping':fingerprint(keyboard_mapping(b.d)), 'owner':owner(b.d)}
    t=time.monotonic_ns()
    receipt=baseline_text(b,text) if method=='baseline' else prepared_text(b,text,xid,case)
    elapsed=time.monotonic_ns()-t
    actual=c.ask('observe')
    after={'mapping':fingerprint(keyboard_mapping(b.d)), 'owner':owner(b.d)}
    supported=all(32<=ord(ch)<=126 for ch in text) and case=='valid'
    correct=(receipt['accepted'] and receipt['error'] is None and actual['text']==text) if supported else (not receipt['accepted'] and receipt['emissions']==0 and actual['text']=='' and not actual['keys'])
    controls=(before==after and initial['clipboard']==actual['clipboard'] and receipt['release_verified'])
    return {'method':method,'case':case,'text':text,'actual':actual['text'],'events':actual['keys'],
            'receipt':receipt,'supported':supported,'behavior_correct':correct,'controls_pass':controls,
            'side_state_before':before,'side_state_after':after,'elapsed_ns_diagnostic_only':elapsed}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--baseline',type=Path,required=True)
    ap.add_argument('--source-commit',required=True); ap.add_argument('--smoke',action='store_true'); a=ap.parse_args()
    out=a.out.resolve(); out.mkdir(parents=True,exist_ok=False)
    sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.iterdir() if p.is_file()}
    dump(out/'started.json',{'source_commit':a.source_commit,'smoke':a.smoke,'sources_sha256':sources,'python':sys.version,'platform':platform.platform(),'affinity':sorted(os.sched_getaffinity(0)),'clock':vars(time.get_clock_info('monotonic'))})
    Backend=load_baseline(a.baseline)
    rows=[]
    try:
        with PrivateDisplay(out) as x:
            c=Consumer(out,x.env); b=None
            try:
                first=c.ask('reset'); b=Backend(x.display,{'receiver':first['xid']})
                codes=[ord('_'),ord('\n'),ord('!'),ord('a')] if a.smoke else list(range(128))
                with (out/'trials.jsonl').open('x') as log:
                    for i in codes:
                        # Alternating order reduces systematic method-order effects.
                        methods=['baseline','prepared'] if i%2==0 else ['prepared','baseline']
                        for method in methods:
                            row=trial(b,c,'office'+chr(i)+'tail',method)
                            rows.append(row); log.write(json.dumps(row,ensure_ascii=True)+'\n'); log.flush(); os.fsync(log.fileno())
                    for case in ('stale','binding','expired','focus'):
                        row=trial(b,c,'office', 'prepared',case)
                        rows.append(row); log.write(json.dumps(row)+'\n'); log.flush()
            finally:
                if b is not None:b.close()
                c.close()
        prepared=[r for r in rows if r['method']=='prepared']
        baseline=[r for r in rows if r['method']=='baseline']
        summary={'trials':len(rows),'prepared_pass':sum(r['behavior_correct'] and r['controls_pass'] for r in prepared),'prepared_total':len(prepared),
                 'baseline_pass':sum(r['behavior_correct'] and r['controls_pass'] for r in baseline),'baseline_total':len(baseline),
                 'baseline_partial_rejections':sum(not r['receipt']['accepted'] and bool(r['actual']) for r in baseline),
                 'baseline_wrong_accepted':sum(r['receipt']['accepted'] and r['actual']!=r['text'] for r in baseline),
                 'all_controls_pass':all(r['controls_pass'] for r in rows),'passed':all(r['behavior_correct'] and r['controls_pass'] for r in prepared)}
        dump(out/'summary.json',summary); print(json.dumps(summary),flush=True)
        return 0 if summary['passed'] else 1
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc()); raise

if __name__=='__main__':raise SystemExit(main())
