"""Preformal prefix guard construction: no experiment/worker invocation."""
import hashlib
import json
from pathlib import Path
import tempfile
import batch_driver


def check():
    cases = []
    with tempfile.TemporaryDirectory() as t:
        root = Path(t); raw = b'{}\n' * 6
        (root / 'RAW.jsonl').write_bytes(raw)
        (root / 'batch-0.started.json').write_text('{"index":0}')
        rec = {'index':0, 'prefix_before':hashlib.sha256(b'').hexdigest(), 'prefix_after':hashlib.sha256(raw).hexdigest()}
        (root / 'batch-0.done.json').write_text(json.dumps(rec))
        assert batch_driver.validate_prefix(root, 1) == raw
        cases.append('valid_prefix')
        changes = [('consumed', lambda: (root/'batch-1.started.json').write_text('{}')),
                   ('wrong_hash', lambda: (root/'batch-0.done.json').write_text(json.dumps({**rec,'prefix_after':'0'*64}))),
                   ('missing_rows', lambda: (root/'RAW.jsonl').write_bytes(raw[:-3])),
                   ('missing_receipt', lambda: (root/'batch-0.done.json').unlink())]
        for name, change in changes:
            (root/'batch-1.started.json').unlink(missing_ok=True)
            (root/'RAW.jsonl').write_bytes(raw)
            (root/'batch-0.done.json').write_text(json.dumps(rec))
            change()
            try: batch_driver.validate_prefix(root, 1)
            except (ValueError, FileNotFoundError): cases.append(name)
            else: raise AssertionError('accepted '+name)
        for index in (-1, 9, True):
            try: batch_driver.validate_prefix(root,index)
            except ValueError: cases.append('invalid_index_'+str(index))
            else: raise AssertionError('accepted invalid index')
    return {'decision':'PASS_PREFIX_GUARD_CONSTRUCTION','checks':cases,'total':len(cases)}


if __name__ == '__main__':
    print(json.dumps(check(),sort_keys=True))

# Optional postformal evidence mutations; never invokes a worker or batch driver.
def evidence_controls(root):
    import shutil
    import batch_audit
    batch_audit.verify(root)
    results = []
    for kind in ('boolean_index','missing_receipt','wrong_prefix','wrong_allocation_rehashed'):
        with tempfile.TemporaryDirectory() as t:
            dest = Path(t)
            for p in root.iterdir():
                if p.is_file() and p.suffix in ('.json','.jsonl'):
                    shutil.copyfile(p,dest/p.name)
            if kind == 'boolean_index':
                p=dest/'batch-0.started.json'; m=json.loads(p.read_text()); m['index']=False; p.write_text(json.dumps(m))
            elif kind == 'missing_receipt':
                (dest/'batch-8.done.json').unlink()
            elif kind == 'wrong_prefix':
                p=dest/'batch-3.done.json'; d=json.loads(p.read_text()); d['prefix_after']='0'*64; p.write_text(json.dumps(d))
            else:
                raw=(dest/'RAW.jsonl').read_bytes().splitlines(keepends=True)
                r=json.loads(raw[0]); r['allocation']='predecessor-not-eligible'
                raw[0]=(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n').encode()
                (dest/'RAW.jsonl').write_bytes(b''.join(raw))
                for i in range(9):
                    p=dest/f'batch-{i}.done.json'; d=json.loads(p.read_text())
                    d['prefix_before']=hashlib.sha256(b''.join(raw[:i*6])).hexdigest()
                    d['prefix_after']=hashlib.sha256(b''.join(raw[:(i+1)*6])).hexdigest()
                    p.write_text(json.dumps(d))
                p=dest/'EXECUTION.json'; e=json.loads(p.read_text()); e['raw_sha256']=hashlib.sha256(b''.join(raw)).hexdigest(); p.write_text(json.dumps(e))
            try: batch_audit.verify(dest)
            except (ValueError,FileNotFoundError) as e: results.append({'case':kind,'rejected':True,'reason':str(e)})
            else: results.append({'case':kind,'rejected':False})
    return {'decision':'PASS_BATCH_CORRUPTION' if all(r['rejected'] for r in results) else 'FAIL_BATCH_CORRUPTION',
            'passed':sum(r['rejected'] for r in results),'total':len(results),'controls':results}


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 2:
        answer=evidence_controls(Path(sys.argv[1]).resolve())
        print(json.dumps(answer,sort_keys=True))
        raise SystemExit(answer['passed']!=answer['total'])
