from pathlib import Path
import subprocess,json,hashlib,time
root=Path(__file__).resolve().parent
repo=root.parent/'calc-construction-publication-4d74'
out=root/'controller-exception-construction-01'
out.mkdir(exist_ok=False)
source=out/'source/research/doom';source.mkdir(parents=True)
for name in ['map01_overlap_controller_v39.py','doom_source_refresh_v1.py','map01_motor_responder_v10.txt','map01_cover_policy_schema_v6.json']:
    (source/name).write_bytes((repo/'research/doom'/name).read_bytes())
argv=['C:/Program Files/WSL/wslc.exe','run','--rm','--pull','never','--name','ai59-4d74-exception01','--network','none','--user','65534:65534','--cpus','1','--memory','512m','--workdir','/out','--mount',f'type=bind,source={root.as_posix()},target=/study,readonly','--mount',f'type=bind,source={out.as_posix()},target=/out','--env','PYTHONDONTWRITEBYTECODE=1','--env','PYTHONPATH=/out/source/research/doom:/study/current-controller-source-09/research/doom:/study/current-controller-source-09/research/live_control:/study/current-controller-source-09/research/real_apps_v1:/study/current-controller-source-09/research/observation_tiles:/study/current-controller-source-09/research/observation_gating','sha256:94014a0f7757b46b7c3ae83f430ad973ae6abe1722937bdc6d060139aaeb6378','timeout','20s','python3','/study/probe_controller_exception_01.py']
pins={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in source.iterdir()}
for name in ['probe_controller_child_01.py','probe_controller_exception_01.py','run_controller_exception_01.py']:
    pins[name]=hashlib.sha256((root/name).read_bytes()).hexdigest();(out/name).write_bytes((root/name).read_bytes())
(out/'FREEZE.json').write_bytes(json.dumps({'argv':argv,'files':pins,'controller_main_git':'9590ee9e0c74f7438306e8efb48b2af813f7a86b','dependencies_git':'f2aa59c8bac88f0091eb24c4f462f55a72303d2f'},indent=2).encode())
started=time.monotonic()
result=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=40)
(out/'stdout.txt').write_bytes(result.stdout);(out/'stderr.txt').write_bytes(result.stderr)
(out/'RESULT.json').write_bytes(json.dumps({'container_exit':result.returncode,'elapsed_seconds':time.monotonic()-started},indent=2).encode())
print(result.returncode);print(result.stdout.decode(errors='replace'));print(result.stderr.decode(errors='replace'))
