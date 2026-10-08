"""ctypes acquisition adapter; policy source is inherited byte-for-byte."""
from __future__ import annotations
import ctypes as C
from pathlib import Path
import time
from predecessor_policy import classify
class Event(C.Structure):
    _fields_=[(k,C.c_uint64) for k in ('ordinal','window','server_ms','dequeued_ns')]+[(k,C.c_int) for k in ('type','send_event','keycode','mode','detail')]+[('keymap',C.c_ubyte*32)]
class Sample(C.Structure):
    _fields_=[(k,C.c_uint64) for k in ('t0','t1','r0','r1','p0','p1')]+[(k,C.c_int) for k in ('count','queries','syncs','errors')]+[('keymap',C.c_ubyte*32),('events',Event*96)]

def load():
    l=C.CDLL(str(Path(__file__).with_name('key_state_native.so')))
    l.ks_open.argtypes=[C.c_ulong,C.c_int];l.ks_open.restype=C.c_void_p
    l.ks_observe.argtypes=[C.c_void_p,C.c_int,C.POINTER(Sample)];l.ks_observe.restype=C.c_int
    l.ks_close.argtypes=[C.c_void_p];l.ks_close.restype=C.c_int
    l.ks_sample_size.restype=C.c_size_t;l.ks_event_size.restype=C.c_size_t
    if l.ks_sample_size()!=C.sizeof(Sample) or l.ks_event_size()!=C.sizeof(Event):raise RuntimeError('native ABI mismatch')
    return l

class Reader:
    def __init__(self,lib,window:int,code:int,seed:str,subscribed:bool,epoch:str):
        self.lib=lib;self.window=window;self.code=code;self.seed=seed;self.epoch=epoch
        self.ptr=lib.ks_open(window,int(subscribed))
        if not self.ptr:raise RuntimeError('observer setup failed')
        self.history=[];self.first=0;self.s=Sample()
    def bootstrap(self):
        # Separate excluded setup: clear pre-seed event queue, not a timed sample.
        r=self.observe('EVENT_SYNC');self.first+=len(self.history);self.history=[];return r
    def observe(self,mode:str):
        op={'QUERY':0,'EVENT_SYNC':1,'LOCAL_ONLY':2}[mode]
        a=time.perf_counter_ns();cpu0=time.process_time_ns()
        rc=self.lib.ks_observe(self.ptr,op,C.byref(self.s))
        if rc:raise RuntimeError('native acquisition error '+str(rc))
        s=self.s;events=[]
        for v in s.events[:s.count]:
            e=dict(ordinal=v.ordinal,type=v.type,send_event=bool(v.send_event),dequeued_ns=v.dequeued_ns)
            if v.type==11:e['keymap']=bytes(v.keymap).hex()
            elif v.type in (9,10):e.update(window=v.window,mode=v.mode,detail=v.detail)
            else:e.update(window=v.window,keycode=v.keycode,server_time_ms=v.server_ms)
            events.append(e)
        if op==0:
            m=bytes(s.keymap);down=bool(m[self.code//8]&(1<<(self.code%8)))
            decision=dict(status='WAIT' if down else 'TYPE',shift_down=down,authority='none',input_dispatched=False)
        else:
            self.history.extend(events)
            p=dict(epoch=self.epoch,expected_epoch=self.epoch,window=self.window,keycode=self.code,seed_keymap=self.seed,seed_focused=True,first_ordinal=self.first,events=self.history,coverage_complete=True)
            decision=classify(p,'FOCUS_KEYMAP')
        cpu1=time.process_time_ns();b=time.perf_counter_ns()
        # Journal conversion/serialization, construction and scoring are outside full timing.
        return dict(mode=mode,wall_before_ns=a,wall_after_ns=b,cpu_before_ns=cpu0,cpu_after_ns=cpu1,
            native_before_ns=s.t0,native_after_ns=s.t1,next_before=s.r0,next_after=s.r1,
            processed_before=s.p0,processed_after=s.p1,query_calls=s.queries,sync_calls=s.syncs,
            native_errors=s.errors,keymap=bytes(s.keymap).hex() if op==0 else None,events=events,
            history_count=len(self.history),decision=decision)
    def close(self):
        if self.ptr:
            rc=self.lib.ks_close(self.ptr);self.ptr=None
            if rc:raise RuntimeError('observer close error')
