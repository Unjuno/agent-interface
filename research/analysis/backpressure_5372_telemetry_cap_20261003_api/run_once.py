"""Exclusive bounded analytical invocation and raw-only audit, no retries."""
import datetime
import hashlib
import json
import os
import pathlib
import platform
import resource
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent

def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def limits():
    resource.setrlimit(resource.RLIMIT_AS, (512*1024*1024,512*1024*1024))
    resource.setrlimit(resource.RLIMIT_CPU, (60,60))
    resource.setrlimit(resource.RLIMIT_FSIZE, (64*1024*1024,64*1024*1024))

def launch(command, output, label):
    started = utc()
    monotonic = time.monotonic()
    with (output/(label+'.stdout.txt')).open('xb') as stdout, (output/(label+'.stderr.txt')).open('xb') as stderr:
        process = subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=stderr,
                                 preexec_fn=limits, env={**os.environ, 'PYTHONDONTWRITEBYTECODE':'1'}, timeout=90)
    return dict(command=command, cwd=str(ROOT), started_utc=started, ended_utc=utc(),
                elapsed_s=time.monotonic()-monotonic, exit_code=process.returncode)

if __name__ == '__main__':
    freeze = json.loads((ROOT/'FREEZE.json').read_text())
    for name, expected in freeze['source_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != expected:
            raise SystemExit('STOP_SOURCE_IDENTITY: '+name)
    output = ROOT/'run_01'
    output.mkdir(exist_ok=False)
    cgroup = {}
    for name in ('memory.max','cpu.max','pids.max'):
        path = pathlib.Path('/sys/fs/cgroup')/name
        cgroup[name] = path.read_text().strip() if path.exists() else 'unavailable'
    record = dict(run_id=freeze['run_id'], freeze_sha256=hashlib.sha256((ROOT/'FREEZE.json').read_bytes()).hexdigest(),
                  source_sha256=freeze['source_sha256'], started_utc=utc(),
                  python=sys.version, executable=sys.executable, platform=platform.platform(),
                  uname=list(platform.uname()), cgroup=cgroup,
                  per_child_requested_limits=dict(address_space_bytes=512*1024*1024,cpu_s=60,file_bytes=64*1024*1024),
                  candidate_invocations=0,auditor_invocations=0,retries=0)
    destination = output/'RUN.json'
    destination.write_text(json.dumps(record, indent=2)+'\n')
    try:
        record['candidate_invocations'] = 1
        record['candidate'] = launch([sys.executable,str(ROOT/'candidate.py'),str(output/'raw.jsonl')],output,'candidate')
        destination.write_text(json.dumps(record,indent=2)+'\n')
        if record['candidate']['exit_code'] == 0:
            record['auditor_invocations'] = 1
            record['auditor'] = launch([sys.executable,str(ROOT/'audit.py'),str(output/'raw.jsonl'),str(output/'audit.json')],output,'auditor')
            if record['auditor']['exit_code'] == 0:
                record['disposition'] = json.loads((output/'audit.json').read_text())['decision']
            else:
                record['disposition'] = 'STOP_AUDITOR_NONZERO'
        else:
            record['disposition'] = 'STOP_CANDIDATE_NONZERO'
    except Exception as error:
        record['disposition'] = 'STOP_LAUNCH_OR_TIMEOUT'
        record['exception'] = repr(error)
    finally:
        record['ended_utc'] = utc()
        record['output_sha256'] = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.name!='RUN.json'}
        destination.write_text(json.dumps(record,indent=2)+'\n')
    print(record['disposition'])
    if record['disposition'].startswith('STOP'):
        raise SystemExit(1)
