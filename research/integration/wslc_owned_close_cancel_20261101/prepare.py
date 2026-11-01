import hashlib,json,pathlib
root=pathlib.Path(__file__).resolve().parent
files=[p for p in (root/'src').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc']+[root/'trial.py',root/'target.py',root/'run.py',root/'prepare.py']
manifest={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
arms=[('close-cancel-live-p01','correct')]
for ident,mode in arms:
 p=root/ident;p.mkdir(exist_ok=False);(p/'output').mkdir()
 c={'allocation':'xvfb-close-cancel-live-'+ident+'-20261101','mode':mode,'order':[f'{i}:{m}' for i,m in arms],
    'base_main':'e5925b6bd99fd4ff3f8e0bda5ed4d7cc02d92c4d','draft_head':'926ba07214b5ab53ff38f66af5c0947606850118',
    'image':'sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25',
    'manifest_sha256':hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest(),
    'intervention':'guarded owner presses a and pauses; real cancellation retires owner and pauses before cleanup; invoke owner.close during cancellation; ensure busy and supervisor still alive; resume cleanup and run fresh guarded task',
    'criteria':'first cleanup entered before close; close returns busy without closing supervisor; first cleanup retains operation identity; old cleanup remains UNKNOWN; fresh guarded task effect and release verified',
    'stop':'one try per arm; preserve all failures; stop block on unresolved input or infrastructure failure',
    'limits':'one trial with injected owner pause; parent changes authority only to open harness Xlib; no production integration, natural hang, hard deadline or MAP01 claim'}
 (p/'conditions.json').write_text(json.dumps(c,indent=2)+'\n')
print('two arms frozen')
