#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, socket, subprocess, sys, time
from pathlib import Path
from Xlib import X, XK, display
from Xlib.ext import xtest
from model import Policy, decide

DESIRED = 'bookkeeperoffice'
STOPS = (3, 5, 8, 12, 15)
FAULTS = ('clean_stop', 'tail_swallow', 'middle_swallow', 'external_mutation')
POLICIES = (Policy.BLIND_FULL, Policy.SENDER_SUFFIX, Policy.OBSERVED_PREFIX)


def rpc(sock_path: Path, req: dict) -> dict:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(str(sock_path))
    s.sendall((json.dumps(req)+'\n').encode())
    raw = b''
    while b'\n' not in raw:
        raw += s.recv(65536)
    s.close()
    return json.loads(raw.split(b'\n',1)[0].decode())


def mapping_hash(d) -> str:
    info=d.display.info
    rows=[list(r) for r in d.get_keyboard_mapping(info.min_keycode, info.max_keycode-info.min_keycode+1)]
    return hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()


def physical_state(d) -> dict:
    bits=d.query_keymap(); mask=int(d.screen().root.query_pointer().mask)
    keys=[k for k in range(8,256) if bits[k//8] & (1<<(k%8))]
    return {'keys':keys,'mask':mask}


def keycode(d, ch: str) -> int:
    sym=XK.string_to_keysym(ch)
    code=d.keysym_to_keycode(sym)
    if not code: raise RuntimeError('unmapped '+repr(ch))
    return code


def focus(d, xid: int):
    w=d.create_resource_object('window', xid)
    w.set_input_focus(X.RevertToParent, X.CurrentTime); d.sync()
    got=getattr(d.get_input_focus().focus,'id',None)
    if got != xid: raise RuntimeError(f'focus mismatch {got} != {xid}')


def type_text(d, xid: int, text: str, pacing: float) -> int:
    focus(d,xid)
    chars=0
    for ch in text:
        code=keycode(d,ch)
        xtest.fake_input(d,X.KeyPress,code); d.sync()
        xtest.fake_input(d,X.KeyRelease,code); d.sync()
        chars += 1
        if pacing: time.sleep(pacing)
    return chars


def expected(policy: Policy, fault: str) -> str:
    if policy is Policy.OBSERVED_PREFIX:
        return 'refuse' if fault in ('middle_swallow','external_mutation') else 'exact'
    if policy is Policy.SENDER_SUFFIX:
        return 'exact' if fault == 'clean_stop' else 'wrong'
    return 'wrong'


def wait_ready(path: Path, timeout=8.0):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if path.exists(): return json.loads(path.read_text())
        time.sleep(.02)
    raise RuntimeError('receiver not ready')


def run(out: Path, display_name: str, pacing: float) -> dict:
    out.mkdir(parents=True,exist_ok=False)
    sock=out/'receiver.sock'; ready=out/'ready.json'
    env=os.environ.copy(); env['DISPLAY']=display_name
    recv=subprocess.Popen([sys.executable,str(Path(__file__).with_name('receiver.py')),'--socket',str(sock),'--ready',str(ready)],env=env,stdout=(out/'receiver.stdout').open('w'),stderr=(out/'receiver.stderr').open('w'))
    try:
        meta=wait_ready(ready); xid=int(meta['xid'])
        d=display.Display(display_name); before_map=mapping_hash(d)
        rows=[]; tid=0
        for stop in STOPS:
            for fault in FAULTS:
                for policy in POLICIES:
                    tid += 1
                    swallow = stop if fault=='tail_swallow' else (max(1,stop//2) if fault=='middle_swallow' else None)
                    rpc(sock,{'cmd':'reset','swallow_at':swallow}); time.sleep(.02)
                    pre_state=physical_state(d)
                    sent=type_text(d,xid,DESIRED[:stop],pacing)
                    initial=rpc(sock,{'cmd':'get'})
                    if fault=='external_mutation':
                        tamper=DESIRED[:max(1,stop-2)]+'x'
                        rpc(sock,{'cmd':'set','text':tamper}); initial=rpc(sock,{'cmd':'get'})
                    observed=str(initial['text'])
                    dec=decide(policy,DESIRED,sent,observed)
                    before_recovery_events=int(initial['event_count'])
                    recovery_chars=0
                    if dec.accepted and dec.text:
                        recovery_chars=type_text(d,xid,dec.text,pacing)
                    final=rpc(sock,{'cmd':'get'})
                    post_state=physical_state(d)
                    final_text=str(final['text'])
                    mode=expected(policy,fault)
                    exact=final_text==DESIRED
                    recovery_input=int(final['event_count'])-before_recovery_events
                    if mode=='exact': pass_gate=dec.accepted and exact
                    elif mode=='wrong': pass_gate=dec.accepted and not exact
                    else: pass_gate=(not dec.accepted and recovery_input==0 and final_text==observed)
                    rows.append({
                        'id':f't{tid:03d}','stop':stop,'fault':fault,'policy':policy.value,'sent_count':sent,
                        'observed_before_recovery':observed,'decision':{'accepted':dec.accepted,'text':dec.text,'reason':dec.reason},
                        'recovery_chars_sent':recovery_chars,'recovery_receiver_events':recovery_input,
                        'final_text':final_text,'exact':exact,'expected_mode':mode,'gate_pass':pass_gate,
                        'pre_state':pre_state,'post_state':post_state,'initial_event_count':initial['event_count'],'final_event_count':final['event_count'],
                    })
        after_map=mapping_hash(d); final_state=physical_state(d); d.close()
        counts={}
        for p in POLICIES:
            rs=[r for r in rows if r['policy']==p.value]
            counts[p.value]={'gate_pass':sum(r['gate_pass'] for r in rs),'total':len(rs),'exact':sum(r['exact'] for r in rs),'refusals':sum(not r['decision']['accepted'] for r in rs)}
        report={'schema':'agent-interface/text-observed-prefix-resume-v1','desired':DESIRED,'stops':STOPS,'faults':FAULTS,'trials':len(rows),'counts':counts,
                'all_gates_pass':all(r['gate_pass'] for r in rows),'map_unchanged':before_map==after_map,'final_state':final_state,'rows':rows}
        (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        return report
    finally:
        try: rpc(sock,{'cmd':'shutdown'})
        except Exception: pass
        try: recv.wait(timeout=2)
        except Exception: recv.kill()


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--display',required=True); ap.add_argument('--pacing-ms',type=float,default=3.0)
    a=ap.parse_args(); rep=run(a.out.resolve(),a.display,a.pacing_ms/1000.0); print(json.dumps({k:rep[k] for k in ('trials','counts','all_gates_pass','map_unchanged','final_state')},indent=2)); return 0 if rep['all_gates_pass'] and rep['map_unchanged'] and not rep['final_state']['keys'] and rep['final_state']['mask']==0 else 1
if __name__=='__main__': raise SystemExit(main())
