"""Defer door-operation evidence checks until the executor is idle.

This journal is not an input authority. It records failures without raising
from the executor's event callback, allowing its cleanup to finish.
"""
from copy import deepcopy
import threading


class DoorEventJournal:
    def __init__(self, max_events=10000):
        if type(max_events) is not int or max_events<1:
            raise ValueError('invalid journal limit')
        self._lock=threading.RLock()
        self._events=[]
        self._done=set()
        self._completed={}
        self._failure=None
        self._max_events=max_events
        self._expected=None
        self._deadline=None

    @property
    def ready(self):
        with self._lock:
            return self._failure is None and self._expected is None

    @property
    def failure(self):
        with self._lock:
            return self._failure

    def fail(self, reason):
        with self._lock:
            if self._failure is None:
                self._failure=str(reason)

    def completion(self, identifier):
        with self._lock:
            if self._failure is not None or identifier not in self._completed:
                raise ValueError('completion unavailable')
            return deepcopy(self._completed[identifier])

    def latest_observation(self, identifier):
        with self._lock:
            if self._failure is not None or identifier not in self._completed:
                raise ValueError('completed observation unavailable')
            observations=[event for event in self._events
                          if event.get('id')==identifier and event.get('event')=='observation']
            if not observations:
                raise ValueError('completed operation has no observation')
            return deepcopy(observations[-1])

    def begin(self, identifier, deadline_ns):
        with self._lock:
            if (self._failure is not None or self._expected is not None
                    or type(identifier) is not str or not identifier or identifier in self._done
                    or type(deadline_ns) is not int or deadline_ns<=0):
                raise ValueError('cannot begin operation')
            self._expected=identifier
            self._deadline=deadline_ns

    def record(self, event):
        with self._lock:
            if self._failure is not None:
                return
            try:
                if type(event) is not dict or len(self._events)>=self._max_events:
                    self._failure='invalid event or journal overflow'
                    return
                identifier=event.get('id')
                if identifier in self._done:
                    self._failure='event published after completion'
                    return
                if event.get('event')=='input_release_unverified':
                    self._failure='input release is unverified'
                    return
                if (event.get('event') in ('accepted','terminal','input_admission',
                                           'input_release_transition','input_released','pointer_admission','keys_held')
                        and (self._expected is None or identifier!=self._expected)):
                    self._failure='unexpected operation event'
                    return
                self._events.append(deepcopy(event))
            except Exception:
                self._failure='event could not be recorded'

    def complete_if_idle(self, identifier, contract, executor, clock):
        # Never block behind terminal publication. The event callback runs
        # with executor.lock held and may itself be delayed by a sink.
        def precheck():
            if self._failure is not None:
                return 'HOLD'
            if (type(identifier) is not str or not identifier or identifier!=self._expected
                    or not callable(clock)):
                self._failure='invalid completion identifier or clock'
                return 'HOLD'
            try:
                now=clock()
            except Exception:
                self._failure='completion clock unavailable'
                return 'HOLD'
            if type(now) is not int or now>=self._deadline:
                self._failure='operation completion deadline expired'
                return 'HOLD'
            return None
        with self._lock:
            status=precheck()
            if status:
                return status
        if not executor.lock.acquire(blocking=False):
            with self._lock:
                return precheck() or 'WAIT'
        try:
            with self._lock:
                status=precheck()
                if status:
                    return status
                if any(identifier in getattr(executor,name,{}) for name in
                       ('admission_publication_errors','terminal_publication_errors','release_publication_errors')):
                    self._failure='publication outcome unknown'
                    return 'HOLD'
                if executor.active is not None:
                    return 'WAIT'
                relevant=[e for e in self._events if e.get('id')==identifier]
                accepted=[e for e in relevant if e.get('event')=='accepted']
                terminal=[e for e in relevant if e.get('event')=='terminal']
                if len(accepted)!=1 or len(terminal)!=1:
                    self._failure='missing or ambiguous accepted or terminal evidence'
                    return 'HOLD'
                publication=terminal[0].get('input_release_publication')
                if type(publication) is dict and publication.get('status')=='delivery_unknown':
                    self._failure='release publication outcome unknown'
                    return 'HOLD'
                try:
                    contract.completed(identifier,terminal[0],accepted[0],relevant)
                except Exception:
                    self._failure='operation evidence rejected'
                    return 'HOLD'
                status=precheck()
                if status:
                    return status
                self._completed[identifier]=(deepcopy(accepted[0]),deepcopy(terminal[0]))
                self._done.add(identifier)
                self._expected=None
                self._deadline=None
                return 'DONE'
        finally:
            executor.lock.release()
