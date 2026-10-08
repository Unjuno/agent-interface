"""Exactly one producer and one primary raw-only auditor; preserves first exits."""
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
OUT = pathlib.Path('/out')


def main():
    freeze = json.loads((ROOT/'FREEZE.json').read_bytes())
    for path,pin in freeze['source_sha256'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest() != pin:
            raise RuntimeError('STOP: frozen source hash mismatch '+path)
    if any(OUT.iterdir()):
        raise RuntimeError('STOP: output allocation already occupied')
    config = json.loads((ROOT/'input.json').read_bytes())
    receipts = []
    for name,command,timeout in (
        ('candidate',[sys.executable,'-B',str(ROOT/'candidate.py'),str(OUT/'raw.jsonl')],config['producer_timeout_seconds']),
        ('auditor',[sys.executable,'-B',str(ROOT/'audit.py'),str(OUT/'raw.jsonl'),str(OUT/'audit.json')],config['auditor_timeout_seconds'])):
        receipt = {'component':name,'command':command,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        try:
            run = subprocess.run(command,capture_output=True,timeout=timeout)
            stdout,stderr,code = run.stdout,run.stderr,run.returncode
        except subprocess.TimeoutExpired as exc:
            stdout,stderr,code = exc.stdout or b'',exc.stderr or b'',124
        receipt.update({'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':code,'stdout_sha256':hashlib.sha256(stdout).hexdigest(),'stderr_sha256':hashlib.sha256(stderr).hexdigest()})
        (OUT/(name+'.stdout')).write_bytes(stdout)
        (OUT/(name+'.stderr')).write_bytes(stderr)
        receipts.append(receipt)
        (OUT/'driver_receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
    print(json.dumps({'allocation':config['allocation'],'candidate_attempts':1,'auditor_attempts':1,'retries':0,'exit_codes':[r['exit_code'] for r in receipts]}))
    return 0 if all(r['exit_code']==0 for r in receipts) else 2


if __name__ == '__main__':
    raise SystemExit(main())
