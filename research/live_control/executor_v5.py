"""Research-only single-owner execution with a separate cancellation channel."""
import threading
import time
import copy


from lease import Expired
from lease_cause_v2 import Lease


from executor_v3 import Cancelled, DecisionRequired


class Executor:
    def __init__(self,backend,emit):
        self.backend,self.emit=backend,emit
        self.lock=threading.RLock()
        self.active=None
        self.used_ids=set()
        self.closed=False

    def submit(self,identifier,steps,expected_sequence,valid_until_ns):
        with self.lock:
            if self.closed or self.active is not None:
                raise ValueError('closed or busy; no implicit queue')
            if type(expected_sequence) is not int or expected_sequence!=self.backend.sequence:
                raise ValueError('latest observation sequence required before input')
            if not isinstance(identifier,str) or not identifier or identifier in self.used_ids:
                raise ValueError('new nonempty id required')
            lease=Lease(valid_until_ns)
            lease.check()
            steps=copy.deepcopy(steps)
            self.backend.validate(steps)  # snapshot entire program before any input
            lease.check()
            cancel=lease
            self.backend.lease=lease
            thread=threading.Thread(target=self._run,args=(identifier,steps,cancel),daemon=False)
            self.active=(identifier,cancel,thread)
            self.used_ids.add(identifier)
            self.emit(dict(event='accepted',id=identifier,steps=len(steps),valid_until_ns=valid_until_ns,accepted_ns=time.perf_counter_ns()))
            thread.start()

    def cancel(self,identifier):
        with self.lock:
            matched=self.active is not None and self.active[0]==identifier
            if matched: self.active[1].set()
            self.emit(dict(event='cancel_requested',id=identifier,matched=matched,
                           requested_ns=time.perf_counter_ns()))
            return matched

    def _run(self,identifier,steps,cancel):
        status='completed'; error=None; completed=0; decision_reason=None
        try:
            for index,step in enumerate(steps):
                if cancel.is_set(): raise Cancelled()
                self.emit(dict(event='step_started',id=identifier,step=index,operation=step['op'],
                               issued_ns=time.perf_counter_ns()))
                self.backend.execute(step,cancel,identifier,index)
                if cancel.is_set(): raise Cancelled()
                completed+=1
                self.emit(dict(event='step_completed',id=identifier,step=index,
                               completed_ns=time.perf_counter_ns()))
        except Expired:
            status='expired'
        except DecisionRequired as exc:
            status='needs_decision'; decision_reason=str(exc) or None
        except Cancelled:
            status='cancelled'
        except Exception as exc:
            status='failed'; error=repr(exc)
        finally:
            try:
                release=self.backend.release_all()
                if release.get('verified') is not True:
                    status='failed';error='input release not verified'
            except Exception as exc:
                release=dict(verified=False,error=repr(exc)); status='failed'
            if status == 'completed':
                try:
                    if cancel.is_set(): raise Cancelled()
                except Expired:
                    status = 'expired'
                except DecisionRequired as exc:
                    status = 'needs_decision'; decision_reason = str(exc) or None
                except Cancelled:
                    status = 'cancelled'
            with self.lock:
                self.emit(dict(event='terminal',id=identifier,status=status,error=error,
                               steps_completed=completed,release=release,
                               interruption=cancel.interruption_snapshot(),decision_reason=decision_reason,
                               terminal_ns=time.perf_counter_ns(),
                               semantic_completion='program status only; task scoring is separate'))
                self.active=None

    def close(self):
        with self.lock:
            self.closed=True
            job=self.active
            if job is not None: job[1].set()
        if job is not None: job[2].join()
