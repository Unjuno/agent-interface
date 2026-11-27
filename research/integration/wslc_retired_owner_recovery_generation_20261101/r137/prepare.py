import hashlib,json,pathlib
root=pathlib.Path(__file__).resolve().parent
files=[p for p in (root/'src').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc']+[root/n for n in ('trial.py','target.py','run.py','prepare.py')]
manifest={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
arms=[('r137-control','control'),('r137-helper','helper')]
for ident,mode in arms:
 p=root/ident;p.mkdir(exist_ok=False);(p/'output').mkdir()
 c={'allocation':'idle-explicit-recovery-'+ident,'mode':mode,'order':arms,'main_at_predecessor_freeze':'11e5d65e5898c71d96de582f9c218d00dc2a635d','predecessor_head':'e6ed07edad270cc4631518bf3b53124e4ada28b6','candidate':'local r132; exact source in manifest','image':'sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25','manifest_sha256':hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest(),'protocol':'Private Xvfb: real old guarded action holds a; delayed b queued during injected X sync block; real cancel acknowledged, parent pauses decision and retires child. Both return UNKNOWN with cleanup stubbed. Control releases a,b by test fixture; helper explicitly calls existing private retirement cleanup with real retirement receipt, no new owner; independently verify key state, delayed horizon and fresh owner task.','criteria':'both see a down before and after cancel, cancel UNKNOWN; control fixture release or helper disconnect plus readback_verified followed by independent keys up; delayed horizon neutral; fresh action produces aa and releases; old close remains UNKNOWN','stop':'one try per arm; stop on failure or unresolved final input; private Xvfb destroyed in finally','limits':'injected sync/delay and decision pause, explicit helper invocation, private exclusive display; not integrated automatic recovery or physical desktop or MAP01'}
 (p/'conditions.json').write_text(json.dumps(c,indent=2)+'\n')
print('frozen')
