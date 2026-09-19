"""Bounded file exchange for the existing private native self-use harness.

One immutable request slot per stage. Resuming only reads; it never republishes.
This is a local research adapter, not a crash-persistent transport protocol.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
import time

from agent_review import review_native


def _process_identity(pid):
    row = Path(f'/proc/{pid}/stat').read_text()
    fields = row[row.rfind(')') + 2:].split()
    return fields[19], fields[0]  # Linux starttime and state.


def current_owner_identity():
    """Identify one local Linux process incarnation, not merely a reusable PID."""
    namespace = Path('/proc/self/ns/pid').stat()
    return {'schema': 'agent-interface/local-owner-v1', 'pid': os.getpid(),
            'starttime': _process_identity(os.getpid())[0],
            'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'pid_namespace': [namespace.st_dev, namespace.st_ino]}


def owner_state(root):
    """Read-only diagnostic; never authorizes restart, replay or input release."""
    path = Path(root)/'owner.json'
    if not path.exists():
        return None  # Historical harnesses did not record an owner.
    try:
        owner = json.loads(path.read_bytes())
        local = current_owner_identity()
        if (owner.get('schema') != local['schema'] or type(owner.get('pid')) is not int
                or owner['pid'] <= 0 or type(owner.get('starttime')) is not str
                or owner.get('boot_id') != local['boot_id']
                or owner.get('pid_namespace') != local['pid_namespace']):
            return {'state': 'unverifiable', 'reason': 'owner_identity_or_local_context_mismatch'}
        try:
            starttime, state = _process_identity(owner['pid'])
        except FileNotFoundError:
            return {'state': 'terminal', 'reason': 'owner_process_absent'}
        if starttime != owner['starttime']:
            return {'state': 'terminal', 'reason': 'owner_incarnation_replaced'}
        if state in ('Z', 'X', 'x'):
            return {'state': 'terminal', 'reason': 'owner_process_terminal'}
        return {'state': 'live', 'process_state': state}
    except (OSError, ValueError, TypeError, AttributeError, IndexError):
        return {'state': 'unverifiable', 'reason': 'owner_identity_unreadable'}


def encoded(value):
    return (json.dumps(value, sort_keys=True, allow_nan=False) + '\n').encode('utf-8')


def publish(path, data):
    """Publish immutable bytes and sync their directory entry on Linux.

    An exception after linking does not imply absence: callers must inspect the
    occupied slot, never replay input. This is not an emission/owner journal.
    """
    path = Path(path)
    fd, name = tempfile.mkstemp(prefix='.publish-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(name, path)
        # File fsync alone does not persist the new name. Failure here leaves
        # an occupied, complete slot, which must not be treated as permission
        # to publish again. Open before syncing; unsupported storage fails.
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        Path(name).unlink(missing_ok=True)


def run(run_directory, stage, decision, *, timeout=5, resume=False, compact=False):
    started = time.monotonic_ns()
    if type(stage) is not int or not 1 <= stage <= 4:
        raise ValueError('explicit stage 1..4 required')
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 <= timeout <= 30:
        raise ValueError('timeout 0..30 required')
    if type(resume) is not bool or type(compact) is not bool or not isinstance(decision, dict):
        raise ValueError('explicit decision and boolean resume required')
    root = Path(run_directory).resolve(strict=True)
    source = json.loads((root / f'source-{stage}.json').read_bytes())
    if type(decision.get('source_sequence')) is not int or decision['source_sequence'] != source['sequence']:
        raise ValueError('decision must name the presented source')
    payload = encoded(decision)
    digest = hashlib.sha256(payload).hexdigest()
    request = root / f'request-{stage}.json'
    reply = root / f'reply-{stage}.json'
    if resume:
        if request.read_bytes() != payload:
            raise ValueError('resume requires the exact committed request')
    else:
        publish(request, payload)  # Existing slot always refuses, even if equal.
    committed = time.monotonic_ns()
    deadline = time.monotonic() + timeout
    while True:
        if reply.exists():
            displayed = review_native(reply, root, compact=compact)
            report = displayed['receipt']['native_result']
            if report.get('stage') != stage or report.get('decision_sha256') != digest:
                raise ValueError('reply does not match the committed request; do not replay')
            displayed['exchange'] = {'submission_committed': True, 'resumed_read_only': resume,
                                     'started_ns': started, 'committed_ns': committed,
                                     'returned_ns': time.monotonic_ns()}
            return displayed
        owner = owner_state(root)
        if owner is not None and owner['state'] != 'live':
            return {'status': 'unknown_requires_external_reconciliation',
                    'submission_committed': True, 'resumed_read_only': resume,
                    'stage': stage, 'decision_sha256': digest, 'owner': owner,
                    'emission_status': 'unknown', 'release_status': 'unknown',
                    'started_ns': started, 'committed_ns': committed,
                    'returned_ns': time.monotonic_ns(), 'image': None, 'authority': 'none',
                    'recovery': 'Do not replay or restart this action. Independently reconcile effect and input release.'}
        if time.monotonic() >= deadline:
            return {'status': 'pending', 'submission_committed': True,
                    'resumed_read_only': resume, 'stage': stage, 'decision_sha256': digest,
                    'started_ns': started, 'committed_ns': committed,
                    'returned_ns': time.monotonic_ns(), 'image': None, 'authority': 'none',
                    'recovery': 'Resume this exact request read-only; do not submit it again.'}
        time.sleep(min(.02, max(0, deadline - time.monotonic())))
