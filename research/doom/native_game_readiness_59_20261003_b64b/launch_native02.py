from datetime import datetime, timezone
import ast
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

HERE = Path(__file__).resolve().parent
PRIVATE = HERE / 'private/native02'
PRIVATE.mkdir(exist_ok=False)
PREFIX = ['/opt/homebrew/bin/orb', 'run', '-m', 'research-6695-docker-01a0ff52', '-u', 'root']
IMAGE = 'sha256:93ef9169b70d152291972b652bde109d15868d25f65e1110a817b1f63ead886f'
REMOTE = '/var/tmp/native-game-b64b-c02-20261003'
SOURCE = '/mnt/mac' + str(HERE / 'native')
COMMANDS = []


def save(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


def run(args, timeout=15):
    argv = PREFIX + args
    row = {'argv': argv, 'utc_start': datetime.now(timezone.utc).isoformat()}
    COMMANDS.append(row)
    save(PRIVATE / 'execution.json', COMMANDS)
    try:
        result = subprocess.run(argv, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        row.update(utc_end=datetime.now(timezone.utc).isoformat(), state='UNKNOWN timeout; no resubmit')
        (PRIVATE / ('command-%02d.timeout.stdout' % (len(COMMANDS)-1))).write_bytes(exc.stdout or b'')
        (PRIVATE / ('command-%02d.timeout.stderr' % (len(COMMANDS)-1))).write_bytes(exc.stderr or b'')
        save(PRIVATE / 'execution.json', COMMANDS)
        raise
    for label, data in [('stdout', result.stdout), ('stderr', result.stderr)]:
        (PRIVATE / ('command-%02d.%s' % (len(COMMANDS)-1, label))).write_bytes(data)
        row[label+'_bytes'] = len(data)
        row[label+'_sha256'] = hashlib.sha256(data).hexdigest()
    row.update(exit_code=result.returncode, utc_end=datetime.now(timezone.utc).isoformat())
    save(PRIVATE / 'execution.json', COMMANDS)
    return result


pins = {}
for p in sorted((HERE / 'native').glob('*.py')):
    ast.parse(p.read_text())
    pins[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
save(HERE / 'CONSTRUCTION_PINS02.json', {
    'ordinary_environment_repair': 'writable /tmp cwd, first failure retained; same game code/seed/action/gates', 'fixed_before_native_game_start': datetime.now(timezone.utc).isoformat(),
    'source_sha256': pins, 'image_id': IMAGE,
    'dependencies_sha256': hashlib.sha256((HERE/'DEPENDENCIES.json').read_bytes()).hexdigest(),
    'source_pins_sha256': hashlib.sha256((HERE/'source-pins.json').read_bytes()).hexdigest(),
    'budget': 'at most two sequential cells; invalid first control STOP; native retry0',
    'kind': 'new ordinary environment/input construction, not a formal or consumed allocation',
    'claim': 'https://github.com/Unjuno/agent-interface/issues/59#issuecomment-5966043438'})
r = run(['docker', 'ps', '--format', '{{.ID}} {{.Names}}'])
if r.returncode or r.stdout.strip():
    raise RuntimeError('STOP private Engine occupied/unavailable')
run(['mkdir', '-m', '777', REMOTE]).check_returncode()
run(['mount', '-t', 'tmpfs', '-o', 'size=32m,mode=777,nosuid,nodev,noexec', 'tmpfs', REMOTE]).check_returncode()
run(['findmnt', '-J', REMOTE]).check_returncode()
created = run(['docker', 'create', '--name', 'game-b64b-native-construction02', '--pull', 'never',
    '--network', 'none', '--cpus', '1', '--memory', '768m', '--memory-swap', '768m', '--pids-limit', '96',
    '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--user', '65534:65534',
    '--workdir', '/tmp', '--tmpfs', '/tmp:rw,size=64m,mode=1777', '-v', SOURCE+':/src:ro', '-v', REMOTE+':/out:rw', IMAGE,
    'timeout', '--signal=TERM', '--kill-after=5s', '40s', 'python', '-X', 'faulthandler', '-B', '/src/game_construction.py'])
created.check_returncode()
cid = created.stdout.decode().strip()
before = run(['docker', 'inspect', cid]); before.check_returncode()
(PRIVATE / 'container.before.json').write_bytes(before.stdout)
started = run(['docker', 'start', '--attach', cid], timeout=55)
after = run(['docker', 'inspect', cid]); after.check_returncode()
(PRIVATE / 'container.after.json').write_bytes(after.stdout)
state = json.loads(after.stdout)[0]['State']
if state['Running']:
    raise RuntimeError('UNKNOWN live container; reconcile exact identity before action')
archive = run(['tar', '-czf', '-', '-C', REMOTE, '.']); archive.check_returncode()
if len(archive.stdout) > 32 << 20:
    raise RuntimeError('output archive exceeds construction cap')
(PRIVATE / 'output.tar.gz').write_bytes(archive.stdout)
dest = HERE / 'native02'
dest.mkdir(exist_ok=False)
with tarfile.open(fileobj=io.BytesIO(archive.stdout), mode='r:gz') as stream:
    stream.extractall(dest, filter='data')
receipt = {'commands': COMMANDS, 'container_id': cid, 'client_exit': started.returncode,
           'state_after': state, 'source_before': pins,
           'source_after': {n:hashlib.sha256((HERE/'native'/n).read_bytes()).hexdigest() for n in pins},
           'archive_sha256': hashlib.sha256(archive.stdout).hexdigest(),
           'archive_bytes': len(archive.stdout), 'utc_saved': datetime.now(timezone.utc).isoformat()}
save(PRIVATE / 'receipt.json', receipt)
run(['docker', 'rm', cid]).check_returncode()
run(['umount', REMOTE]).check_returncode()
print(json.dumps({k:receipt[k] for k in ['container_id','client_exit','state_after','archive_bytes']}, sort_keys=True))
raise SystemExit(started.returncode or state['ExitCode'])
