#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, socket, subprocess, sys, time
from pathlib import Path
from types import SimpleNamespace
from Xlib import X, display
from xkb_projection import resolve_xkb, project_group1_two_levels

EXPECTED_DEP_BLOB = '35c7375e50f3e0c58f57c8139a6dc8abeef87771'
HERE = Path(__file__).resolve().parent

def git_blob(path: Path) -> str:
    data = path.read_bytes(); return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
def rpc(path: str, obj: dict) -> dict:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); end = time.monotonic() + 3
    while True:
        try: s.connect(path); break
        except OSError:
            if time.monotonic() >= end: raise
            time.sleep(.01)
    s.sendall((json.dumps(obj) + '\n').encode()); data = b''
    while not data.endswith(b'\n'): data += s.recv(65536)
    s.close(); return json.loads(data.decode())
def load_dep(path: Path):
    if git_blob(path) != EXPECTED_DEP_BLOB: raise RuntimeError('preflight dependency blob mismatch')
    spec = importlib.util.spec_from_file_location('retained_preflight', path); mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod; spec.loader.exec_module(mod); return mod

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument('--layout', required=True); ap.add_argument('--variant', default=''); ap.add_argument('--out', type=Path, required=True); ap.add_argument('--dependency', type=Path, required=True); a = ap.parse_args()
    a.out = a.out.resolve(); a.out.mkdir(parents=True, exist_ok=False)
    if not os.environ.get('DISPLAY') or not os.environ.get('XAUTHORITY'): raise RuntimeError('run inside authenticated private Xvfb')
    dep = load_dep(a.dependency.resolve()); d = display.Display(os.environ['DISPLAY']); first = d.display.info.min_keycode
    baseline = dep.keyboard_mapping(d); baseline_hash = dep.fingerprint(baseline)
    xkb_text = resolve_xkb(os.environ['DISPLAY'], os.environ['XAUTHORITY'], a.layout, a.variant, a.out)
    projected, matched = project_group1_two_levels(xkb_text, first, baseline); d.change_keyboard_mapping(first, [tuple(r) for r in projected]); d.sync()
    live = dep.keyboard_mapping(d); applied_hash = dep.fingerprint(live)
    sock = str(a.out / 'receiver.sock'); env = os.environ.copy(); proc = subprocess.Popen([sys.executable, str(HERE/'receiver.py'), sock], env=env, text=True, stdout=subprocess.PIPE, stderr=(a.out/'receiver.stderr').open('w'))
    meta = json.loads(proc.stdout.readline()); xid = int(meta['xid']); win = d.create_resource_object('window', xid); win.set_input_focus(X.RevertToParent, X.CurrentTime); d.sync(); time.sleep(.05)
    rows = []
    try:
        for cp in range(32, 127):
            ch = chr(cp); rpc(sock, {'op':'reset'}); win.set_input_focus(X.RevertToParent, X.CurrentTime); d.sync(); backend = SimpleNamespace(d=d, emissions=0)
            try: dep.prepare(ch, live, first); expected_accept = True
            except dep.Rejected: expected_accept = False
            receipt = dep.deliver(backend, ch, target=xid, observation=7, current_observation=7, revision=3, current_revision=3, expires_ns=time.monotonic_ns()+3_000_000_000, pacing_s=.002)
            time.sleep(.025); actual = rpc(sock, {'op':'get'}).get('text',''); map_same = dep.fingerprint(dep.keyboard_mapping(d)) == applied_hash
            gate = receipt['accepted'] == expected_accept and map_same and receipt.get('release_verified') and ((expected_accept and actual == ch) or ((not expected_accept) and actual == '' and receipt['emissions'] == 0))
            rows.append({'cp':cp,'requested':ch,'expected_accept':expected_accept,'accepted':receipt['accepted'],'error':receipt.get('error'),'emissions':receipt['emissions'],'actual':actual,'map_same':map_same,'release_verified':receipt.get('release_verified'),'gate':gate})
    finally:
        try: rpc(sock, {'op':'quit'})
        except Exception: pass
        try: proc.wait(timeout=2)
        except subprocess.TimeoutExpired: proc.kill()
        d.change_keyboard_mapping(first, [tuple(r) for r in baseline]); d.sync(); restored_hash = dep.fingerprint(dep.keyboard_mapping(d)); d.close()
    accepted = [r['cp'] for r in rows if r['accepted']]; rejected = [r['cp'] for r in rows if not r['accepted']]
    report = {'schema':'agent-interface/text-payload-xkb-layout-arm-v1','layout':a.layout,'variant':a.variant,'dependency_blob':EXPECTED_DEP_BLOB,'matched_key_blocks':matched,'baseline_map_hash':baseline_hash,'applied_map_hash':applied_hash,'mapping_changed':applied_hash != baseline_hash,'restored_map_hash':restored_hash,'restored_exact':restored_hash == baseline_hash,'accepted_count':len(accepted),'rejected_count':len(rejected),'accepted_codepoints':accepted,'rejected_codepoints':rejected,'trials':rows,'passed':all(r['gate'] for r in rows) and restored_hash == baseline_hash and (a.layout == 'us' or applied_hash != baseline_hash)}
    (a.out/'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8'); print(json.dumps({k:report[k] for k in ['layout','variant','accepted_count','rejected_count','mapping_changed','restored_exact','passed']}, indent=2)); return 0 if report['passed'] else 1
if __name__ == '__main__': raise SystemExit(main())
