from pathlib import Path
import subprocess,json,hashlib,time
root=Path(__file__).resolve().parent;out=root/'sample-pair-03';out.mkdir(exist_ok=False)
files={}
for folder in ['sample-pair-source-03','fixture-input']:
    for p in (root/folder).rglob('*'):
        if p.is_file():files[p.relative_to(root).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['sample_pair_entry_03.py','probe_sample_pair_03.py','run_sample_pair_03.py','prepare_sample_pair_03.py','SAMPLE_PAIR_SOURCE_03.json']:
    p=root/name;files[name]=hashlib.sha256(p.read_bytes()).hexdigest();(out/name).write_bytes(p.read_bytes())
argv=['C:/Program Files/WSL/wslc.exe','run','--rm','--pull','never','--name','ai59-4d74-progresssample03','--network','none','--user','65534:65534','--cpus','1','--memory','1G','--workdir','/out','--env','HOME=/tmp','--env','PYTHONDONTWRITEBYTECODE=1','--mount',f'type=bind,source={root.as_posix()},target=/study,readonly','--mount',f'type=bind,source={out.as_posix()},target=/out','sha256:94014a0f7757b46b7c3ae83f430ad973ae6abe1722937bdc6d060139aaeb6378','timeout','110s','python3','/study/probe_sample_pair_03.py']
freeze={'argv':argv,'files':files,'source_git':json.loads((root/'SAMPLE_PAIR_SOURCE_03.json').read_text())['commit'],'model_calls':0,'allocation':'progress-sample-construction-03','H':'Same-thread scorer-only game variables can measure changing damage/progress separately from input occupancy','T':'one no-input5000ms coast from fixturev2,seed40126; clock+5s lease; HEALTH AMMO1 POSITION_X Y Z KILLCOUNT DEATHCOUNT with coherent tic bracket; normalfinish','D':'finite coherent samples in window; initial API health/ammo agrees with observed initial HUD if both available; mismatch or missing/unsupported fields FAIL, absent damage/progress exposure HOLD; no useful-efficacy PASS','C':'sampled API state not exact onset; observer timing/fixture setup affect exposure; no model or causal comparison','U':'CPU private networknone WSLc,no provider/GPU/input; first outcome retained, no retry'}
(out/'FREEZE.json').write_text(json.dumps(freeze,indent=2))
start=time.monotonic();r=subprocess.run(argv,capture_output=True,timeout=120)
(out/'stdout.txt').write_bytes(r.stdout);(out/'stderr.txt').write_bytes(r.stderr);(out/'HOST.json').write_text(json.dumps({'exit_code':r.returncode,'elapsed_s':time.monotonic()-start}));print(r.returncode);print(r.stdout.decode());print(r.stderr.decode())
