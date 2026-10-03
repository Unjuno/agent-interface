"""Disposable application, with a single-clock atomic effect admission boundary."""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from pathlib import Path

class Trial:
    def __init__(self,spec,clock=time.monotonic_ns,sleep=time.sleep):
        self.spec=spec;self.clock=clock;self.sleep=sleep
        self.origin=None;self.target=None;self.effects=[];self.events=[]
        self.busy=False;self.revealed=False;self.lock=threading.RLock()
    def elapsed(self): return self.clock()-self.origin
    def log(self,name,**values):
        self.events.append(dict(event=name,ns=self.elapsed(),**values))
    def start(self):
        with self.lock:
            if self.origin is not None: raise ValueError('already started')
            self.origin=self.clock();self.events.append(dict(event='start',ns=0))
    def signal(self):
        with self.lock:
            if self.origin is None or self.elapsed()<self.spec['signal_ms']*1_000_000: return 'PENDING'
            if not self.revealed:
                self.log('signal',value=self.spec['signal']);self.revealed=True
            return self.spec['signal']
    def work(self,name,target,ms):
        if target not in ('A','B'): raise ValueError('invalid target')
        with self.lock:
            if self.origin is None or self.busy or self.effects: raise ValueError('invalid work state')
            if (name=='prepare') != (self.target is None): raise ValueError('invalid work phase')
            self.busy=True;self.log(name+'_start',target=target)
        self.sleep(ms/1000)
        with self.lock:
            self.target=target;self.busy=False;self.log(name+'_end',target=target)
    def prepare(self,target): self.work('prepare',target,self.spec['preparation_ms'])
    def edit(self,target): self.work('edit',target,self.spec['edit_ms'])
    def commit(self):
        with self.lock:
            now=self.elapsed()
            status=('duplicate' if self.effects else 'unprepared' if self.target is None or self.busy
                    else 'deadline' if now>self.spec['deadline_ms']*1_000_000 else 'committed')
            self.events.append(dict(event='commit',ns=now,target=self.target,status=status))
            if status=='committed': self.effects.append(dict(ns=now,target=self.target))
            return status

HTML='''<!doctype html><meta charset="utf-8"><title>Disposable staged form</title>
<h1>Local fixture only</h1><button id="start">Start</button>
<div>Signal: <output id="signal">PENDING</output></div>
<label>Draft <select id="target"><option>A</option><option>B</option></select></label>
<button id="prepare" disabled>Prepare</button><button id="edit" disabled>Edit</button>
<button id="commit" disabled>Commit</button><output id="state">IDLE</output>
<script>
const trial=new URLSearchParams(location.search).get('trial');
const el=id=>document.getElementById(id);
async function api(op,target){const response=await fetch('/op?trial='+encodeURIComponent(trial),
 {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op,target})});
 if(!response.ok)throw Error(await response.text());return response.json();}
el('start').onclick=async()=>{try{await api('start');el('start').disabled=true;el('prepare').disabled=false;
 el('state').textContent='STARTED';poll();}catch(e){el('state').textContent='ERROR:'+e.message;}};
async function poll(){const r=await fetch('/signal?trial='+encodeURIComponent(trial));const value=(await r.json()).value;
 el('signal').textContent=value;if(value==='PENDING')setTimeout(poll,10);}
async function work(op){el('state').textContent='BUSY';el('prepare').disabled=el('edit').disabled=el('commit').disabled=true;
 try{await api(op,el('target').value);el('state').textContent='READY';el('edit').disabled=el('commit').disabled=false;}
 catch(e){el('state').textContent='ERROR:'+e.message;}}
el('prepare').onclick=()=>work('prepare');el('edit').onclick=()=>work('edit');
el('commit').onclick=async()=>{try{const r=await api('commit');el('state').textContent=r.status.toUpperCase();
 el('edit').disabled=el('commit').disabled=true;}catch(e){el('state').textContent='ERROR:'+e.message;}};
</script>'''

def make_server(trials):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def reply(self,obj,status=200):
            data=json.dumps(obj).encode();self.send_response(status)
            self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)))
            self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
        def do_GET(self):
            parsed=urlparse(self.path)
            if parsed.path=='/':
                data=HTML.encode();self.send_response(200);self.send_header('Content-Type','text/html')
                self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
            if parsed.path=='/signal':
                try: self.reply({'value':trials[parse_qs(parsed.query)['trial'][0]].signal()})
                except (KeyError,ValueError) as e:self.reply({'error':str(e)},400)
                return
            self.reply({'error':'not found'},404)
        def do_POST(self):
            try:
                parsed=urlparse(self.path)
                if parsed.path!='/op':raise ValueError('invalid endpoint')
                n=int(self.headers['Content-Length'])
                if n>1024:raise ValueError('request too big')
                body=json.loads(self.rfile.read(n));trial=trials[parse_qs(parsed.query)['trial'][0]]
                op=body['op']
                if op=='start':trial.start();value={}
                elif op=='prepare':trial.prepare(body['target']);value={}
                elif op=='edit':trial.edit(body['target']);value={}
                elif op=='commit':value={'status':trial.commit()}
                else:raise ValueError('unknown operation')
                self.reply(value)
            except (KeyError,ValueError,TypeError) as e:self.reply({'error':str(e)},400)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    return server,thread
