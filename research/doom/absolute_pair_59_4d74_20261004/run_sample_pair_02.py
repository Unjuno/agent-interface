from pathlib import Path
import subprocess,json,hashlib,time
root=Path(__file__).resolve().parent;out=root/'sample-pair-02';out.mkdir(exist_ok=False)
files={}
for folder in ['sample-pair-source-02','fixture-input']:
    for p in (root/folder).rglob('*'):
        if p.is_file():files[p.relative_to(root).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['sample_pair_entry_02.py','probe_sample_pair_02.py','run_sample_pair_02.py','prepare_sample_pair_02.py','SAMPLE_PAIR_SOURCE_02.json']:
    p=root/name;files[name]=hashlib.sha256(p.read_bytes()).hexdigest();(out/name).write_bytes(p.read_bytes())
argv=['C:/Program Files/WSL/wslc.exe','run','--rm','--pull','never','--name','ai59-4d74-samplepair02','--network','none','--user','65534:65534','--cpus','1','--memory','1G','--workdir','/out','--env','HOME=/tmp','--env','PYTHONDONTWRITEBYTECODE=1','--mount',f'type=bind,source={root.as_posix()},target=/study,readonly','--mount',f'type=bind,source={out.as_posix()},target=/out','sha256:94014a0f7757b46b7c3ae83f430ad973ae6abe1722937bdc6d060139aaeb6378','timeout','110s','python3','/study/probe_sample_pair_02.py']
freeze={'argv':argv,'files':files,'source_git':json.loads((root/'SAMPLE_PAIR_SOURCE_02.json').read_text())['commit'],'model_calls':0,'allocation':'absolute-pair-construction-02','H':'A common absolute lease deadline separates input release from delayed lifecycle completion despite synchronous snapshots','T':'three fresh counterbalanced pairs; same fixture/seed; 600ms absolute runtime window and lease; scorer-only samples; completed or expired terminal then normal finish','D':'all six terminal completed or expired with verified empty release and normal child/reader closure; report samples within clock+600ms and late admissions/release separately; absent release or positive admission after deadline FAIL; no matched efficacy PASS' ,'C':'sampling excludes exact transitions; overhead may change actual trajectory/window exposure; no model latency or causal useful-feedback benefit','U':'CPU private WSLc construction, no provider/GPU; preserve first failure and stop remaining cells on failure'}
(out/'FREEZE.json').write_text(json.dumps(freeze,indent=2))
start=time.monotonic();r=subprocess.run(argv,capture_output=True,timeout=120)
(out/'stdout.txt').write_bytes(r.stdout);(out/'stderr.txt').write_bytes(r.stderr);(out/'HOST.json').write_text(json.dumps({'exit_code':r.returncode,'elapsed_s':time.monotonic()-start}));print(r.returncode);print(r.stdout.decode());print(r.stderr.decode())
