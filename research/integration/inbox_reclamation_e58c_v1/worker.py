"""Finite private publisher/reader workers; never a production or network service."""
from __future__ import annotations
import base64
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'vendor'))
from delivery_ledger_v2 import DeliveryLedger
from reader import read_pending


def deny_network(event, args):
    if event.startswith('socket.'):
        raise RuntimeError('NETWORK_NOT_PERMITTED_IN_STUDY')


sys.addaudithook(deny_network)


def emit(**message):
    message['pid'] = os.getpid()
    print(json.dumps(message, sort_keys=True, separators=(',', ':')), flush=True)


def command():
    line = sys.stdin.buffer.readline(65537)
    if not line.endswith(b'\n') or len(line) > 65536:
        raise ValueError('INVALID_COMMAND_FRAME')
    obj = json.loads(line)
    if not isinstance(obj, dict):
        raise ValueError('INVALID_COMMAND')
    return obj


def encode(obj):
    return (json.dumps(obj, sort_keys=True, separators=(',', ':')) + '\n').encode()


def write_generation(path, epoch, tail):
    path.mkdir(exist_ok=False)
    ledger = DeliveryLedger()
    rows = [ledger.prepare({'event': 'notification', 'payload': val})
            for val in ('shared:1', 'shared:2', 'tail:' + tail)]
    (path / 'epoch.json').write_bytes(encode({'schema': 'fixture-epoch-v1', 'epoch': epoch}))
    (path / 'delivered.jsonl').write_bytes(b''.join(encode(row) for row in rows))


def switch(root):
    # Same-filesystem atomic name replacement. No directory contents are changed here.
    os.symlink('gen-b', root / 'NEXT')
    os.replace(root / 'NEXT', root / 'CURRENT')


def publisher(root):
    config = command()
    write_generation(root / 'gen-a', config['epoch_a'], 'A')
    write_generation(root / 'gen-b', config['epoch_b'], 'B')
    os.symlink('gen-a', root / 'CURRENT')
    emit(event='ready', generations=['gen-a', 'gen-b'])
    while True:
        cmd = command()
        if cmd['op'] == 'stop':
            emit(event='stopped')
            return
        if cmd['op'] != 'mutate':
            raise ValueError('UNEXPECTED_PUBLISHER_COMMAND')
        operation = cmd['operation']
        if operation != 'NONE':
            switch(root)
        if operation in ('UNLINK_OLD', 'RECYCLE_NAME'):
            (root / 'gen-a' / 'delivered.jsonl').unlink()
            (root / 'gen-a' / 'epoch.json').unlink()
            (root / 'gen-a').rmdir()
        if operation == 'RECYCLE_NAME':
            write_generation(root / 'gen-a', config['epoch_b'], 'B')
        if operation == 'REPLACE_FILE':
            replacement = root / 'gen-a' / 'replacement.jsonl'
            replacement.write_bytes((root / 'gen-b' / 'delivered.jsonl').read_bytes())
            os.replace(replacement, root / 'gen-a' / 'delivered.jsonl')
        if operation not in ('NONE', 'SWITCH', 'UNLINK_OLD', 'RECYCLE_NAME', 'REPLACE_FILE'):
            raise ValueError('UNKNOWN_OPERATION')
        emit(event='mutated', operation=operation, current=os.readlink(root / 'CURRENT'))


def fd_count():
    return len(list(Path('/proc/self/fd').iterdir()))


def descriptor_info(fd):
    st = os.fstat(fd)
    return {'device': st.st_dev, 'inode': st.st_ino, 'size': st.st_size, 'links': st.st_nlink}


def consumer(root):
    config = command()
    policy = config['policy']
    owned = []
    initial_fds = fd_count()
    initial_source = None
    try:
        if policy == 'RESOLVED_PATH':
            pinned = (root / 'CURRENT').resolve(strict=True)
            epoch_raw = (pinned / 'epoch.json').read_bytes()
            read_path = pinned / 'delivered.jsonl'
        else:
            dfd = os.open(root / 'CURRENT', os.O_RDONLY | os.O_DIRECTORY)
            owned.append(dfd)
            pinned = Path('/proc/self/fd') / str(dfd)
            if policy == 'STREAM_FD':
                streamfd = os.open('delivered.jsonl', os.O_RDONLY, dir_fd=dfd)
                owned.append(streamfd)
                initial_source = descriptor_info(streamfd)
                read_path = Path('/proc/self/fd') / str(streamfd)
            elif policy == 'DIRECTORY_FD':
                read_path = pinned / 'delivered.jsonl'
            else:
                raise ValueError('UNKNOWN_POLICY')
            meta_fd = os.open('epoch.json', os.O_RDONLY, dir_fd=dfd)
            with os.fdopen(meta_fd, 'rb') as meta:
                epoch_raw = meta.read(4097)
        epoch_obj = json.loads(epoch_raw)
        valid = (set(epoch_obj) == {'schema', 'epoch'} and
                 epoch_obj['schema'] == 'fixture-epoch-v1' and
                 type(epoch_obj['epoch']) is str and
                 epoch_obj['epoch'] == config['expected_epoch'])
        emit(event='prepared', epoch_b64=base64.b64encode(epoch_raw).decode(),
             epoch_valid=valid, retained_handles=len(owned), initial_source=initial_source)
        cmd = command()
        if cmd != {'op': 'read'}:
            raise ValueError('UNEXPECTED_READER_COMMAND')
        if not valid:
            outcome = {'status': 'REFUSED_EPOCH', 'receipt': None, 'observed_b64': None}
        else:
            try:
                receipt = read_pending(read_path, stream_id=config['expected_epoch'],
                                       cursor=config['cursor'], max_records=32, max_bytes=16384)
                # No writer operation is possible during this phase. The second read
                # is diagnostic byte retention, NOT a general atomic-snapshot claim.
                observed = read_path.read_bytes()
                outcome = {'status': 'DELIVERED', 'receipt': receipt,
                           'observed_b64': base64.b64encode(observed).decode()}
            except FileNotFoundError as exc:
                outcome = {'status': 'REFUSED_SOURCE_UNAVAILABLE', 'receipt': None,
                           'observed_b64': None, 'errno': exc.errno}
        if policy == 'STREAM_FD':
            outcome['retained_source_after'] = descriptor_info(streamfd)
    finally:
        for fd in reversed(owned):
            os.close(fd)
    emit(event='read_result', **outcome, fds_before=initial_fds, fds_after=fd_count())


if __name__ == '__main__':
    role, root = sys.argv[1], Path(sys.argv[2]).resolve(strict=True)
    if role == 'publisher':
        publisher(root)
    elif role == 'reader':
        consumer(root)
    else:
        raise ValueError('INVALID_ROLE')
