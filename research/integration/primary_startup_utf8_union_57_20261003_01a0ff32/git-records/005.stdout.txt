"""Linux exclusive JSON publication for caller-authored file exchanges.

Publication mechanism promoted unchanged from native_exchange_v1. No model,
input, request retry, source authority or semantic decision is supplied here.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

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


def publish_json(path, value):
    """Publish complete finite JSON once; any failure requires reconciliation."""
    if sys.platform != 'linux':
        raise ValueError('exclusive host JSON publication currently requires Linux')
    path = Path(path).absolute()
    data = encoded(value)
    publish(path, data)
    return {'schema': 'agent-interface/host-json-publication-v1',
            'status': 'published', 'path': str(path), 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest(),
            'authority': 'none', 'input_dispatched': False}
