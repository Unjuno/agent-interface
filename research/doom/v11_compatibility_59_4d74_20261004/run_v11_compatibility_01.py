from pathlib import Path
import subprocess, json, hashlib, time, shutil
root = Path(__file__).resolve().parent
source = root / 'v11-compatibility-source-01'
source.mkdir(exist_ok=False)
for p in (root/'accepted-sink-source-01').glob('*.py'):
    shutil.copyfile(p, source/p.name)
for name, content in json.loads((root/'v11_source_payload_01.json').read_text()).items():
    (source/name).write_bytes(content.encode('utf-8'))
out = root / 'v11-compatibility-01'
out.mkdir(exist_ok=False)
image = (root/'image-02/image.id').read_text().strip()
args = ['C:/Program Files/WSL/wslc.exe', 'run', '--name', 'v11-compatibility-59-4d74-01', '--pull', 'never', '--cpus', '1', '--memory', '512M', '--network', 'none', '--user', '65534', '--env', 'HOME=/tmp', '--env', 'PYTHONDONTWRITEBYTECODE=1', '--mount', f'type=bind,source={source},target=/source,readonly', '--mount', f'type=bind,source={out},target=/out', image, '/usr/local/bin/python3', '-B', '/source/test_input_owner_v11.py', '-v']
freeze = {'head': 'd35572515f828f458f7bc7406334f74707164199', 'H': 'Existing V11 delegation and release interval receipt contracts remain compatible after the proposed owner migration.', 'T': 'Run all five unchanged contract tests once against exact-head v10/v11/test and frozen earlier support in private WSLc.', 'D': 'All five tests pass; otherwise preserve failures without retry.', 'C': 'Mocked contract check, not full owner/runtime or physical release.', 'U': 'No X server/game/model/GPU/physical input; cached image; cgroup warning retained; caps enforcement unproven.', 'image': image, 'argv': args, 'source_files': {p.name: {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size} for p in source.glob('*.py')}, 'retries': 0, 'setup_stop': 'Prior Windows command exceeded CreateProcess command-length limit before execution; no source staging or container launch occurred.'}
(out/'FREEZE.json').write_text(json.dumps(freeze, indent=2)+'\n')
start = time.monotonic()
with (out/'stdout.txt').open('wb') as stdout, (out/'stderr.txt').open('wb') as stderr:
    result = subprocess.run(args, stdout=stdout, stderr=stderr, timeout=45)
(out/'HOST.json').write_text(json.dumps({'exit': result.returncode, 'elapsed_s': time.monotonic()-start, 'scope': freeze['C'], 'retry': False}, indent=2)+'\n')
print(json.dumps({'exit': result.returncode, 'stdout': (out/'stdout.txt').read_text(), 'stderr': (out/'stderr.txt').read_text()}))
