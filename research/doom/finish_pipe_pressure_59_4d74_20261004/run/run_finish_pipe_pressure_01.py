from pathlib import Path
import subprocess,json,hashlib,time
root=Path(__file__).resolve().parent
repo=root.parent/'calc-construction-publication-4d74'
out=root/'finish-pipe-pressure-01';out.mkdir(exist_ok=False)
source=out/'source';source.mkdir()
raw=subprocess.check_output(['git','show','origin/main:research/doom/doom_controller_failure_cleanup_v1.py'],cwd=repo)
(source/'doom_controller_failure_cleanup_v1.py').write_bytes(raw)
for name in ['probe_finish_pipe_pressure_01.py','run_finish_pipe_pressure_01.py']:
    (out/name).write_bytes((root/name).read_bytes())
argv=['C:/Program Files/WSL/wslc.exe','run','--rm','--pull','never','--name','ai59-4d74-finishpressure01','--network','none','--user','65534:65534','--cpus','1','--memory','512m','--workdir','/out','--mount',f'type=bind,source={root.as_posix()},target=/study,readonly','--mount',f'type=bind,source={out.as_posix()},target=/out','--env','PYTHONDONTWRITEBYTECODE=1','--env','PYTHONPATH=/out/source','sha256:94014a0f7757b46b7c3ae83f430ad973ae6abe1722937bdc6d060139aaeb6378','timeout','15s','python3','/study/probe_finish_pipe_pressure_01.py']
pins={p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*.py')}
(out/'FREEZE.json').write_bytes(json.dumps({'argv':argv,'files':pins,'source_git':subprocess.check_output(['git','rev-parse','origin/main'],cwd=repo).decode().strip()},indent=2).encode())
started=time.monotonic();result=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
(out/'stdout.txt').write_bytes(result.stdout);(out/'stderr.txt').write_bytes(result.stderr)
(out/'RESULT.json').write_bytes(json.dumps({'exit_code':result.returncode,'elapsed_s':time.monotonic()-started},indent=2).encode())
print(result.returncode);print(result.stdout.decode(errors='replace'));print(result.stderr.decode(errors='replace'))
