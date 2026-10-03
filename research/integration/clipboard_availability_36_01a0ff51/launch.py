"""One-shot dedicated Engine launcher with finite attach and owned cleanup."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

BASE = ['orb', '-m', 'research-clipboard-36-01a0ff51-docker', '-u', 'root']
SOURCE = '/mnt/clipboard36-availability-src-01a0ff51'
OUTPUT = '/mnt/clipboard36-availability-out-01a0ff51'


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--phase', choices=['candidate', 'audit'], required=True)
    parser.add_argument('--freeze', type=Path, required=True); parser.add_argument('--records', type=Path, required=True)
    args = parser.parse_args(); freeze = json.loads(args.freeze.read_text()); args.records.mkdir(parents=True, exist_ok=True)
    record = args.records / (args.phase + '.receipt.json')
    with record.open('x') as stream: stream.write('{}\n')
    receipt = {'phase': args.phase, 'study_id': freeze['study_id'], 'freeze_sha256': hashlib.sha256(args.freeze.read_bytes()).hexdigest(),
               'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'commands': []}
    def save(): record.write_text(json.dumps(receipt, indent=2) + '\n')
    def run(command, timeout=15):
        argv = BASE + command; item = {'argv': argv, 'timeout_s': timeout,
                                     'start_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
        receipt['commands'].append(item); save()
        try:
            p = subprocess.run(argv, capture_output=True, timeout=timeout)
            item.update(exit=p.returncode, stdout=p.stdout.decode(), stderr=p.stderr.decode()); return p
        except subprocess.TimeoutExpired as error:
            item.update(timeout=True, stdout=(error.stdout or b'').decode(), stderr=(error.stderr or b'').decode()); raise
        finally: item['end_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat(); save()
    def hashes():
        p = run(['sha256sum', *[SOURCE + '/' + n for n in freeze['source_sha256']]])
        if p.returncode: raise RuntimeError('source query failed')
        return {l.split()[1].removeprefix(SOURCE + '/'): l.split()[0] for l in p.stdout.decode().splitlines()}
    name = 'clipboard36-availability-01a0ff51-formal01-' + args.phase
    started = False
    try:
        receipt['source_before'] = hashes()
        if receipt['source_before'] != freeze['source_sha256']: raise RuntimeError('frozen source mismatch')
        image = run(['docker', 'image', 'inspect', freeze['image_id'], '--format', '{{.Id}}'])
        if image.returncode or image.stdout.decode().strip() != freeze['image_id']: raise RuntimeError('image unavailable')
        command = ['docker', 'create', '--name', name, '--network', 'none', '--read-only', '--cpus', '.5', '--memory', '512m', '--pids-limit', '128', '--tmpfs', '/tmp:rw,nosuid,size=64m', '--mount', 'type=bind,src=' + SOURCE + ',dst=/src,readonly']
        if args.phase == 'candidate':
            command += ['--mount', 'type=bind,src=' + OUTPUT + ',dst=/out', freeze['image_id'], 'timeout', '--signal=TERM', '--kill-after=3s', '60s', 'python3', '-B', '/src/run.py', '--cases', '/src/cases.json', '--output', '/out/formal01']
        else:
            p = run(['mkdir', OUTPUT + '/audit01'])
            if p.returncode: raise RuntimeError('audit output already occupied/unavailable')
            command += ['--mount', 'type=bind,src=' + OUTPUT + '/formal01,dst=/evidence,readonly', '--mount', 'type=bind,src=' + OUTPUT + '/audit01,dst=/audit', freeze['image_id'], 'timeout', '--signal=TERM', '--kill-after=3s', '30s', 'python3', '-B', '/src/audit.py', '--cases', '/src/cases.json', '--raw', '/evidence/raw.json', '--output', '/audit/audit.json']
        p = run(command)
        if p.returncode: raise RuntimeError('create failed')
        receipt['container_id'] = p.stdout.decode().strip(); run(['docker', 'inspect', name])
        started = True
        attached = run(['docker', 'start', '--attach', name], timeout=75 if args.phase == 'candidate' else 45)
        p = run(['docker', 'inspect', name])
        if p.returncode: raise RuntimeError('state unavailable')
        state = json.loads(p.stdout)[0]['State']; receipt['state'] = state
        receipt['source_after'] = hashes()
        if args.phase == 'candidate':
            size = run(['du', '-sb', OUTPUT + '/formal01'])
            if size.returncode: raise RuntimeError('size query failed')
            receipt['output_bytes'] = int(size.stdout.decode().split()[0])
        receipt['status'] = 'EXIT_ZERO_SOURCE_EQUAL' if attached.returncode == state['ExitCode'] == 0 and not state['Running'] and receipt['source_after'] == freeze['source_sha256'] and receipt.get('output_bytes', 0) <= freeze['output_cap_bytes'] else 'FIRST_NONZERO_OR_MISMATCH'
    except Exception as error:
        receipt['status'] = 'STOP_FIRST_OUTCOME_OR_STATE_UNKNOWN'; receipt['error'] = type(error).__name__ + ': ' + str(error)
        if started:
            try:
                receipt['cleanup_attempt'] = run(['docker', 'kill', name]).returncode
                p = run(['docker', 'inspect', name]); receipt['post_cleanup_inspect_exit'] = p.returncode
            except Exception as cleanup: receipt['cleanup_error'] = str(cleanup)
    receipt['ended_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat(); save()
    print(json.dumps({'phase': args.phase, 'status': receipt['status']}))
    raise SystemExit(receipt['status'] != 'EXIT_ZERO_SOURCE_EQUAL')


if __name__ == '__main__': main()
