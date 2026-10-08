"""Own-guest finite launcher. Receipts are one-shot; output/containers are retained."""
import argparse
import datetime
import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import Path

BASE = ['orb', '-m', 'research-clipboard-36-01a0ff51-docker', '-u', 'root']
PREFIX = '/mnt/edit49-01a0ff51-'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--records', type=Path, required=True)
    p.add_argument('--phase', required=True)
    p.add_argument('--image', required=True)
    a = p.parse_args()
    a.records.mkdir(exist_ok=True, parents=True)
    record = a.records / (a.phase + '.receipt.json')
    with record.open('x') as f: f.write('{}\n')
    r = dict(phase=a.phase, commands=[], started_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    def save(): record.write_text(json.dumps(r, indent=2) + '\n')
    def call(command, *, data=None, timeout=15, binary=False):
        argv = BASE + command
        item = dict(argv=argv, timeout_s=timeout, started_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
        r['commands'].append(item); save()
        try:
            result = subprocess.run(argv, input=data, capture_output=True, timeout=timeout)
            item.update(exit=result.returncode, stdout='[binary tar retained separately]' if binary else result.stdout.decode(), stderr=result.stderr.decode())
            return result
        except subprocess.TimeoutExpired as e:
            item.update(timeout=True, stdout=(e.stdout or b'').decode(errors='replace'), stderr=(e.stderr or b'').decode(errors='replace'))
            raise
        finally:
            item['ended_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat(); save()
    frozen = json.loads((a.source / 'FREEZE.json').read_text()) if a.phase in ('formal01', 'audit01') else None
    names = list(frozen['source_sha256']) if frozen else [str(f.relative_to(a.source)) for f in a.source.rglob('*') if f.is_file() and ('/' not in str(f.relative_to(a.source)) or str(f.relative_to(a.source)).startswith('vendor/'))]
    r['source_sha256'] = {name: hashlib.sha256((a.source / name).read_bytes()).hexdigest() for name in names}
    if frozen:
        r['freeze_sha256'] = hashlib.sha256((a.source / 'FREEZE.json').read_bytes()).hexdigest()
        if r['source_sha256'] != frozen['source_sha256'] or a.image != frozen['image_id']:
            raise ValueError('local frozen source/image mismatch')
    key = 'formal01' if a.phase == 'audit01' else a.phase
    gsrc, gout = PREFIX + key + '-src', PREFIX + key + '-out'
    if a.phase != 'audit01':
        z = call(['mkdir', gsrc, gout])
        if z.returncode: raise ValueError('guest namespace occupied')
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode='w') as tar:
            for name in names: tar.add(a.source / name, arcname=name)
        z = call(['tar', '-xf', '-', '-C', gsrc], data=buf.getvalue())
        if z.returncode: raise ValueError('source transfer failed')
    def remote_hashes():
        z = call(['sha256sum', *[gsrc + '/' + name for name in names]])
        if z.returncode: raise ValueError('remote source missing')
        return {line.split()[1].removeprefix(gsrc + '/'): line.split()[0] for line in z.stdout.decode().splitlines()}
    r['source_before'] = remote_hashes()
    if r['source_before'] != r['source_sha256']: raise ValueError('remote source mismatch')
    z = call(['docker', 'image', 'inspect', a.image, '--format', '{{.Id}}'])
    if z.returncode or z.stdout.decode().strip() != a.image: raise ValueError('image unavailable')
    name = 'edit49-01a0ff51-' + a.phase
    command = ['docker', 'create', '--name', name, '--network', 'none', '--read-only', '--cpus', '.5', '--memory', '512m', '--pids-limit', '128', '--tmpfs', '/tmp:rw,nosuid,size=64m', '--mount', 'type=bind,src=' + gsrc + ',dst=/src,readonly']
    if a.phase == 'audit01':
        gaudit = PREFIX + 'audit01-out'
        z = call(['mkdir', gaudit])
        if z.returncode: raise ValueError('audit output occupied')
        command += ['--mount', 'type=bind,src=' + gout + '/formal01,dst=/evidence,readonly', '--mount', 'type=bind,src=' + gaudit + ',dst=/out', a.image, 'timeout', '--kill-after=3s', '30s', 'python3', '-B', '/src/audit.py', '--cases', '/src/cases.json', '--evidence', '/evidence', '--output', '/out/audit.json']
        collect = gaudit
    elif a.phase.startswith('tests'):
        command += [a.image, 'timeout', '--kill-after=3s', '30s', 'python3', '-B', '-m', 'unittest', '-v', 'test_policy.py', 'test_audit.py']
        collect = gout
    else:
        cases = 'cases.json' if a.phase == 'formal01' else 'construction_cases.json'
        command += ['--mount', 'type=bind,src=' + gout + ',dst=/out', a.image, 'timeout', '--kill-after=3s', '90s', 'python3', '-B', '/src/run.py', '--cases', '/src/' + cases, '--output', '/out/' + a.phase]
        collect = gout
    z = call(command)
    if z.returncode: raise ValueError('create failed')
    r['container_id'] = z.stdout.decode().strip()
    r['inspect_before'] = json.loads(call(['docker', 'inspect', name]).stdout)
    try:
        z = call(['docker', 'start', '--attach', name], timeout=105 if a.phase != 'audit01' else 45)
    except subprocess.TimeoutExpired:
        r['cleanup_kill_exit'] = call(['docker', 'kill', name]).returncode
        raise
    r['state'] = json.loads(call(['docker', 'inspect', name]).stdout)[0]['State']
    r['source_after'] = remote_hashes()
    r['output_bytes'] = int(call(['du', '-sb', collect]).stdout.decode().split()[0])
    r['status'] = 'EXIT_ZERO_SOURCE_EQUAL' if z.returncode == r['state']['ExitCode'] == 0 and not r['state']['Running'] and r['source_before'] == r['source_after'] and r['output_bytes'] <= 2 * 1024 * 1024 else 'FIRST_NONZERO_OR_MISMATCH'
    archive = call(['tar', '-cf', '-', '-C', collect, '.'], binary=True)
    if archive.returncode: raise ValueError('collection failed')
    (a.records / (a.phase + '.tar')).write_bytes(archive.stdout)
    destination = a.records / a.phase
    destination.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive.stdout), mode='r') as tar: tar.extractall(destination, filter='data')
    r['ended_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat(); save()
    print(json.dumps({k: r[k] for k in ['phase', 'status', 'output_bytes']}))
    raise SystemExit(r['status'] != 'EXIT_ZERO_SOURCE_EQUAL')


if __name__ == '__main__':
    main()
