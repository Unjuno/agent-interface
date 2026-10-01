"""Finite fixture processes over private files; never a production producer."""
import hashlib
import json
import os
from pathlib import Path
import sys

from candidate import read_epoch_bound
from upstream.reader import read_pending
from upstream.delivery_ledger_v2 import DeliveryLedger


def emit(value):
    print(json.dumps(value, sort_keys=True, separators=(',', ':')), flush=True)


def producer():
    ledger = DeliveryLedger()
    config = json.loads(sys.stdin.readline())
    path = Path(config['path'])
    emit({'event': 'ready', 'pid': os.getpid(), 'epoch': config['epoch']})
    for line in sys.stdin:
        request = json.loads(line)
        if request['op'] == 'stop':
            emit({'event': 'stopped', 'pid': os.getpid()})
            return
        prepared = []
        for value in request['values']:
            item = {'event': 'observation', 'payload': {'value': value}}
            if config['protocol'] == 'IN_BAND_EPOCH':
                item['producer_epoch'] = config['epoch']
            prepared.append(ledger.prepare(item))
        emitted = prepared[request.get('skip', 0):]
        data = b''.join((json.dumps(x, sort_keys=True, separators=(',', ':'))
                         + '\n').encode() for x in emitted)
        mode = request['op']
        if mode == 'replace':
            temporary = path.with_name('replacement-' + str(os.getpid()))
            with temporary.open('xb') as file:
                file.write(data)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary, path)
        elif mode in ('create', 'append'):
            with path.open('xb' if mode == 'create' else 'ab') as file:
                file.write(data)
                file.flush()
                os.fsync(file.fileno())
        else:
            raise ValueError('INVALID_PRODUCER_OPERATION')
        emit({'event': 'published', 'pid': os.getpid(), 'epoch': config['epoch'],
              'prepared': prepared, 'emitted': emitted, 'written_utf8': data.decode(),
              'file_sha256': hashlib.sha256(path.read_bytes()).hexdigest()})


def reader():
    request = json.loads(sys.stdin.read())
    function = read_epoch_bound if request['protocol'] == 'IN_BAND_EPOCH' else read_pending
    try:
        result = {'status': 'OK', 'receipt': function(
            request['path'], stream_id=request['stream_id'],
            cursor=request['cursor'], max_records=request['max_records'])}
    except ValueError as error:
        result = {'status': 'REJECT', 'reason': str(error), 'authority': 'none',
                  'acknowledged': False, 'input_dispatched': False}
    emit({'pid': os.getpid(), 'result': result})


if __name__ == '__main__':
    if sys.argv[1:] == ['produce']:
        producer()
    elif sys.argv[1:] == ['read']:
        reader()
    else:
        raise SystemExit('expected produce or read')
