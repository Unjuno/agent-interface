"""One private-engine native block; saves first exit, inspection and raw files."""
import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VM = 'research-6183-t0-20261003'
IMAGE = 'sha256:c4839671ed0625dd38a53d8ed542bab16407c2b4c88a5ac84431695438c2b816'

def write(path, value):
    with path.open('x') as f: f.write(json.dumps(value, sort_keys=True, indent=2) + '\n')

def command(source, output, mode):
    return ['orbctl','run','-m',VM,'-u','root','docker','run','--pull=never',
            '--name','phase-effect-6067-a02-3cbf-'+mode,'--label','owner=3cbf',
            '--label','stage='+mode,'--user','501:501','--cpus','1',
            '--memory','512m','--memory-swap','512m','--pids-limit','64',
            '--network','none','--read-only','--cap-drop','ALL',
            '--security-opt','no-new-privileges','--tmpfs','/tmp:rw,nosuid,size=64m',
            '--mount','type=bind,src='+source+',dst=/src,readonly',
            '--mount','type=bind,src='+output+',dst=/out',IMAGE,
            'python3','-B','/src/producer.py','--out','/out/result','--'+mode]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', choices=('construction','formal'), required=True)
    ap.add_argument('--guest-source', required=True)
    ap.add_argument('--guest-output', required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    args = command(a.guest_source, a.guest_output, a.mode)
    readiness = {}
    if a.mode == 'formal':
        freeze = json.loads((HERE/'FREEZE.json').read_text())
        if args != freeze['producer_command']: raise ValueError('prospective command identity')
        for name, digest in freeze['candidate_sha256'].items():
            if hashlib.sha256((HERE/name).read_bytes()).hexdigest() != digest:
                raise ValueError('host source pin: '+name)
        pin_names = list(freeze['candidate_sha256']) + ['FREEZE.json']
        cmd = ['orbctl','run','-m',VM,'sha256sum']+[a.guest_source+'/'+n for n in pin_names]
        r = subprocess.run(cmd, capture_output=True, text=True, check=True)
        expected = {a.guest_source+'/'+n: hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in pin_names}
        actual = {line.split()[1]:line.split()[0] for line in r.stdout.splitlines()}
        if actual != expected: raise ValueError('staged guest source pins')
        readiness['guest_sha256'] = {'command': cmd, 'stdout': r.stdout}
        r = subprocess.run(['orbctl','run','-m',VM,'-u','root','docker','ps','-q'], capture_output=True,text=True,check=True)
        if r.stdout.strip(): raise ValueError('private engine not idle')
        readiness['private_engine_idle'] = True
    a.out.mkdir(exist_ok=False)
    write(a.out/'consumed.json', {'mode':a.mode,'started_ns':time.monotonic_ns(), 'readiness':readiness})
    mkdir = ['orbctl','run','-m',VM,'mkdir',a.guest_output]
    subprocess.run(mkdir,check=True)
    started = time.monotonic_ns()
    with (a.out/'launch.stdout.log').open('xb') as stdout, (a.out/'launch.stderr.log').open('xb') as stderr:
        r = subprocess.run(args,stdout=stdout,stderr=stderr)
    inspected = subprocess.run(['orbctl','run','-m',VM,'-u','root','docker','inspect',
                                '--format','{{json .}}',args[args.index('--name')+1]],capture_output=True,text=True)
    write(a.out/'launch.json', {'command':args,'exit_code':r.returncode,'started_ns':started,
                              'finished_ns':time.monotonic_ns(),'inspect_exit':inspected.returncode,
                              'inspect_stdout':inspected.stdout,'inspect_stderr':inspected.stderr})
    copy = ['orbctl','run','-m',VM,'cp','-a',a.guest_output+'/result','/mnt/mac'+str((a.out/'record').resolve())]
    copied = subprocess.run(copy,capture_output=True,text=True)
    write(a.out/'copy.json', {'command':copy,'exit_code':copied.returncode,'stdout':copied.stdout,'stderr':copied.stderr})
    if r.returncode or inspected.returncode or copied.returncode: raise SystemExit(2)

if __name__ == '__main__': main()
