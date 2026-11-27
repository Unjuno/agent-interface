"""Bounded research monitor; cancellation acknowledgement is not release.

The caller owns the action, unique cancellation token, and probe custody. Probe
operations must themselves be bounded; a stuck callback leaves the worker live
and join() reports running. Never reuse a token or start a replacement action
until this worker and the action have both terminated and release is verified.
"""
import copy
import math
import threading
import time


class BoundedPatchWatch:
    def __init__(self, *, open_probe, reference, token, cancel, interval_s=.025,
                 deadline_s=2.0, max_samples=100, threshold=32.0):
        if (not callable(open_probe) or not callable(cancel) or
                type(reference) is not bytes or not reference or
                type(token) is not str or not token or len(token)>64 or
                type(max_samples) is not int or not 1<=max_samples<=10000 or
                type(interval_s) not in (int,float) or not math.isfinite(interval_s) or not 0<interval_s<=1 or
                type(deadline_s) not in (int,float) or not math.isfinite(deadline_s) or not 0<deadline_s<=60 or
                type(threshold) not in (int,float) or not math.isfinite(threshold) or not 0<=threshold<=255):
            raise ValueError('valid bounded watch configuration required')
        self.open_probe,self.reference,self.token,self.cancel=open_probe,reference,token,cancel
        self.interval_s,self.deadline_s,self.max_samples,self.threshold=interval_s,deadline_s,max_samples,threshold
        self._lock=threading.Lock();self._thread=None;self._result=None

    def start(self):
        with self._lock:
            if self._thread is not None:raise RuntimeError('watch is single use')
            self._thread=threading.Thread(target=self._run,daemon=True)
            self._thread.start()

    def join(self, timeout):
        if type(timeout) not in (int,float) or not math.isfinite(timeout) or timeout<0:
            raise ValueError('finite nonnegative join timeout required')
        with self._lock:thread=self._thread
        if thread is None:raise RuntimeError('watch has not started')
        thread.join(timeout)
        if thread.is_alive():return {'status':'running','release_verified':False}
        return copy.deepcopy(self._result)

    def _run(self):
        result={'status':'monitor_error','release_verified':False,'samples':[],'cancel':None,
                'started_ns':time.monotonic_ns()};probe=None;cancel_attempted=False
        def request():
            nonlocal cancel_attempted
            if cancel_attempted:return
            cancel_attempted=True
            result['cancel_started_ns']=time.monotonic_ns()
            try:result['cancel']=copy.deepcopy(self.cancel(self.token))
            except Exception as error:result['cancel_error_type']=type(error).__name__
            finally:result['cancel_finished_ns']=time.monotonic_ns()
        try:
            probe=self.open_probe();end=time.monotonic()+self.deadline_s;seen=False
            while time.monotonic()<end:
                held=probe.held()
                if type(held) is not bool:raise ValueError('held state must be boolean')
                if time.monotonic()>=end:
                    result['status']='budget_exhausted';request();break
                if held:
                    seen=True;start=time.monotonic_ns();data,artifact=probe.capture();finished=time.monotonic_ns()
                    if type(data) is not bytes or len(data)!=len(self.reference) or type(artifact) is not dict:
                        raise ValueError('capture must match reference and contain metadata')
                    difference=sum(abs(a-b) for a,b in zip(data,self.reference))/len(data)
                    result['samples'].append({'capture_started_ns':start,'capture_ended_ns':finished,
                                              'difference':difference,'artifact':copy.deepcopy(artifact)})
                    if time.monotonic()>=end:
                        result['status']='budget_exhausted';request();break
                    if difference>self.threshold:
                        result['status']='change_detected';request();break
                    if len(result['samples'])>=self.max_samples:
                        result['status']='budget_exhausted';request();break
                elif seen:
                    result['status']='held_ended';break
                time.sleep(self.interval_s)
            else:
                result['status']='budget_exhausted';request()
        except Exception as error:
            result['status']='monitor_error';result['error_type']=type(error).__name__;request()
        finally:
            if probe is not None:
                try:probe.close()
                except Exception as error:
                    result['status']='monitor_error';result['close_error_type']=type(error).__name__;request()
            result['finished_ns']=time.monotonic_ns();self._result=result
