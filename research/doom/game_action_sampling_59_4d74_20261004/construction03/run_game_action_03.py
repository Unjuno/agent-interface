from pathlib import Path
import subprocess,json,hashlib,time
root=Path(__file__).resolve().parent;out=root/'game-action-measurement-03';out.mkdir(exist_ok=False)
files={}
for folder in ['current-controller-source-11','fixture-input']:
    for p in (root/folder).rglob('*'):
        if p.is_file():files[p.relative_to(root).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['game_action_measurement_entry_01.py','probe_game_action_03.py','run_game_action_03.py']:
    p=root/name;files[name]=hashlib.sha256(p.read_bytes()).hexdigest();(out/name).write_bytes(p.read_bytes())
argv=['C:/Program Files/WSL/wslc.exe','run','--rm','--pull','never','--name','ai59-4d74-gameaction03','--network','none','--user','65534:65534','--cpus','1','--memory','1G','--workdir','/out','--env','HOME=/tmp','--env','PYTHONDONTWRITEBYTECODE=1','--mount',f'type=bind,source={root.as_posix()},target=/study,readonly','--mount',f'type=bind,source={out.as_posix()},target=/out','sha256:94014a0f7757b46b7c3ae83f430ad973ae6abe1722937bdc6d060139aaeb6378','timeout','45s','python3','/study/probe_game_action_03.py']
(out/'FREEZE.json').write_bytes(json.dumps({'argv':argv,'files':files,'source_git':'4c2fe6cbd4218306bcb203cf04258b0f9a322213','model_calls':0,'prospective_comment':5979278268},indent=2).encode())
start=time.monotonic();r=subprocess.run(argv,capture_output=True,timeout=55)
(out/'stdout.txt').write_bytes(r.stdout);(out/'stderr.txt').write_bytes(r.stderr)
(out/'HOST.json').write_bytes(json.dumps({'exit_code':r.returncode,'elapsed_s':time.monotonic()-start},indent=2).encode());print(r.returncode);print(r.stdout.decode());print(r.stderr.decode())
