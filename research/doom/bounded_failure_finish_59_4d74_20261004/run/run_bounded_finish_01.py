from pathlib import Path
import hashlib,json,subprocess,time
root=Path(__file__).resolve().parent
repo=root.parent/'calc-construction-publication-4d74'
out=root/'bounded-finish-01';out.mkdir(exist_ok=False)
source=out/'source';source.mkdir()
for name in ['doom_controller_failure_cleanup_v1.py','test_failure_finish_pipe_v1.py','test_controller_failure_cleanup_v1.py']:
    (source/name).write_bytes((repo/'research/doom'/name).read_bytes())
for name in ['probe_bounded_finish_01.py','run_bounded_finish_01.py']:
    (out/name).write_bytes((root/name).read_bytes())
argv=['C:/Program Files/WSL/wslc.exe','run','--rm','--pull','never','--name','ai59-4d74-boundedfinish01','--network','none','--user','65534:65534','--cpus','1','--memory','512m','--workdir','/out','--mount',f'type=bind,source={source.as_posix()},target=/source,readonly','--mount',f'type=bind,source={out.as_posix()},target=/out','--env','PYTHONDONTWRITEBYTECODE=1','--env','PYTHONPATH=/source','sha256:94014a0f7757b46b7c3ae83f430ad973ae6abe1722937bdc6d060139aaeb6378','timeout','15s','python3','/out/probe_bounded_finish_01.py']
pins={p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*.py')}
(out/'FREEZE.json').write_bytes(json.dumps({'argv':argv,'files':pins,'source_kind':'working candidate; byte hashes authoritative'},indent=2).encode())
started=time.monotonic();r=subprocess.run(argv,capture_output=True,timeout=30)
(out/'stdout.txt').write_bytes(r.stdout);(out/'stderr.txt').write_bytes(r.stderr)
(out/'RESULT.json').write_bytes(json.dumps({'exit_code':r.returncode,'elapsed_s':time.monotonic()-started},indent=2).encode())
print(r.returncode);print(r.stdout.decode());print(r.stderr.decode())
