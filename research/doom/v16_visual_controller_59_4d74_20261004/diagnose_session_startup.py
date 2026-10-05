from pathlib import Path
import subprocess,json,hashlib
root=Path(__file__).resolve().parent
out=root/'controller-startup-diagnostic-01'
out.mkdir(exist_ok=False)
f=json.loads((root/'controller-visual-01/FREEZE.json').read_bytes())
argv=f['container_argv'][:]
argv[argv.index('--name')+1]='ai59-4d74-startdiag01'
for i,v in enumerate(argv):
 if v==f'type=bind,source={root / "controller-visual-01"},target=/out':argv[i]=f'type=bind,source={out},target=/out'
idx=argv.index('/usr/local/bin/python3')
argv=argv[:idx]+['timeout','30s','/usr/local/bin/python3','/study/current-controller-source-09/research/doom/session_map01_v16.py','--out','/out/session','--seed','40116','--timeout-seconds','600','--skill','1','--load-fixture-manifest','/study/fixture-input/fixture.json']
(out/'FREEZE.json').write_bytes(json.dumps({'argv':argv,'driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source_freeze':'../controller-visual-01/FREEZE.json','purpose':'startup diagnostic only, stdin EOF, zero model/input commands, distinct seed'},indent=2).encode())
r=subprocess.run(argv,input=b'',capture_output=True,timeout=40)
(out/'stdout.txt').write_bytes(r.stdout);(out/'stderr.txt').write_bytes(r.stderr)
(out/'exit.json').write_bytes(json.dumps({'exit':r.returncode}).encode())
print(json.dumps({'exit':r.returncode,'stderr':r.stderr.decode(errors='replace')}))
