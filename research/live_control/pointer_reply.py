"""One pending pointer reply, bounded by image age and the original lease."""
import copy,threading,time,uuid
from executor_v3 import Cancelled,DecisionRequired

class PointerReply:
    def __init__(self):self.cv=threading.Condition();self.pending=None
    def offer(self,sequence,capture_ns,timeout_ms,lease):
        with self.cv:
            if self.pending is not None:raise ValueError('one pending reply only')
            deadline=min(lease.deadline,capture_ns+timeout_ms*1_000_000)
            if time.perf_counter_ns()>=deadline:raise DecisionRequired('observation too old for reply')
            p=dict(ticket=uuid.uuid4().hex,sequence=sequence,deadline=deadline,lease=lease,reply=None,timed_out=False)
            def expire():
                with self.cv:
                    if self.pending is p:
                        p['timed_out']=True;lease.set();self.cv.notify_all()
            timer=threading.Timer((deadline-time.perf_counter_ns())/1e9,expire);timer.daemon=True;p['timer']=timer
            self.pending=p;timer.start()
            return {'ticket':p['ticket'],'sequence':sequence,'reply_until_ns':deadline}
    def submit(self,ticket,sequence,command):
        with self.cv:
            p=self.pending
            if p is None or ticket!=p['ticket'] or type(sequence) is not int or sequence!=p['sequence']:raise ValueError('obsolete reply ticket/sequence')
            if p['reply'] is not None:raise ValueError('reply already supplied')
            if time.perf_counter_ns()>=p['deadline'] or p['lease'].cancel.is_set():raise ValueError('reply no longer valid')
            p['reply']=copy.deepcopy(command);self.cv.notify_all()
            return {'accepted':True,'executed':False}
    def wait(self,lease):
        with self.cv:
            p=self.pending
            if p is None or p['lease'] is not lease:raise ValueError('no matching reply wait')
            while True:
                lease.check()
                if p['timed_out'] or time.perf_counter_ns()>=p['deadline']:
                    lease.set();raise DecisionRequired('pointer reply timed out')
                if lease.cancel.is_set():raise Cancelled()
                if p['reply'] is not None:
                    command=p['reply'];p['timer'].cancel();self.pending=None;return command
                self.cv.wait(.01)
    def clear(self):
        with self.cv:
            if self.pending is not None:
                self.pending['timer'].cancel();self.pending=None
            self.cv.notify_all()
