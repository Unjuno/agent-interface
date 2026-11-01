import hashlib,json,pathlib,subprocess,sys,time
root=pathlib.Path(__file__).resolve().parent;p=root/sys.argv[1];c=json.loads((p/'conditions.json').read_text())
manifest=json.loads((root/'manifest.json').read_text())
if hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest()!=c['manifest_sha256']:raise RuntimeError('manifest changed')
for name,digest in manifest.items():
 if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise RuntimeError('candidate changed '+name)
cmd=['wslc','run','--rm','--name',c['allocation'],'--network','none','--cpus','1','--memory','1g','--pull','never',
 '--mount',f'type=bind,source={root / "src"},target=/src,readonly',
 '--mount',f'type=bind,source={root / "trial.py"},target=/trial.py,readonly',
 '--mount',f'type=bind,source={root / "target.py"},target=/target.py,readonly',
 '--mount',f'type=bind,source={p / "output"},target=/out',
 '--env','PYTHONPATH=/src','--env','PYTHONDONTWRITEBYTECODE=1','--env','CONTROL_MODE='+c['mode'],'--env','AGENT_INTERFACE_MCP_XVFB_CANCEL_ACK_WITHHOLD_S=0',
 '--entrypoint','timeout',c['image'],'--signal=TERM','--kill-after=3s','30s','python3','-B','/trial.py']
(p/'private-command.json').write_text(json.dumps(cmd,indent=2)+'\n')
started=time.monotonic()
with (p/'stdout').open('wb') as stdout,(p/'stderr').open('wb') as stderr:
 proc=subprocess.run(cmd,stdout=stdout,stderr=stderr,timeout=50,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
result={'returncode':proc.returncode,'elapsed_seconds':time.monotonic()-started}
(p/'launcher-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result),flush=True);sys.exit(proc.returncode)
