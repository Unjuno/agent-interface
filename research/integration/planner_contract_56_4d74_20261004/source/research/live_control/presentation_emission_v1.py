"""Record local client output; never infer downstream delivery or model usage."""
import hashlib
import json
import os
import time
import uuid
from pathlib import Path


def emit(value, stream, directory):
    """Write UTF-8 JSON plus newline to a binary stream, retaining every attempt.

    A successful flush is only a local stream boundary. The caller/tool may
    transform, truncate or reject these bytes before any model receives them.
    """
    root = Path(directory)
    root.mkdir(exist_ok=False, parents=True)
    record = dict(format='presentation-emission-v1', attempt_id=uuid.uuid4().hex,
                  pid=os.getpid(), clock=dict(name='perf_counter_ns',
                  domain='this process only; cross-process alignment unverified'),
                  status='preparing', accepted_bytes=0,
                  model_received_ns=None, model_input_tokens=None,
                  model_id=None, model_cost=None,
                  downstream_measurement='not recorded',
                  scope='local binary stream write and flush, not model receipt')
    record['serialization_started_ns'] = time.perf_counter_ns()
    try:
        payload = (json.dumps(value, ensure_ascii=False, allow_nan=False,
                              separators=(',', ':')) + '\n').encode('utf-8')
        record['serialization_finished_ns'] = time.perf_counter_ns()
        record['payload_bytes'] = len(payload)
        record['payload_sha256'] = hashlib.sha256(payload).hexdigest()
        (root / 'payload.bin').write_bytes(payload)
        record['write_started_ns'] = time.perf_counter_ns()
        while record['accepted_bytes'] < len(payload):
            remaining = payload[record['accepted_bytes']:]
            count = stream.write(remaining)
            if type(count) is not int or not 0 < count <= len(remaining):
                raise OSError('stream did not report valid forward progress')
            record['accepted_bytes'] += count
        record['write_finished_ns'] = time.perf_counter_ns()
        stream.flush()
        record['flush_finished_ns'] = time.perf_counter_ns()
        record['status'] = 'locally_flushed'
    except Exception as exc:
        record['status'] = 'failed'
        record['error_type'] = type(exc).__name__
        record['error'] = str(exc)
        raise
    finally:
        record['attempt_finished_ns'] = time.perf_counter_ns()
        (root / 'receipt.json').write_text(json.dumps(record, indent=2) + '\n',
                                           encoding='utf-8')
    return record


if __name__ == '__main__':
    import sys
    source, destination = sys.argv[1:]
    emit(json.loads(Path(source).read_text(encoding='utf-8')), sys.stdout.buffer,
         destination)
