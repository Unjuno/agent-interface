"""Additional independent-auditor tests on copied, rehashed evidence only."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from audit import audit
from test_audit import controls, read, write


def main(source, mode):
    result = controls(source, mode)
    for name in ('missing_external_exit', 'nonzero_external_exit', 'wrong_batch_prefix'):
        with tempfile.TemporaryDirectory(prefix='batch-controls-') as tmp:
            root = Path(tmp)/'data'
            shutil.copytree(source, root)
            target = root/'BATCH-00.EXECUTION.json'
            if name == 'missing_external_exit':
                target.unlink()
            elif name == 'nonzero_external_exit':
                obj = read(target); obj['exit'] = 3; write(target, obj)
            else:
                target = root/'BATCH-00.DONE.json'
                obj = read(target); obj['prefix_sha256'] = '0'*64; write(target, obj)
            manifest = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in sorted(root.rglob('*')) if p.is_file() and p.name != 'MANIFEST.json'}
            write(root/'MANIFEST.json', manifest)
            checked = audit(root, mode)
            result['controls'].append({'control': name, 'rejected': bool(checked['errors']),
                                       'errors': checked['errors']})
    result['count'] = len(result['controls'])
    result['passed'] = all(item['rejected'] for item in result['controls'])
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('root', type=Path)
    p.add_argument('--mode', choices=('construction', 'formal'), required=True)
    a = p.parse_args(); raise SystemExit(main(a.root, a.mode))
