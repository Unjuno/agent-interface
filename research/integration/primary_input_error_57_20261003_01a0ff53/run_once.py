"""One prospective eight-child ordinary comparison; output is exclusive-create."""
import datetime, hashlib, json, os, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
NODE = '/opt/homebrew/bin/node'
SCENARIOS = ['before_request', 'pending_success', 'pending_failure', 'eof_pending']

def digest(data):
    return hashlib.sha256(data).hexdigest()

freeze = json.loads((HERE / 'FREEZE.json').read_bytes())
for path, pin in freeze['files'].items():
    data = (HERE / path).read_bytes()
    if len(data) != pin['bytes'] or digest(data) != pin['sha256']:
        raise ValueError('freeze source mismatch: ' + path)
binary = pathlib.Path(NODE).resolve()
if digest(binary.read_bytes()) != freeze['node_binary_sha256']:
    raise ValueError('Node binary changed')
destination = pathlib.Path(sys.argv[1]).resolve()
destination.mkdir(parents=True, exist_ok=False)
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
source_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=HERE).decode().strip()
code = (HERE / 'child_probe.cjs').read_text()
rows = []
for arm in ('baseline', 'candidate'):
    for scenario in SCENARIOS:
        row_start = datetime.datetime.now(datetime.timezone.utc).isoformat()
        env = dict(os.environ, PRIMARY_READ_SCENARIO=scenario)
        # eval imports relative to this exact frozen source directory. No private
        # absolute path enters the child's stack or the published command text.
        child = subprocess.run([NODE, '--eval', code], cwd=HERE / arm, env=env,
                               capture_output=True, timeout=5)
        stdout, stderr = child.stdout, child.stderr
        rows.append({'arm': arm, 'scenario': scenario,
                     'started_utc': row_start,
                     'ended_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                     'exit_code': child.returncode,
                     'stdout': stdout.decode(), 'stderr': stderr.decode(),
                     'stdout_sha256': digest(stdout), 'stderr_sha256': digest(stderr)})
report = {'schema': 'primary-read-error-comparison-v1', 'source_commit': source_commit,
          'freeze_sha256': digest((HERE / 'FREEZE.json').read_bytes()),
          'started_utc': started, 'ended_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'node_version': subprocess.check_output([NODE, '--version']).decode().strip(),
          'command': ['node', '--eval', 'exact child_probe.cjs contents'],
          'cwd_roles': ['baseline', 'candidate'], 'scenarios': SCENARIOS,
          'rows': rows, 'attempts': 1, 'retries': 0}
raw = (json.dumps(report, sort_keys=True, indent=2) + '\n').encode()
with (destination / 'raw.json').open('xb') as out:
    out.write(raw)
print(json.dumps({'rows': len(rows), 'raw_bytes': len(raw), 'raw_sha256': digest(raw),
                  'source_commit': source_commit, 'child_exits': [r['exit_code'] for r in rows]}))
