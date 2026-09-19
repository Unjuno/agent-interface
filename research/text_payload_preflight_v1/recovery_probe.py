#!/usr/bin/env python3
"""Candidate-only validation after loss of the original disposable workspace."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import select
import subprocess
import sys
import time
from types import SimpleNamespace
import traceback
from Xlib import display
import Xlib
from preflight import deliver, fingerprint, keyboard_mapping

HERE=Path(__file__).resolve().parent
DEPS={'preflight.py':'35c7375e50f3e0c58f57c8139a6dc8abeef87771',
      'receiver.py':'decce092c4f5b4d93031059c5ecb84151e11f8b8',
      'test_preflight.py':'d98aaa58dcd3a5b5ef84d3441d895de45e62431e'}

def dump(path,value):
    path.write_text(json.dumps(value,indent=2,ensure_ascii=True)+'\n')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--source-commit',required=True); a=ap.parse_args()
    if os.environ.get('AGENT_INTERFACE_PRIVATE_XVFB')!='1' or not os.environ.get('XAUTHORITY'):
        raise RuntimeError('Use the documented private xvfb-run invocation')
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    hashes={}
    for name,expected in DEPS.items():
        data=(HERE/name).read_bytes();actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if actual!=expected:raise RuntimeError('source mismatch: '+name)
        hashes[name]=actual
    hashes['recovery_probe.py.sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    cpu=next((line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')), 'unknown')
    dump(out/'started.json',{'source_commit':a.source_commit,'dependency_blobs':hashes,'python':sys.version,'platform':platform.platform(),'xlib_module_version':Xlib.__version__,'cpu':cpu,'affinity':sorted(os.sched_getaffinity(0)),'clock_frequency_controlled':False,'pacing_s':.012,'scope':'candidate only; no baseline comparison or Office formal run'})
    tests=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(HERE),'-p','test_preflight.py','-v'],capture_output=True,text=True)
    (out/'unittest.txt').write_text(tests.stdout+tests.stderr);(out/'unit.exitcode').write_text(str(tests.returncode))
    if tests.returncode:raise RuntimeError('unit tests failed')
    logs=[];processes=[];d=None
    try:
        log=(out/'openbox.log').open('w');logs.append(log)
        processes.append(subprocess.Popen(['openbox'],stdout=log,stderr=subprocess.STDOUT));time.sleep(.2)
        log=(out/'receiver.stderr').open('w');logs.append(log)
        p=subprocess.Popen([sys.executable,str(HERE/'receiver.py')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,text=True,bufsize=1);processes.append(p)
        def ask(op):
            p.stdin.write(json.dumps({'op':op})+'\n');p.stdin.flush()
            if not select.select([p.stdout],[],[],8)[0]:raise TimeoutError('receiver')
            return json.loads(p.stdout.readline())
        first=ask('reset');d=display.Display();backend=SimpleNamespace(d=d,emissions=0)
        root=d.screen().root
        def owner():return getattr(d.get_selection_owner(d.intern_atom('CLIPBOARD')),'id',0)
        cases=[('codepoint-'+str(i),'office'+chr(i)+'tail',32<=i<=126) for i in range(128)]
        cases += [(name,'office',False) for name in ('stale','binding','expired','focus')]
        rows=[]
        with (out/'trials.jsonl').open('x') as f:
            for name,text,supported in cases:
                initial=ask('reset');w=d.create_resource_object('window',initial['xid']);ancestors=[]
                while w.id!=root.id:
                    ancestors.append(w.id);w=w.query_tree().parent
                target=getattr(d.get_input_focus().focus,'id',None)
                if target not in ancestors:raise RuntimeError('focus outside receiver ancestry')
                before={'map':fingerprint(keyboard_mapping(d)),'clipboard_owner':owner(),'clipboard_text':initial['clipboard']}
                r=deliver(backend,text,target=1 if name=='focus' else target,observation=4 if name=='stale' else 5,current_observation=5,revision=1 if name=='binding' else 2,current_revision=2,expires_ns=time.monotonic_ns()+(-1 if name=='expired' else 30_000_000_000))
                observed=ask('observe')
                after={'map':fingerprint(keyboard_mapping(d)),'clipboard_owner':owner(),'clipboard_text':observed['clipboard']}
                behavior=(r['accepted'] and not r['error'] and observed['text']==text) if supported else (not r['accepted'] and r['emissions']==0 and observed['text']=='' and observed['keys']==[])
                controls=before==after and r['release_verified']
                row={'id':name,'requested':text,'supported':supported,'actual':observed['text'],'events':observed['keys'],'receipt':r,'before':before,'after':after,'behavior_pass':behavior,'controls_pass':controls}
                rows.append(row);f.write(json.dumps(row,ensure_ascii=True)+'\n');f.flush();os.fsync(f.fileno())
        summary={'result_id':out.name,'source_commit':a.source_commit,'trials':len(rows),'exact_supported':sum(r['supported'] and r['behavior_pass'] for r in rows),'supported_total':sum(r['supported'] for r in rows),'zero_effect_rejections':sum(not r['supported'] and r['behavior_pass'] for r in rows),'rejections_total':sum(not r['supported'] for r in rows),'controls_pass':sum(r['controls_pass'] for r in rows),'pass':all(r['behavior_pass'] and r['controls_pass'] for r in rows)}
        dump(out/'summary.json',summary);print(json.dumps(summary),flush=True)
        return 0 if summary['pass'] else 1
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        if d:d.close()
        for p in reversed(processes):
            if p.poll() is None:p.terminate()
            try:p.wait(timeout=3)
            except subprocess.TimeoutExpired:p.kill();p.wait()
        for f in logs:f.close()

if __name__=='__main__':raise SystemExit(main())
