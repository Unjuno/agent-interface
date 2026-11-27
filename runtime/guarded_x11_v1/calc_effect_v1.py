"""Fail-closed verifier for one server-owned Calc call artifact."""
import hashlib
import json
import os
from pathlib import Path
import re
import stat

from .calc_profile_v1 import verify_saved_fods_bytes

ARTIFACT_NAME = 'task-artifact.fods'
CUSTODY_NAME = 'calc-artifact-custody.json'


def _identity(info):
    # On Windows, stat/lstat and fstat expose st_ctime_ns differently:
    # pathname stats report creation time while descriptor stats can report
    # last-write time. Compare the stable creation timestamp across those APIs
    # when available, retaining ctime on platforms without birthtime.
    change_or_birth_ns = getattr(info, 'st_birthtime_ns', None)
    if type(change_or_birth_ns) is not int:
        change_or_birth_ns = info.st_ctime_ns
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
            change_or_birth_ns)


def _same_stat_version(left, right):
    """Compare same-API stat samples, preserving their ctime change check."""
    return (_identity(left) == _identity(right)
            and left.st_ctime_ns == right.st_ctime_ns)


def _read_regular(path, *, max_bytes):
    path = Path(path)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > max_bytes:
        raise ValueError('not a bounded regular file')
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(path, flags)
    try:
        opened = os.fstat(fd)
        if (not stat.S_ISREG(opened.st_mode) or _identity(before) != _identity(opened)
                or opened.st_size > max_bytes):
            raise ValueError('file changed before open')
        chunks = []
        total = 0
        while True:
            chunk = os.read(fd, min(1024 * 1024, max_bytes + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > max_bytes:
                raise ValueError('file exceeds bound')
        after = os.fstat(fd)
        current = path.lstat()
        if (not _same_stat_version(opened, after)
                or not _same_stat_version(before, current)
                or _identity(after) != _identity(current)
                or total != after.st_size):
            raise ValueError('file changed while reading')
        return b''.join(chunks), _identity(after)
    finally:
        os.close(fd)


def verify_call_owned_calc_effect(call_root, *, call_id, attempt_id,
                                  close_receipt, expected_profile_id='calc-ocr-save-v1'):
    """Verify a fixed artifact only after exact call retirement and close receipt.

    A successful parse is deliberately not treated as GUI provenance. The
    custody sidecar must be minted by a future trusted Save-As controller.
    Current Calc profile runs therefore remain unknown.
    """
    unknown = {'status': 'unknown', 'task_success': None,
               'reason': 'artifact_custody_unavailable', 'replay_allowed': False}
    try:
        if (type(call_id) is not str or not re.fullmatch(r'[0-9a-f]{32}', call_id)
                or type(attempt_id) is not str or not attempt_id
                or type(expected_profile_id) is not str
                or not isinstance(close_receipt, dict)):
            return dict(unknown, reason='call_identity_invalid')
        if (close_receipt.get('status') != 'closed'
                or close_receipt.get('verified') is not True
                or close_receipt.get('owner_process_retired') is not True
                or close_receipt.get('release_confirmed') is not True):
            return dict(unknown, reason='verified_close_required')
        root = Path(call_root)
        custody_bytes, _ = _read_regular(root / CUSTODY_NAME, max_bytes=64 * 1024)
        custody = json.loads(custody_bytes.decode('utf-8'))
        required = {'schema', 'call_id', 'attempt_id', 'profile_id', 'artifact_name',
                    'artifact_sha256', 'artifact_bytes', 'artifact_identity',
                    'blank_sha256', 'save_request_id', 'close_receipt_sha256'}
        if (type(custody) is not dict or set(custody) != required
                or custody.get('schema') != 'agent-interface/calc-artifact-custody-v1'
                or custody.get('call_id') != call_id
                or custody.get('attempt_id') != attempt_id
                or custody.get('profile_id') != expected_profile_id
                or custody.get('artifact_name') != ARTIFACT_NAME):
            return dict(unknown, reason='custody_identity_mismatch')
        data, identity = _read_regular(root / ARTIFACT_NAME, max_bytes=64 * 1024 * 1024)
        digest = hashlib.sha256(data).hexdigest()
        if (custody.get('artifact_sha256') != digest
                or custody.get('artifact_bytes') != len(data)
                or custody.get('artifact_identity') != list(identity)
                or custody.get('close_receipt_sha256') != hashlib.sha256(
                    json.dumps(close_receipt, sort_keys=True,
                        separators=(',', ':')).encode('utf-8')).hexdigest()
                or type(custody.get('blank_sha256')) is not str
                or len(custody['blank_sha256']) != 64
                or type(custody.get('save_request_id')) is not str
                or not custody['save_request_id']):
            return dict(unknown, reason='custody_content_mismatch')
        # A sidecar is data, not authority. No registered Save-As controller
        # currently mints an authenticated in-memory receipt for this call, so
        # even a perfectly self-consistent caller-created sidecar cannot make
        # parsed bytes a task effect.
        return dict(unknown, reason='trusted_save_controller_unavailable')
    except FileNotFoundError:
        return dict(unknown, reason='artifact_custody_unavailable')
    except (OSError, ValueError, TypeError, UnicodeError, json.JSONDecodeError):
        return dict(unknown, reason='artifact_or_custody_unreadable')
