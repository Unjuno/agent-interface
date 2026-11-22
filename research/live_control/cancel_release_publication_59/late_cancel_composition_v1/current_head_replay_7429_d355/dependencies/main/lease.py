"""Cooperative lease in the runtime's perf_counter_ns clock domain."""
import threading,time


class Expired(Exception):
    def __init__(self):super().__init__('intent validity expired')


class Lease:
    def __init__(self,deadline,clock=time.perf_counter_ns):
        if type(deadline) is not int:raise ValueError('integer runtime-clock deadline required')
        self.deadline=deadline;self.clock=clock;self.cancel=threading.Event()
        if deadline-clock()>30_000_000_000:raise ValueError('deadline exceeds 30 second admission horizon')
    def check(self):
        if self.clock()>=self.deadline:raise Expired()
    def set(self):self.cancel.set()
    def is_set(self):
        self.check();return self.cancel.is_set()
    def wait(self,timeout):
        self.check()
        result=self.cancel.wait(min(timeout,max(0,(self.deadline-self.clock())/1e9)))
        self.check();return result
