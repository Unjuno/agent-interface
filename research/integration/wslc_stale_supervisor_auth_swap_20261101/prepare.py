import hashlib,json,pathlib
root=pathlib.Path(__file__).resolve().parent
files=[p for p in (root/'src').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc']+[root/'trial.py',root/'target.py',root/'run.py',root/'prepare.py']
manifest={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
arms=[('authswap-v01','keep'),('authswap-v02','swap')]
for ident,mode in arms:
 p=root/ident;p.mkdir(exist_ok=False);(p/'output').mkdir()
 c={'allocation':'xvfb-authswap-'+ident+'-20261101','mode':mode,'order':[f'{i}:{m}' for i,m in arms],
    'base_main':'e5925b6bd99fd4ff3f8e0bda5ed4d7cc02d92c4d','draft_head':'926ba07214b5ab53ff38f66af5c0947606850118',
    'image':'sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25',
    'manifest_sha256':hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest(),
    'intervention':'start old guarded owner/supervisor then retire owner and display; start new Xvfb with same display number; hold b in fresh target; retain old authority or replace its file with new authority; invoke old supervisor with synthetic old b obligation; inspect fresh b, cleanup and run fresh task',
    'criteria':'same display number; prestarted old supervisor receives exact prior owner identity and synthetic b obligation; record result and fresh b state for old vs replaced authority; fixture cleanup; fresh guarded task effect and release verified',
    'stop':'one try per arm; preserve all failures; stop block on unresolved input or infrastructure failure',
    'limits':'explicit test-only mutation of disposable authority file; synthetic cleanup request, not production cancellation; fixed-order pair; no general attack or recovery claim'}
 (p/'conditions.json').write_text(json.dumps(c,indent=2)+'\n')
print('two arms frozen')
