"""Strict ctypes binding for the unchanged #361 acquisition helper."""
from __future__ import annotations
import ctypes as C
from pathlib import Path
import time

class Native:
    def __init__(self, display: str):
        self.lib = C.CDLL(str(Path(__file__).with_name('native.so')))
        self.lib.q_init.restype=C.c_int
        self.lib.q_open.argtypes=[C.c_char_p]; self.lib.q_open.restype=C.c_void_p
        self.lib.q_close.argtypes=[C.c_void_p]; self.lib.q_close.restype=None
        self.lib.q_paint.argtypes=[C.c_void_p,C.c_int]; self.lib.q_paint.restype=C.c_int
        self.lib.q_read.argtypes=[C.c_void_p,C.POINTER(C.c_ubyte),C.c_size_t,C.POINTER(C.c_uint64)]
        self.lib.q_read.restype=C.c_int
        if self.lib.q_init()==0: raise RuntimeError('XInitThreads failed')
        self.handle=self.lib.q_open(display.encode())
        if not self.handle: raise RuntimeError('private X11 open failed')
    def paint(self, count: int) -> dict:
        first=time.monotonic_ns(); rc=self.lib.q_paint(self.handle,count); last=time.monotonic_ns()
        if rc: raise RuntimeError(f'paint failed {rc}')
        return {'requested_pixels':count,'start_ns':first,'end_ns':last,'returncode':rc}
    def capture(self) -> tuple[bytes,dict]:
        data=(C.c_ubyte*4096)(); clocks=(C.c_uint64*6)()
        before=time.monotonic_ns(); rc=self.lib.q_read(self.handle,data,4096,clocks); after=time.monotonic_ns()
        if rc: raise RuntimeError(f'capture ABI or request failed {rc}')
        return bytes(data),{'before_py_ns':before,'native':list(clocks),'after_py_ns':after,'returncode':rc}
    def close(self) -> None:
        if self.handle: self.lib.q_close(self.handle); self.handle=None
