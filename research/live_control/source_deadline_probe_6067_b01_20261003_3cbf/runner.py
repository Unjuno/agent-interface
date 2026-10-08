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

def receipt(cmd):
    start=time.monotonic_ns()
    r=subprocess.run(cmd,capture_output=True,text=True)
    return {'command':cmd,'started_ns':start,'finished_ns':time.monotonic_ns(),
            'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr}

def transport_commands(source, output, out, pin_names):
    return {'hash_command':['orbctl','run','-m',VM,'sha256sum']+[source+'/'+n for n in pin_names],
            'idle_command':['orbctl','run','-m',VM,'-u','root','docker','ps','-q'],
            'mkdir_command':['orbctl','run','-m',VM,'mkdir',output],
            'inspect_command':['orbctl','run','-m',VM,'-u','root','docker','inspect','--format','{{json .}}','source-deadline-6067-b01-3cbf'],
            'copy_command':['orbctl','run','-m',VM,'cp','-a',output+'/result','/mnt/mac'+str((out/'record').resolve())]}

def command(source, output, mode):
    return ['orbctl','run','-m',VM,'-u','root','docker','run','--pull=never',
            '--name','source-deadline-6067-b01-3cbf','--label','owner=3cbf',
            '--label','stage='+mode,'--user','501:501','--cpus','1',
            '--memory','512m','--memory-swap','512m','--pids-limit','64',
            '--network','none','--read-only','--cap-drop','ALL',
            '--security-opt','no-new-privileges','--tmpfs','/tmp:rw,nosuid,size=64m',
            '--mount','type=bind,src='+source+',dst=/src,readonly',
            '--mount','type=bind,src='+output+',dst=/out',IMAGE,
            'python3','-B','/src/probe.py','--out','/out/result' ]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--guest-source', required=True)
    ap.add_argument('--guest-output', required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    args = command(a.guest_source, a.guest_output, 'source-boundary-diagnostic')
    freeze = json.loads((HERE/'FREEZE.json').read_text())
    if args != freeze['producer_command']: raise ValueError('prospective command identity')
    for name, digest in freeze['source_sha256'].items():
        if hashlib.sha256((HERE/name).read_bytes()).hexdigest() != digest:
            raise ValueError('host source pin: '+name)
    pin_names = list(freeze['source_sha256']) + ['FREEZE.json']
    commands=transport_commands(a.guest_source,a.guest_output,a.out,pin_names)
    for k,v in commands.items():
        if freeze[k]!=v: raise ValueError('prospective transport command '+k)
    before=receipt(commands['hash_command'])
    expected = {a.guest_source+'/'+n: hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in pin_names}
    actual = {line.split()[1]:line.split()[0] for line in before['stdout'].splitlines()}
    if before['exit_code'] or actual != expected: raise ValueError('staged guest source pins')
    idle=receipt(commands['idle_command'])
    if idle['exit_code'] or idle['stdout'].strip(): raise ValueError('private engine not idle')
    readiness={'guest_sha256':before,'idle':idle}
    a.out.mkdir(exist_ok=False)
    consumed={'mode':'source-boundary-diagnostic','started_ns':time.monotonic_ns(),'readiness':readiness}
    consumed['mkdir']=receipt(commands['mkdir_command'])
    write(a.out/'consumed.json',consumed)
    if consumed['mkdir']['exit_code']: raise SystemExit(2)
    started = time.monotonic_ns()
    with (a.out/'launch.stdout.log').open('xb') as stdout, (a.out/'launch.stderr.log').open('xb') as stderr:
        r = subprocess.run(args,stdout=stdout,stderr=stderr)
    finished=time.monotonic_ns()
    inspected=receipt(commands['inspect_command'])
    write(a.out/'launch.json', {'command':args,'exit_code':r.returncode,'started_ns':started,
                              'finished_ns':finished,'inspection':inspected,'inspect_exit':inspected['exit_code'],
                              'inspect_stdout':inspected['stdout'],'inspect_stderr':inspected['stderr']})
    copied=receipt(commands['copy_command'])
    write(a.out/'copy.json',copied)
    post=receipt(commands['hash_command'])
    write(a.out/'post_source.json',post)
    if post['exit_code'] or post['stdout'] != readiness['guest_sha256']['stdout']:
        raise SystemExit(2)
    if r.returncode or inspected['exit_code'] or copied['exit_code']: raise SystemExit(2)

if __name__ == '__main__': main()
