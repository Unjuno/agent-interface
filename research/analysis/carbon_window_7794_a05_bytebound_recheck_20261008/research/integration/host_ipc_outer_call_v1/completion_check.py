"""Passive integration gate for a cooperative, quiescent local publication.

No subprocess, input, request publication, or retry is available in this module.
The envelope is a NEW supervisor contract, not emitted by the upstream broker.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

LIMIT_BYTES = 131072


def strict(raw: bytes):
    if len(raw) > LIMIT_BYTES:
        raise ValueError('OVERSIZED')
    def pairs(items):
        out = {}
        for k, v in items:
            if k in out:
                raise ValueError('DUPLICATE_KEY')
            out[k] = v
        return out
    def invalid(v):
        raise ValueError('NONFINITE')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def decide(files: dict[str, bytes], envelope: dict) -> str:
    """Return a refusal reason or VERIFIED. Operates only on passed byte values."""
    try:
        if type(envelope) is not dict or set(envelope) != {
            'version', 'authority_granted', 'client_exit', 'broker_exit', 'sha256'
        }:
            return 'ENVELOPE_SCHEMA'
        if type(envelope['version']) is not int or envelope['version'] != 1:
            return 'ENVELOPE_VERSION'
        if envelope['authority_granted'] is not False:
            return 'ENVELOPE_AUTHORITY'
        for key in ('client_exit', 'broker_exit'):
            if type(envelope[key]) is not int or envelope[key] != 0:
                return key.upper() + '_NOT_ZERO'
        names = {'request', 'published_request', 'response', 'receipt', 'process'}
        if set(files) != names or set(envelope['sha256']) != names:
            return 'ARTIFACT_SET'
        for key, raw in files.items():
            if type(raw) is not bytes or len(raw) > LIMIT_BYTES:
                return 'ARTIFACT_TYPE_OR_LIMIT'
            if hashlib.sha256(raw).hexdigest() != envelope['sha256'][key]:
                return 'ARTIFACT_HASH'
        if files['request'] != files['published_request']:
            return 'REQUEST_BYTES'
        req = strict(files['request']); rec = strict(files['receipt'])
        proc = strict(files['process'])
        rid = req.get('request_id')
        if (type(rid) is not str or len(rid) != 32
                or any(c not in '0123456789abcdef' for c in rid)):
            return 'REQUEST_ID'
        if rec.get('request_id') != rid or proc.get('request_id') != rid:
            return 'RECEIPT_ID'
        if any(x.get('authority_granted') is not False for x in (req, rec, proc)):
            return 'AUTHORITY'
        if rec.get('boundary') != 'host-local-codex-exe' or proc.get('boundary') != 'container-to-host-model-ipc':
            return 'BOUNDARY'
        if type(rec.get('returncode')) is not int or rec['returncode'] != 0:
            return 'CHILD_NOT_ZERO'
        if type(proc.get('exit_code')) is not int or proc['exit_code'] != 0:
            return 'PROCESS_NOT_ZERO'
        if rec.get('error_class') is not None or rec.get('stop_reason') is not None:
            return 'BROKER_FAILURE'
        for x in (rec, proc):
            if any(type(x.get(k)) is not int or x[k] < 0 for k in ('started_ns', 'exited_ns')):
                return 'CLOCK_TYPE'
            if x['exited_ns'] < x['started_ns']:
                return 'CLOCK_ORDER'
        # Each clock interval is checked within its own process only.
        if not files['response'].endswith(b'\n'):
            return 'RESPONSE_FRAMING'
        rows = [strict(line) for line in files['response'].splitlines() if line.strip()]
        if any(type(r) is not dict for r in rows):
            return 'EVENT_OBJECT'
        if [r.get('type') for r in rows] != ['thread.started', 'item.completed', 'turn.completed']:
            return 'EVENT_SEQUENCE'
        if type(rows[0].get('thread_id')) is not str or not rows[0]['thread_id']:
            return 'THREAD'
        item = rows[1].get('item')
        if type(item) is not dict or item.get('type') != 'agent_message' or type(item.get('text')) is not str:
            return 'MESSAGE'
        usage = rows[2].get('usage')
        if (type(usage) is not dict or set(usage) != {'input_tokens','output_tokens','cached_input_tokens'}
                or any(type(v) is not int or v < 0 for v in usage.values())
                or usage['cached_input_tokens'] > usage['input_tokens']):
            return 'USAGE'
        return 'VERIFIED'
    except (ValueError, KeyError, TypeError, AttributeError, UnicodeError):
        return 'MALFORMED'


def require_completion(root: Path) -> None:
    """Check before the original schema/semantic parsers can emit result.json.

    This finite adapter assumes no writer after supervisor completion. It is not
    an atomic multi-file snapshot, authentication, or a production collector.
    """
    root = Path(root)
    reason = 'MISSING_COMPLETION'
    try:
        envelope = strict((root / 'completion.json').read_bytes())
        request = (root / 'runner/plan.json').read_bytes()
        rid = strict(request)['request_id']
        if type(rid) is not str or len(rid) != 32 or any(c not in '0123456789abcdef' for c in rid):
            raise ValueError('REQUEST_ID')
        files = {
            'request': request,
            'published_request': (root / 'ipc' / (rid + '.request.json')).read_bytes(),
            'response': (root / 'runner/events.jsonl').read_bytes(),
            'receipt': (root / 'ipc' / (rid + '.broker.json')).read_bytes(),
            'process': (root / 'runner/process.json').read_bytes(),
        }
        reason = decide(files, envelope)
    except (OSError, KeyError, ValueError, TypeError):
        pass
    (root / 'completion-validation.json').write_text(json.dumps({
        'reason': reason, 'accepted': reason == 'VERIFIED',
        'authority_granted': False, 'dispatches': 0,
    }, sort_keys=True) + '\n', encoding='utf-8')
    if reason != 'VERIFIED':
        raise RuntimeError('STOP_JOINED_COMPLETION:' + reason)
