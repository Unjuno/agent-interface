"""Verify delivery against immutable first audit, NOT repeat official science audit."""
import hashlib
import json
from pathlib import Path

AUDIT_SHA = '047e1a0f6b89679dd38854e01041e97e6ff15e818a42d76426b09a4ff7152322'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def inventory(root):
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob('*') if path.is_file()}


def check_delivery(root):
    audit_bytes = (root / 'raw/audit/AUDIT.json').read_bytes()
    require(hashlib.sha256(audit_bytes).hexdigest() == AUDIT_SHA, 'audit anchor')
    audit = json.loads(audit_bytes)
    expected = audit['payload_sha256']
    require(len(expected) == 73, 'inventory cardinality')
    for copy in ('native', 'export'):
        require(inventory(root / 'raw' / copy) == expected, 'inventory ' + copy)
    require(audit['scientific_pass'] is True and audit['producer_reruns'] == 0,
            'saved audit outcome')
    for name in ('native', 'audit'):
        receipt = json.loads((root / f'raw/{name}-container-inspect.json').read_text())
        require(len(receipt) == 1, 'receipt cardinality')
        state = receipt[0]['State']
        require(state['Running'] is False and state['OOMKilled'] is False
                and type(state['ExitCode']) is int and state['ExitCode'] == 0,
                'receipt terminal')
    return {'files': 73, 'delivery': 'VERIFIED_FIRST_AUDIT_ANCHOR',
            'scope': 'retained delivery only; no producer or official auditor rerun'}


if __name__ == '__main__':
    print(json.dumps(check_delivery(Path(__file__).resolve().parent), sort_keys=True))
