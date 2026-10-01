"""Bounded local framing and append-only research journals (stdlib only)."""
import json, os, socket, struct, time
from pathlib import Path


def encoded(obj):
    return (json.dumps(obj, sort_keys=True, separators=(',', ':')) + '\n').encode()


def exact(sock, n):
    data = bytearray()
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise EOFError('incomplete local frame')
        data.extend(chunk)
    return bytes(data)


def receive(sock):
    n = struct.unpack('!I', exact(sock, 4))[0]
    if n > 65536:
        raise ValueError('oversize local metadata frame')
    return json.loads(exact(sock, n))


def send(sock, obj):
    data = encoded(obj)
    sock.sendall(struct.pack('!I', len(data)) + data)


def connect(path):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(3)
    sock.connect(path)
    return sock


def call(path, req):
    with connect(path) as sock:
        send(sock, req)
        return receive(sock)


class Journal:
    def __init__(self, path):
        self.file = Path(path).open('xb')
        self.seq = 0

    def add(self, kind, **fields):
        obj = dict(seq=self.seq, ns=time.monotonic_ns(), pid=os.getpid(), kind=kind, **fields)
        self.seq += 1
        self.file.write(encoded(obj))
        self.file.flush()

    def close(self):
        self.file.close()
