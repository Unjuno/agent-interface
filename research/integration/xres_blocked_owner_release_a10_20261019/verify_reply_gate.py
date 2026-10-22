import importlib.util
from pathlib import Path
import socket
import threading
import time

source = Path('research/integration/xres_blocked_owner_release_a10_20261019/probe.py')
spec = importlib.util.spec_from_file_location('xres_a10_probe', source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
proxy = object.__new__(module.UnixReplyProxy)
proxy.allow_replies = threading.Event()
proxy.allow_replies.set()
proxy.reply_gate_lock = threading.Lock()
proxy.closed = threading.Event()
proxy.errors = []
proxy.byte_counts = {'owner_to_server': 0, 'server_to_owner': 0}
proxy.lock = threading.Lock()
proxy.withheld_server_to_owner_bytes = 0
owner_side, owner_reader = socket.socketpair()
server_side, server_writer = socket.socketpair()
proxy.client, proxy.upstream = owner_side, server_side
owner_reader.settimeout(0.15)

class TrackingRecvSocket:
    def __init__(self, wrapped, entered):
        self.wrapped = wrapped
        self.entered = entered

    def recv(self, size):
        self.entered.set()
        return self.wrapped.recv(size)


recv_entered = threading.Event()
worker = threading.Thread(target=proxy._pump, args=(
    TrackingRecvSocket(server_side, recv_entered), owner_side,
    'server_to_owner'))
worker.start()
assert recv_entered.wait(1), 'relay did not enter recv before gate closure'
proxy.block_replies()
server_writer.sendall(b'held-reply')
try:
    received_early = owner_reader.recv(64)
except socket.timeout:
    received_early = b''
assert received_early == b'', f'reply leaked while gate was closed: {received_early!r}'
proxy.allow_replies.set()
received = owner_reader.recv(64)
assert received == b'held-reply', received
server_writer.close()
worker.join(timeout=1)
assert not worker.is_alive()
assert proxy.withheld_server_to_owner_bytes == len(received)
assert proxy.byte_counts['server_to_owner'] == len(received)
owner_reader.close()
print('PASS_GATE_CLOSED_AFTER_RECV_AND_RELEASED_BYTES_VERIFIED')
