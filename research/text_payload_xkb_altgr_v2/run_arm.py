from __future__ import annotations
import argparse, hashlib, json, os, socket, subprocess, sys, time
from pathlib import Path
from types import SimpleNamespace
from Xlib import X, display
import candidate, projection
HERE=Path(__file__).resolve().parent

def sha(b:bytes): return hashlib.sha256(b).hexdigest()
def rpc(path,obj):
    s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); end=time.monotonic()+3
    while True:
        try:s.connect(path);break
        except OSError:
            if time.monotonic()>=end:raise
            time.sleep(.01)
    s.sendall((json.dumps(obj)+'\n').encode()); data=b''
    while not data.endswith(b'\n'): data+=s.recv(65536)
    s.close(); return json.loads(data.decode())

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--rep',type=int,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    a.out=a.out.resolve(); a.out.mkdir(parents=True,exist_ok=False)
    if not os.environ.get('DISPLAY') or not os.environ.get('XAUTHORITY'): raise RuntimeError('private xvfb-run required')
    schedule=json.loads((HERE/'schedule.json').read_text()); payloads=schedule['payloads']; order=schedule['orders'][a.rep]
    d=display.Display(os.environ['DISPLAY']); info=d.display.info; first=info.min_keycode; baseline=candidate.keyboard_mapping(d)
    xkb_text=projection.resolve_xkb(os.environ['DISPLAY'],os.environ['XAUTHORITY'],schedule['layout'],schedule['variant'],a.out)
    rows,matched,ralt=projection.project_group1_four_levels(xkb_text,first,baseline); d.change_keyboard_mapping(first,[tuple(r) for r in rows]); d.sync(); mods=projection.bind_mode_switch_mod5(d,ralt)
    live=candidate.keyboard_mapping(d); applied_hash=candidate.fingerprint(live); mod_hash=candidate.modifier_fingerprint(candidate.modifier_mapping(d))
    (a.out/'applied_mapping.json').write_text(json.dumps(live,separators=(',',':'))+'\n'); (a.out/'modifier_mapping.json').write_text(json.dumps(candidate.modifier_mapping(d),separators=(',',':'))+'\n')
    sock=str(a.out/'receiver.sock'); proc=subprocess.Popen([sys.executable,str(HERE/'receiver.py'),sock],env=os.environ.copy(),text=True,stdout=subprocess.PIPE,stderr=(a.out/'receiver.stderr').open('w'))
    xid=int(json.loads(proc.stdout.readline())['xid']); win=d.create_resource_object('window',xid); win.set_input_focus(X.RevertToParent,X.CurrentTime); d.sync(); time.sleep(.05)
    rows_out=[]
    try:
        for seq,idx in enumerate(order):
            text=payloads[idx]; rpc(sock,{'op':'reset'}); win.set_input_focus(X.RevertToParent,X.CurrentTime); d.sync(); backend=SimpleNamespace(d=d,emissions=0)
            try:
                plan=candidate.prepare(text,live,first); expected_accept=True; expected_levels=[s.level for s in plan.strokes]; expected_mode=any(s.mode_switch for s in plan.strokes)
            except candidate.Rejected as exc:
                expected_accept=False; expected_levels=[]; expected_mode=False; expected_error=str(exc)
            before_map=candidate.fingerprint(candidate.keyboard_mapping(d)); before_mod=candidate.modifier_fingerprint(candidate.modifier_mapping(d))
            rec=candidate.deliver(backend,text,target=xid,observation=7,current_observation=7,revision=3,current_revision=3,expires_ns=time.monotonic_ns()+3_000_000_000,pacing_s=.002)
            time.sleep(.025); actual=rpc(sock,{'op':'get'}).get('text',''); after_map=candidate.fingerprint(candidate.keyboard_mapping(d)); after_mod=candidate.modifier_fingerprint(candidate.modifier_mapping(d)); phys=candidate.physical_state(d)
            gate=(rec['accepted']==expected_accept and rec.get('release_verified') is True and not phys['keys'] and phys['mask']==0 and before_map==after_map==applied_hash and before_mod==after_mod==mod_hash and ((expected_accept and actual==text) or ((not expected_accept) and actual=='' and rec['emissions']==0)))
            rows_out.append({'sequence':seq,'payload_index':idx,'payload':text,'expected_accept':expected_accept,'expected_levels':expected_levels,'expected_mode_switch':expected_mode,'candidate':rec,'actual':actual,'map_before':before_map,'map_after':after_map,'modifier_before':before_mod,'modifier_after':after_mod,'physical_after_trial':phys,'gate':gate})
    finally:
        try: rpc(sock,{'op':'quit'})
        except Exception: pass
        try: proc.wait(timeout=2)
        except subprocess.TimeoutExpired: proc.kill()
        final_map=candidate.fingerprint(candidate.keyboard_mapping(d)); final_mod=candidate.modifier_fingerprint(candidate.modifier_mapping(d)); final_phys=candidate.physical_state(d); d.close()
    report={'schema':'xkb-altgr-direct-arm-v1','task':schedule['task'],'rep':a.rep,'layout':schedule['layout'],'variant':schedule['variant'],'xkb_source_sha256':sha((a.out/'layout.src.xkb').read_bytes()),'xkb_resolved_sha256':sha((a.out/'layout.resolved.xkb').read_bytes()),'matched_key_blocks':matched,'ralt_keycode':ralt,'applied_map_hash':applied_hash,'applied_modifier_hash':mod_hash,'modifier_mapping':mods,'final_map_hash':final_map,'final_modifier_hash':final_mod,'final_physical':final_phys,'trials':rows_out,'passed':all(r['gate'] for r in rows_out) and final_map==applied_hash and final_mod==mod_hash and not final_phys['keys'] and final_phys['mask']==0}
    (a.out/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False,sort_keys=True)+'\n'); print(json.dumps({'rep':a.rep,'passed':report['passed'],'resolved':report['xkb_resolved_sha256']},sort_keys=True)); return 0 if report['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
