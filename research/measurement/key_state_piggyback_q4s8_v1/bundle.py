"""Read-only focus plus key-state bundles; no input or expected-state access."""
import ctypes as C
import time
import native
MODES=('FOCUS_QUERY','FOCUS_SYNC','FOCUS_PIGGYBACK')
class Focus(C.Structure):
    _fields_=[(k,C.c_uint64) for k in ('t0','t1','r0','r1','p0','p1','focus')]+[(k,C.c_int) for k in ('revert','errors')]
def load():
    lib=native.load()
    lib.ks_focus.argtypes=[C.c_void_p,C.POINTER(Focus)];lib.ks_focus.restype=C.c_int
    lib.ks_focus_size.restype=C.c_size_t
    if C.sizeof(Focus)!=lib.ks_focus_size():raise RuntimeError('focus ABI mismatch')
    return lib

def focus(reader):
    s=Focus()
    rc=reader.lib.ks_focus(reader.ptr,C.byref(s))
    if rc:raise RuntimeError('focus query failure '+str(rc))
    return {k:int(getattr(s,k)) for k,_ in s._fields_}

def collect(reader,mode):
    if mode not in MODES:raise ValueError('unknown bundle')
    start=time.perf_counter_ns();cpu0=time.process_time_ns()
    f=focus(reader)
    state=reader.observe({'FOCUS_QUERY':'QUERY','FOCUS_SYNC':'EVENT_SYNC','FOCUS_PIGGYBACK':'LOCAL_ONLY'}[mode])
    cpu1=time.process_time_ns();end=time.perf_counter_ns()
    return dict(mode=mode,start_ns=start,end_ns=end,cpu0=cpu0,cpu1=cpu1,focus=f,state=state,
                authority='none',task_success=None)
