"""Host launcher. Private exact receipts stay outside public source tree."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import time

HERE=Path(__file__).resolve().parent
VM='research-6695-docker-01a0ff52'
IMAGE='python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016'
PREFIX=['/opt/homebrew/bin/orb','run','-m',VM,'-u','root']


def utc():return datetime.now(timezone.utc).isoformat()
def sha(b):return hashlib.sha256(b).hexdigest()
def save(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')


def main():
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['construction01','candidate01','audit01']);p.add_argument('--private',type=Path,required=True);a=p.parse_args()
    a.private.mkdir(parents=True,exist_ok=False)
    if a.phase!='construction01':
        freeze=json.loads((HERE/'FREEZE.json').read_text())
        for rel,digest in freeze['source_sha256'].items():
            if sha((HERE/rel).read_bytes())!=digest:raise ValueError('frozen source changed:'+rel)
    source_before={str(f.relative_to(HERE)):sha(f.read_bytes()) for f in HERE.rglob('*.py') if '/construction/' not in str(f)}
    commands=[]
    def run(args,timeout=15):
        argv=PREFIX+args;record={'argv':argv,'utc_start':utc()};commands.append(record)
        save(a.private/'execution.json',{'phase':a.phase,'commands':commands,'source_before':source_before})
        start=time.monotonic_ns()
        try:
            r=subprocess.run(argv,capture_output=True,timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            record.update(utc_end=utc(),observation_timeout=True,stdout_sha256=sha(exc.stdout or b''),stderr_sha256=sha(exc.stderr or b''))
            save(a.private/'execution.json',{'phase':a.phase,'commands':commands,'source_before':source_before,'state':'UNKNOWN; reconcile exact container, no resubmit'})
            raise
        record.update(utc_end=utc(),outer_wall_ns=time.monotonic_ns()-start,exit_code=r.returncode,
                      stdout_sha256=sha(r.stdout),stderr_sha256=sha(r.stderr))
        index=len(commands)-1;(a.private/f'command-{index:02d}.stdout').write_bytes(r.stdout);(a.private/f'command-{index:02d}.stderr').write_bytes(r.stderr)
        save(a.private/'execution.json',{'phase':a.phase,'commands':commands,'source_before':source_before})
        return r
    listing=run(['docker','ps','--format','{{.ID}} {{.Names}}'])
    if listing.returncode or listing.stdout.strip():raise RuntimeError('private Engine unavailable or occupied')
    image=run(['docker','image','inspect',IMAGE]);image.check_returncode();(a.private/'image.inspect.json').write_bytes(image.stdout)
    remote='/var/tmp/scorer-native-b64b-'+a.phase
    prep=run(['mkdir','-m','777',remote]);prep.check_returncode()
    guest_source='/mnt/mac'+str(HERE)
    flags=['docker','create','--name','scorer-native-b64b-'+a.phase,'--pull','never','--network','none',
           '--cpus','1','--memory','256m','--memory-swap','256m','--pids-limit','64','--read-only',
           '--cap-drop','ALL','--security-opt','no-new-privileges','--user','65534:65534',
           '--tmpfs','/tmp:rw,size=32m','-v',guest_source+':/src:ro','-v',remote+':/out:rw']
    if a.phase=='audit01':
        flags += ['-v','/var/tmp/scorer-native-b64b-candidate01/result:/raw:ro']
        argv=['python','-B','/src/auditor.py','/src/deck.json','/raw','/out/AUDIT.json']
    else:
        deck='construction/deck-01.json' if a.phase=='construction01' else 'deck.json'
        argv=['python','-B','/src/candidate.py','--deck','/src/'+deck,'--out','/out/result']
    created=run(flags+[IMAGE]+argv);created.check_returncode();cid=created.stdout.decode().strip()
    before=run(['docker','inspect',cid]);before.check_returncode();(a.private/'container.before.json').write_bytes(before.stdout)
    started=run(['docker','start','--attach',cid],timeout=30 if a.phase!='audit01' else 15)
    after=run(['docker','inspect',cid]);after.check_returncode();(a.private/'container.after.json').write_bytes(after.stdout)
    inspect=json.loads(after.stdout)[0]
    if inspect['State']['Running']:raise RuntimeError('container still running; reconcile before action')
    archive=run(['tar','-czf','-','-C',remote,'.']);archive.check_returncode()
    if len(archive.stdout)>8<<20:raise RuntimeError('archive cap exceeded')
    dest=HERE/'construction/run-01' if a.phase=='construction01' else HERE/('formal_01/candidate' if a.phase=='candidate01' else 'formal_01/audit')
    dest.mkdir(parents=True,exist_ok=False)
    with tarfile.open(fileobj=io.BytesIO(archive.stdout),mode='r:gz') as t:t.extractall(dest,filter='data')
    source_after={rel:sha((HERE/rel).read_bytes()) for rel in source_before}
    receipt={'phase':a.phase,'image':IMAGE,'container_id':cid,'client_exit':started.returncode,
             'container_exit':inspect['State']['ExitCode'],'running':inspect['State']['Running'],
             'source_before':source_before,'source_after':source_after,'commands':commands,
             'image_inspection_sha256':sha(image.stdout),'archive_sha256':sha(archive.stdout),
             'utc_saved':utc()}
    save(a.private/'receipt.json',receipt)
    public=json.loads(json.dumps(receipt))
    for record in public['commands']:
        record['argv']=[x.replace(guest_source,'{OWN_SOURCE}') for x in record['argv']]
    public['publication']={'argv_is_redacted_derivative':True,'redaction':'private absolute source mount -> {OWN_SOURCE}',
                           'private_original_receipt_sha256':sha((a.private/'receipt.json').read_bytes())}
    save(dest/'RECEIPT.public.json',public)
    removed=run(['docker','rm',cid]);removed.check_returncode()
    print(json.dumps({'phase':a.phase,'client_exit':started.returncode,'container_exit':inspect['State']['ExitCode'],
         'container_id':cid,'source_unchanged':source_before==source_after,'output':str(dest.relative_to(HERE))}))
    raise SystemExit(started.returncode or inspect['State']['ExitCode'])


if __name__=='__main__':main()
