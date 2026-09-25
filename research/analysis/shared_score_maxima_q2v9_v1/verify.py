"""Read-only reconstruction. Never imports or invokes the candidate runner."""
import base64
import hashlib
import json
from pathlib import Path
import sys
import zlib
from audit import audit
from controls import check


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2)+'\n').encode()


def main():
    root = Path(__file__).resolve().parent
    freeze_bytes = (root/'FREEZE.json').read_bytes()
    freeze = json.loads(freeze_bytes)
    for path, digest in freeze['files'].items():
        if hashlib.sha256((root/path).read_bytes()).hexdigest() != digest:
            raise ValueError('source mismatch: '+path)
    retained = root/'retained'
    if (retained/'records.json').exists():
        raw = (retained/'records.json').read_bytes()
    else:
        delivery = json.loads((root/'DELIVERY.json').read_text())
        wire = (retained/'records.json.zlib.b64').read_bytes()
        if hashlib.sha256(wire).hexdigest() != delivery['encoded_sha256']:
            raise ValueError('encoded identity')
        packed = base64.b64decode(wire.strip(), validate=True)
        raw = zlib.decompress(packed)
        if len(raw) != delivery['raw_bytes'] or hashlib.sha256(raw).hexdigest() != delivery['raw_sha256']:
            raise ValueError('decoded identity')
    data = json.loads(raw)
    receipt = json.loads((retained/'PROCESS.json').read_text())
    if hashlib.sha256(raw).hexdigest() != receipt['stdout_sha256']:
        raise ValueError('process output identity')
    if (retained/'stderr.txt').read_bytes():
        raise ValueError('stderr nonempty')
    result = audit(data, receipt, freeze['corpus_sha256'], hashlib.sha256(freeze_bytes).hexdigest())
    if result['errors'] or canonical(result) != (retained/'AUDIT.json').read_bytes():
        raise ValueError('original audit differs or fails')
    checks = check(data, receipt, freeze['corpus_sha256'], hashlib.sha256(freeze_bytes).hexdigest())
    if not checks['passed'] or canonical(checks) != (retained/'CONTROLS.json').read_bytes():
        raise ValueError('original controls differ or fail')
    print(json.dumps({'decision':'PASS_READONLY_RECONSTRUCTION', 'source_files':len(freeze['files']),
                      'records':len(data['rows']), 'raw_bytes':len(raw), 'audit_byte_equal':True,
                      'controls_byte_equal':True, 'new_candidate_invocations':0}, sort_keys=True))


if __name__ == '__main__':
    main()
