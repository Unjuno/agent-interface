from pathlib import Path
import subprocess,json,hashlib,time
root=Path(__file__).resolve().parent;out=root/'sample-pair-04';out.mkdir(exist_ok=False)
files={}
for folder in ['sample-pair-source-04','fixture-input']:
    for p in (root/folder).rglob('*'):
        if p.is_file():files[p.relative_to(root).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['sample_pair_entry_04.py','probe_sample_pair_04.py','run_sample_pair_04.py','prepare_sample_pair_04.py','SAMPLE_PAIR_SOURCE_04.json']:
    p=root/name;files[name]=hashlib.sha256(p.read_bytes()).hexdigest();(out/name).write_bytes(p.read_bytes())
argv=['C:/Program Files/WSL/wslc.exe','run','--rm','--pull','never','--name','ai59-4d74-weaponammo04','--network','none','--user','65534:65534','--cpus','1','--memory','1G','--workdir','/out','--env','HOME=/tmp','--env','PYTHONDONTWRITEBYTECODE=1','--mount',f'type=bind,source={root.as_posix()},target=/study,readonly','--mount',f'type=bind,source={out.as_posix()},target=/out','sha256:94014a0f7757b46b7c3ae83f430ad973ae6abe1722937bdc6d060139aaeb6378','timeout','110s','python3','/study/probe_sample_pair_04.py']
freeze={'argv':argv,'files':files,'source_git':json.loads((root/'SAMPLE_PAIR_SOURCE_04.json').read_text())['commit'],'model_calls':0,'allocation':'weapon-ammo-construction-04','H':'Scorer-only selected-weapon ammo and inventory variables reconcile to captured HUD values','T':'one no-input5000ms coast from fixturev2,seed40127; clock+5s lease; HEALTH SELECTED_WEAPON SELECTED_WEAPON_AMMO AMMO0-AMMO9 POSITION_X Y Z KILLCOUNT DEATHCOUNT with coherent tic bracket; normalfinish','D':'finite coherent samples in window; initial API health and selected ammo agrees with nearby observed initial HUD or fail; missing or unsupported fields fail; no efficacy PASS','C':'sampled API state not exact onset; HUD/API cross-clock offset retained; no model or causal comparison','U':'CPU private networknone WSLc,no provider/GPU/input; first outcome retained, no retry'}
(out/'FREEZE.json').write_text(json.dumps(freeze,indent=2))
start=time.monotonic();r=subprocess.run(argv,capture_output=True,timeout=120)
(out/'stdout.txt').write_bytes(r.stdout);(out/'stderr.txt').write_bytes(r.stderr);(out/'HOST.json').write_text(json.dumps({'exit_code':r.returncode,'elapsed_s':time.monotonic()-start}));print(r.returncode);print(r.stdout.decode());print(r.stderr.decode())
