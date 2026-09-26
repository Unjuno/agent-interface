"""Research adapter: preserved bytes are historical transport data, not authority."""
import ctypes as C
from pathlib import Path
import time

class Receiver:
    def __init__(self, sock):
        self.sock = sock
        self.lib = C.CDLL(str(Path(__file__).resolve().parent / 'build/prefix_receive.so'))
        self.lib.read_prefix.argtypes = [C.c_int, C.POINTER(C.c_ubyte), C.c_size_t,
            C.POINTER(C.c_int), C.POINTER(C.c_uint64), C.POINTER(C.c_uint64),
            C.POINTER(C.c_int), C.POINTER(C.c_uint64)]
        self.lib.read_prefix.restype = C.c_int
        self.buf = (C.c_ubyte*(64*8192))()
        self.lens = (C.c_int*64)()
        self.times = (C.c_uint64*64)()
        self.clocks = (C.c_uint64*2)()
    def read(self):
        err, size = C.c_int(), C.c_uint64()
        before = time.monotonic_ns()
        n = self.lib.read_prefix(self.sock.fileno(), self.buf, len(self.buf),
            self.lens, self.times, self.clocks, C.byref(err), C.byref(size))
        after = time.monotonic_ns()
        if n < 0:
            raise OSError(-n, 'native argument failure')
        if n > 64:
            raise RuntimeError('native count invalid')
        packets = [(C.string_at(C.addressof(self.buf)+i*8192, self.lens[i]),
                    self.times[i]) for i in range(n)]
        return packets, {'before_py_ns': before, 'after_py_ns': after,
            'native_clocks': list(self.clocks), 'count': n,
            'dequeued_ns': list(self.times[:n]), 'fault_errno': err.value,
            'rejected_size': size.value, 'grants_input_authority': False}
