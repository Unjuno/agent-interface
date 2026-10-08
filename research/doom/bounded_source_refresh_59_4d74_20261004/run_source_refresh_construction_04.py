from pathlib import Path
import hashlib,json,subprocess,time
root=Path(__file__).resolve().parent
source=root.parent/'calc-construction-publication-4d74/research/doom'
out=root/'source-refresh-construction-04'
out.mkdir(exist_ok=False)
names=['doom_source_refresh_v1.py','test_source_refresh_v1.py','map01_overlap_controller_v39.py','test_map01_overlap_controller_v39.py','test_overlap_controller_v39_wait.py']
for name in names:
    (out/name).write_bytes((source/name).read_bytes())
argv=['C:/Program Files/WSL/wslc.exe','run','--rm','--pull','never','--name','ai59-4d74-source-refresh04','--network','none','--user','65534:65534','--cpus','1','--memory','512m','--workdir','/candidate/research/doom','--mount',f'type=bind,source={source.as_posix()},target=/candidate/research/doom,readonly','--mount',f'type=bind,source={(root/"current-controller-source-09").as_posix()},target=/deps,readonly','--env','PYTHONDONTWRITEBYTECODE=1','--env','PYTHONPATH=/candidate/research/doom:/deps/research/doom:/deps/research/live_control:/deps/research/real_apps_v1:/deps/research/observation_tiles:/deps/research/observation_gating','sha256:94014a0f7757b46b7c3ae83f430ad973ae6abe1722937bdc6d060139aaeb6378','timeout','30s','python3','-m','unittest','test_source_refresh_v1','test_map01_overlap_controller_v39','test_overlap_controller_v39_wait','-v']
pins={n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in names}
(out/'FREEZE.json').write_bytes(json.dumps({'argv':argv,'source_sha256':pins,'dependency_source_git':'f2aa59c8bac88f0091eb24c4f462f55a72303d2f','scope':'construction only; dependency source pins retained in comparison7577'},indent=2).encode())
started=time.monotonic()
result=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=50)
(out/'stdout.txt').write_bytes(result.stdout); (out/'stderr.txt').write_bytes(result.stderr)
(out/'RESULT.json').write_bytes(json.dumps({'exit_code':result.returncode,'elapsed_seconds':time.monotonic()-started},indent=2).encode())
print(result.returncode);print(result.stdout.decode(errors='replace'));print(result.stderr.decode(errors='replace'))
