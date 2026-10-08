"""Prospectively pinned one-shot container create/start and receipt recorder."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

MACHINE = 'research-clipboard-36-01a0ff51-docker'
ENGINE_SOURCE = '/mnt/clipboard36-x11-src-01a0ff51'
ENGINE_OUTPUT = '/mnt/clipboard36-x11-out-01a0ff51'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['candidate', 'audit'], required=True)
    parser.add_argument('--freeze', type=Path, required=True)
    parser.add_argument('--records', type=Path, required=True)
    args = parser.parse_args()
    freeze = json.loads(args.freeze.read_text())
    args.records.mkdir(parents=True, exist_ok=True)
    record = args.records / (args.phase + '.receipt.json')
    if record.exists(): raise RuntimeError('phase receipt exists: reconcile, never rerun')
    receipt = {'study_id': freeze['study_id'], 'phase': args.phase,
               'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'commands': [], 'freeze_sha256': hashlib.sha256(args.freeze.read_bytes()).hexdigest()}
    def save(): record.write_text(json.dumps(receipt, indent=2) + '\n')
    def run(command, timeout=60):
        argv = ['orb', '-m', MACHINE, '-u', 'root', *command]
        item = {'argv': argv, 'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
        receipt['commands'].append(item); save()
        result = subprocess.run(argv, capture_output=True, timeout=timeout)
        item.update(exit_code=result.returncode, stdout=result.stdout.decode(), stderr=result.stderr.decode(),
                    ended_at=datetime.datetime.now(datetime.timezone.utc).isoformat()); save()
        return result
    save()
    try:
        pins = freeze['source_sha256']
        def source_hashes():
            r = run(['sha256sum', *[ENGINE_SOURCE + '/' + name for name in pins]])
            if r.returncode: raise RuntimeError('source hash query failed')
            return {line.split()[1].removeprefix(ENGINE_SOURCE + '/'): line.split()[0] for line in r.stdout.decode().splitlines()}
        receipt['source_before'] = source_hashes(); save()
        if receipt['source_before'] != pins: raise RuntimeError('frozen source mismatch')
        image = run(['docker', 'image', 'inspect', freeze['image_id'], '--format', '{{.Id}}'])
        if image.returncode or image.stdout.decode().strip() != freeze['image_id']: raise RuntimeError('frozen image unavailable')
        name = 'clipboard36-x11-01a0ff51-formal01-' + args.phase
        command = ['docker', 'create', '--name', name, '--network', 'none', '--read-only', '--cpus', '.5', '--memory', '512m', '--pids-limit', '128', '--tmpfs', '/tmp:rw,nosuid,size=64m', '--mount', 'type=bind,src=' + ENGINE_SOURCE + ',dst=/src,readonly']
        if args.phase == 'candidate':
            command += ['--mount', 'type=bind,src=' + ENGINE_OUTPUT + ',dst=/out', freeze['image_id'], 'python3', '-B', '/src/run.py', '--cases', '/src/cases.json', '--output', '/out/formal01']
        else:
            r = run(['mkdir', ENGINE_OUTPUT + '/audit01'])
            if r.returncode: raise RuntimeError('fresh audit output unavailable')
            command += ['--mount', 'type=bind,src=' + ENGINE_OUTPUT + '/formal01,dst=/evidence,readonly', '--mount', 'type=bind,src=' + ENGINE_OUTPUT + '/audit01,dst=/audit', freeze['image_id'], 'python3', '-B', '/src/audit.py', '--cases', '/src/cases.json', '--raw', '/evidence/raw.json', '--output', '/audit/audit.json']
        created = run(command)
        if created.returncode: raise RuntimeError('container create failed; preserve first receipt')
        receipt['container_id'] = created.stdout.decode().strip(); save()
        run(['docker', 'inspect', name])
        started = run(['docker', 'start', '--attach', name], timeout=None)
        inspected = run(['docker', 'inspect', name])
        if inspected.returncode: raise RuntimeError('container state unavailable')
        state = json.loads(inspected.stdout)[0]['State']; receipt['container_state'] = state
        receipt['client_exit'] = started.returncode
        if args.phase == 'candidate':
            size = run(['du', '-sb', ENGINE_OUTPUT + '/formal01'])
            if size.returncode: raise RuntimeError('retained size unavailable')
            receipt['output_bytes'] = int(size.stdout.decode().split()[0])
            receipt['within_output_cap'] = receipt['output_bytes'] <= freeze['output_cap_bytes']
        receipt['source_after'] = source_hashes()
        receipt['ended_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        receipt['status'] = 'EXIT_ZERO_SOURCE_EQUAL' if started.returncode == state['ExitCode'] == 0 and receipt['source_after'] == pins and not state['Running'] and receipt.get('within_output_cap', True) else 'FIRST_OUTCOME_NONZERO_OR_MISMATCH'
        save(); print(json.dumps({'phase': args.phase, 'status': receipt['status'], 'client_exit': started.returncode, 'container_exit': state['ExitCode']}))
        raise SystemExit(0 if receipt['status'] == 'EXIT_ZERO_SOURCE_EQUAL' else 1)
    except Exception as error:
        receipt['status'] = 'FIRST_OUTCOME_OR_STATE_UNKNOWN'; receipt['error'] = type(error).__name__ + ': ' + str(error)
        save(); raise


if __name__ == '__main__': main()
