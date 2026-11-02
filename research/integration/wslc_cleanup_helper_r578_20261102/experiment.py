import json, re, subprocess, sys, time, uuid
from pathlib import Path
root = Path(sys.argv[1])
sys.path.insert(0, sys.argv[2])
from wslc_cleanup import cleanup_owned
run = uuid.uuid4().hex
cidfile = root / 'container.cid'
image = 'sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25'
result = {'status': 'UNKNOWN', 'run_id': run}

def invoke(name, args, timeout):
    (root / (name + '.command.json')).write_text(json.dumps(args, indent=2), encoding='utf-8')
    try:
        p = subprocess.run(args, capture_output=True, timeout=timeout)
        (root / (name + '.stdout')).write_bytes(p.stdout)
        (root / (name + '.stderr')).write_bytes(p.stderr)
        (root / (name + '.result.json')).write_text(json.dumps({'exit': p.returncode}), encoding='utf-8')
        return p
    except subprocess.TimeoutExpired as exc:
        (root / (name + '.stdout')).write_bytes(exc.stdout or b'')
        (root / (name + '.stderr')).write_bytes(exc.stderr or b'')
        (root / (name + '.result.json')).write_text(json.dumps({'status': 'timeout'}), encoding='utf-8')
        raise

try:
    args = ['wslc','run','--detach','--rm','--name','ai-r578-'+run[:16], '--label','agent-interface.run-id='+run,'--cidfile',str(cidfile),'--network','none','--cpus','1','--memory','1g','--pull','never','--entrypoint','python3',image,'-c','import time; time.sleep(60)']
    p = invoke('launch', args, 15)
    if p.returncode: raise RuntimeError('launch failure')
    deadline = time.monotonic() + 5
    cid = None
    while time.monotonic() < deadline:
        if cidfile.exists():
            candidate = cidfile.read_text(encoding='ascii').strip()
            if re.fullmatch('[0-9a-f]{64}', candidate):
                cid = candidate
                break
        time.sleep(.05)
    if cid is None: raise RuntimeError('complete CID unavailable')
    result['cid'] = cid
    wrong = ('0' if cid[0] != '0' else '1') + cid[1:]
    p = invoke('negative_list', ['wslc','container','list','--all','--filter','id='+wrong,'--format','json','--no-trunc'], 8)
    if p.returncode or p.stdout.strip() or p.stderr: raise RuntimeError('negative control failed')
    receipt = cleanup_owned(cid, run, timeout_s=20, journal_path=root/'cleanup.jsonl')
    result['receipt'] = receipt
    result['status'] = receipt['status']
except BaseException as exc:
    result['error_type'] = type(exc).__name__
finally:
    (root/'result.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'status':result['status'], 'error_type': result.get('error_type'), 'cid_present': 'cid' in result}))
