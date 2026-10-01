"""Python-level consumption clocks are retained after every native handoff."""
import ctypes as C
from pathlib import Path
import time

class Receiver:
    def __init__(self,sock,batched):
        self.sock=sock;self.batched=batched
        if batched:
            self.lib=C.CDLL(str(Path(__file__).resolve().parent/'build'/'receive_batch.so'))
            self.lib.read_batch.argtypes=[C.c_int,C.POINTER(C.c_ubyte),C.c_size_t,C.POINTER(C.c_int),C.POINTER(C.c_uint64),C.POINTER(C.c_uint64)]
            self.lib.read_batch.restype=C.c_int
            self.buf=(C.c_ubyte*(64*8192))();self.lens=(C.c_int*64)();self.times=(C.c_uint64*64)();self.clocks=(C.c_uint64*2)()
    def read(self):
        before=time.monotonic_ns()
        if not self.batched:
            packet=self.sock.recv(8192);after=time.monotonic_ns()
            return [(packet,None)],{'before_py_ns':before,'after_py_ns':after,'native_clocks':None,'count':1,'dequeued_ns':[None]}
        n=self.lib.read_batch(self.sock.fileno(),self.buf,len(self.buf),self.lens,self.times,self.clocks)
        after=time.monotonic_ns()
        if n<0:raise OSError(-n,'native read_batch failed')
        if not 0<=n<=64:raise RuntimeError('native batch size invalid')
        packets=[(C.string_at(C.addressof(self.buf)+i*8192,self.lens[i]),self.times[i]) for i in range(n)]
        return packets,{'before_py_ns':before,'after_py_ns':after,'native_clocks':list(self.clocks),
                        'count':n,'dequeued_ns':list(self.times[:n])}
