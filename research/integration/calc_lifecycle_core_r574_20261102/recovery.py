"""Experimental two-stage WSLc reconciliation, not an independent custodian."""
import math
from pathlib import Path
import time
from wslc_cleanup import cleanup_owned


def reconcile_owned(cid, run_id, allocation, *, timeout_s=20, cleanup=cleanup_owned):
    if type(timeout_s) not in (int, float) or not math.isfinite(timeout_s) or timeout_s <= 0:
        raise ValueError('positive finite timeout required')
    allocation = Path(allocation)
    deadline = time.monotonic() + timeout_s
    result = {'task_status': 'UNKNOWN', 'stop': {'status': 'UNKNOWN'},
              'remove': {'status': 'UNKNOWN'}}
    fatal = None
    for name, remove in (('stop', False), ('remove', True)):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            result[name] = {'status': 'UNKNOWN', 'error_type': 'DeadlineExceeded'}
            continue
        try:
            receipt = cleanup(cid, run_id, timeout_s=remaining,
                              journal_path=allocation / ('reconcile-' + name + '.jsonl'),
                              remove_exited=remove)
            result[name] = receipt if isinstance(receipt, dict) else {'status':'UNKNOWN', 'error_type':'InvalidReceipt'}
            result[name + '_returned_late'] = time.monotonic() >= deadline
        except BaseException as exc:
            result[name] = {'status':'UNKNOWN', 'error_type':type(exc).__name__}
            result[name + '_returned_late'] = time.monotonic() >= deadline
            if fatal is None and not isinstance(exc, Exception):
                fatal = exc
    if fatal is not None:
        raise fatal
    return result
