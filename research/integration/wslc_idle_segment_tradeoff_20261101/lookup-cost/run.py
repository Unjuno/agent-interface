import hashlib,json,pathlib,subprocess,sys,time
root=pathlib.Path(__file__).resolve().parent;path=root/sys.argv[1];c=json.loads((path/'conditions.json').read_text())
for name,digest in c['source_sha256'].items():
    if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise RuntimeError('frozen source changed: '+name)
cmd=['wslc','run','--rm','--name',c['allocation'],'--network','none','--cpus','1','--memory','1g','--pull','never',
    '--mount',f'type=bind,source={root},target=/src,readonly','--mount',f'type=bind,source={path / "output"},target=/out',
    '--env','PYTHONPATH=/src','--env','PYTHONDONTWRITEBYTECODE=1','--env','SIZE_ORDER='+c['order'],
    '--entrypoint','timeout',c['image'],'--signal=TERM','--kill-after=3s','90s','python3','-B','/src/bench.py']
started=time.monotonic()
with (path/'stdout').open('wb') as stdout,(path/'stderr').open('wb') as stderr:
    proc=subprocess.run(cmd,stdout=stdout,stderr=stderr,timeout=110,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
(path/'launcher-result.json').write_text(json.dumps({'returncode':proc.returncode,'elapsed_seconds':time.monotonic()-started},indent=2)+'\n')
print(json.dumps({'returncode':proc.returncode}),flush=True);sys.exit(proc.returncode)
