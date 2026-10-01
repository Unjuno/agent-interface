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


def encoded(value):
    return (json.dumps(value, sort_keys=True, allow_nan=False) + '\n').encode('utf-8')


def publish(path, data):
    """Publish complete bytes without replacing an existing request/reply."""
    path = Path(path)
    fd, name = tempfile.mkstemp(prefix='.publish-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(name, path)
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
        if time.monotonic() >= deadline:
            return {'status': 'pending', 'submission_committed': True,
                    'resumed_read_only': resume, 'stage': stage, 'decision_sha256': digest,
                    'started_ns': started, 'committed_ns': committed,
                    'returned_ns': time.monotonic_ns(), 'image': None, 'authority': 'none',
                    'recovery': 'Resume this exact request read-only; do not submit it again.'}
        time.sleep(min(.02, max(0, deadline - time.monotonic())))
