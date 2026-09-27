"""Finite private-file reader worker; no GUI, input, network, ACK or action."""
from __future__ import annotations
import base64
import json
import os
from pathlib import Path
import resource
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'vendor'))
from reader import read_pending


def emit(value):
    sys.stdout.write(json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n')
    sys.stdout.flush()


def stat_fd(fd):
    st = os.fstat(fd)
    return dict(dev=st.st_dev, ino=st.st_ino, size=st.st_size, nlink=st.st_nlink)


def main():
    inherited, size = int(sys.argv[1]), int(sys.argv[2])
    policy, epoch, snapshot = sys.argv[3], sys.argv[4], Path(sys.argv[5])
    if policy not in ('UNCHECKED_DUP', 'CHECKED_DUP', 'PREAD') or not 0 < size < 4096:
        raise ValueError('bad fixed worker configuration')
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2, 256 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
    inherited_count = len(os.listdir('/proc/self/fd'))
    fd = os.dup(inherited)
    os.close(inherited)
    data = b''
    emit(dict(op='ready', pid=os.getpid(), inherited=inherited, duplicate=fd,
              fd_count=inherited_count, stat=stat_fd(fd)))
    try:
        for line in sys.stdin:
            cmd = json.loads(line)
            before = os.lseek(fd, 0, os.SEEK_CUR)
            if cmd == {'op': 'reset'}:
                os.lseek(fd, 0, os.SEEK_SET)
                emit(dict(op='reset', before=before, after=os.lseek(fd, 0, os.SEEK_CUR)))
            elif set(cmd) == {'op', 'n'} and cmd['op'] == 'read':
                n = cmd['n']
                if type(n) is not int or not 0 < n <= size:
                    raise ValueError('invalid read extent')
                logical_offset = len(data)
                part = os.pread(fd, n, logical_offset) if policy == 'PREAD' else os.read(fd, n)
                data += part
                emit(dict(op='read', before=before, after=os.lseek(fd, 0, os.SEEK_CUR),
                          logical_offset=logical_offset, n=n, data_b64=base64.b64encode(part).decode()))
            elif cmd == {'op': 'finish'}:
                with snapshot.open('xb') as out:
                    out.write(data)
                os.chmod(snapshot, 0o444)
                response = None
                status = 'REFUSED_INCOMPLETE_ACQUISITION'
                if policy == 'UNCHECKED_DUP' or len(data) == size:
                    response = read_pending(snapshot, stream_id=epoch, max_records=32, max_bytes=4096)
                    status = 'DELIVERED'
                retained = stat_fd(fd)
                os.close(fd)
                fd = None
                emit(dict(op='finish', status=status, receipt=response,
                          data_b64=base64.b64encode(data).decode(), size=len(data),
                          stat=retained, fd_count_after=len(os.listdir('/proc/self/fd')),
                          authority='none', acknowledged=False, input_dispatched=False))
                return 0
            else:
                raise ValueError('unknown worker command')
        raise RuntimeError('missing finish command')
    finally:
        if fd is not None:
            os.close(fd)


if __name__ == '__main__':
    raise SystemExit(main())
