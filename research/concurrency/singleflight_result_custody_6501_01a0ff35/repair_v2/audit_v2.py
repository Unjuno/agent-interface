"""Versioned retained-data join; original frozen audit and raw stay unchanged."""
from pathlib import Path
import hashlib
import importlib.util

_original_path = Path(__file__).resolve().parent.parent / 'audit.py'
if hashlib.sha256(_original_path.read_bytes()).hexdigest() != 'f09d1d9e38ad95d73d2f0dd43730501704f35bfc34d7c7ed0cf6247408bad321':
    raise RuntimeError('original audit source pin mismatch')
_spec = importlib.util.spec_from_file_location('_custody_original_saved_data', _original_path)
_legacy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_legacy)
AuditError = _legacy.AuditError


def inspect(raw, freeze_bytes, fixture_bytes):
    """Keep every original gate, then reconcile each delivery's producer return."""
    result = _legacy.inspect(raw, freeze_bytes, fixture_bytes)
    checked = 0
    for row in raw['rows']:
        returns = {e['call']: e['ordinal'] for e in row['events']
                   if e['kind'] == 'read_return'}
        deliveries = {e['waiter']: e['ordinal'] for e in row['events']
                      if e['kind'] == 'delivery'}
        for waiter in ('A', 'B'):
            call = 1 if waiter == 'B' and row['policy'] == 'independent' else 0
            if returns[call] >= deliveries[waiter]:
                raise AuditError(f'return_before_delivery:{waiter}:call{call}')
            checked += 1
    return dict(result, audit_version='retained-delivery-return-v2',
                mapped_delivery_returns_verified=checked)
