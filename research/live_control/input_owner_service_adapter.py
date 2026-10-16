"""Explicit selected-backend custody for ordinary RPC plus cancellation service."""
import copy
import threading

import input_owner_rpc_v2 as rpc
from input_owner_cancel_v4 import CancellationClient


class OwnedOwnerAdapter:
    def __init__(self,service,*,display,timeout=2,close_timeout=5):
        self.service=service;self.timeout=rpc._timeout(timeout);self.close_timeout=rpc._timeout(close_timeout)
        self._lock=threading.RLock();self._obligation=None;self._records=[];self._attempted=set()
        self._leases={};self._bindings={};self._close_result=None;self._closed=False;self._closing=False;self.client=self.control=None
        startup=service.startup
        if (type(startup) is not dict or startup.get('display')!=display
                or startup.get('cancellation_enabled') is not True):
            raise ValueError('owned cancellation service for the selected display required')
        self.owner_id=startup['owner_id'];self.service_id=startup['service_id']
        try:
            self.client=rpc.OwnerRpcClient(service.take_socket(),display=display,service_id=self.service_id,timeout=self.timeout)
            self.control=CancellationClient(service.take_cancellation_socket(),startup=startup,timeout=self.timeout)
        except BaseException as error:
            error.owner_service_handle=service
            closers=[]
            if self.client is not None:closers.append(self.client.close)
            if self.control is not None:closers.append(self.control.close)
            closers.append(service.close_channel)
            try:rpc._run_cleanups(*closers)
            except BaseException as cleanup:
                cleanup.owner_service_handle=service;raise
            raise

    def _retain(self,kind,detail):
        with self._lock:
            if self._obligation is None:
                self._obligation=dict(schema='owned-adapter-obligation-v1',service_id=self.service_id,
                    owner_id=self.owner_id,kind=kind,detail=copy.deepcopy(detail),grants_input_authority=False)

    def _refresh(self):
        outcomes=self.control.outcomes
        with self._lock:
            for token,outcome in outcomes.items():
                if token in self._attempted and outcome is not None and (
                        outcome.get('release_verified') is not True or outcome.get('cause_applied') is not True):
                    self._retain('cancellation_unverified',dict(intent_token=token,outcome=outcome))
        return outcomes

    def obligation_snapshot(self):
        self._refresh()
        with self._lock:return copy.deepcopy(self._obligation)

    @property
    def records(self):
        outcomes=self._refresh()
        incoming=self.client.records
        incoming.extend(outcome['cause']['record'] for outcome in outcomes.values()
                        if outcome is not None and outcome.get('cause_applied') and outcome.get('cause') is not None)
        with self._lock:
            for row in incoming:
                if row not in self._records:self._records.append(copy.deepcopy(row))
            return copy.deepcopy(self._records)

    def bind_lease(self,lease):
        with self._lock:
            if self._closed or self.obligation_snapshot() is not None:
                raise ValueError('external owner has unresolved custody; no new authority')
            self.control.watch(lease)
            self._leases[lease.intent_token]=lease
            self._bindings[lease.intent_token]=rpc.encode_lease(lease)

    def call(self,operation,lease=None,key=None):
        with self._lock:
            if self._closed:raise RuntimeError('external owner adapter closed')
            if lease is not None:
                token=getattr(lease,'intent_token',None);expected=copy.deepcopy(self._bindings.get(token))
                current=rpc.encode_lease(lease)
                if expected is not None:
                    for flag in ('cancel_requested','focus_invalid'):expected[flag]=current[flag]
                if self._leases.get(token) is not lease or expected!=current:
                    self._retain('original_source_changed',dict(operation=operation,intent_token=token))
                    raise ValueError('original backend source binding changed; no RPC sent')
            if operation in ('down','up','up_batch'):
                if self.obligation_snapshot() is not None:raise ValueError('external owner release unverified')
                token=getattr(lease,'intent_token',None)
                if self._leases.get(token) is not lease:raise ValueError('original backend-bound lease required')
                self._attempted.add(token)
        if operation=='release' and lease is not None and lease.cancel.is_set():
            token=lease.intent_token
            if token in self._attempted:
                try:self.control.wait(token,self.timeout)
                except Exception as error:self._retain('cancellation_outcome_unknown',dict(error=type(error).__name__))
        try:result=self.client.call(operation,lease,key)
        except BaseException as error:
            self._retain('ordinary_rpc_unknown',dict(operation=operation,error=type(error).__name__))
            if operation=='release' and isinstance(error,Exception):
                return dict(verified=False,error=type(error).__name__,owner_service_obligation=self.obligation_snapshot())
            raise
        if operation=='release' and (type(result) is not dict or result.get('verified') is not True):
            self._retain('ordinary_release_unverified',result)
        obligation=self.obligation_snapshot()
        if operation=='release' and obligation is not None:
            return dict(result if type(result) is dict else {},verified=False,owner_service_obligation=obligation,
                        underlying_cleanup_verified=type(result) is dict and result.get('verified') is True)
        return result

    def close(self):
        with self._lock:
            if self._close_result is not None:
                if self._closing:
                    self._retain('concurrent_close_unresolved',dict(service_id=self.service_id))
                    self._close_result['obligation']=copy.deepcopy(self._obligation)
                return copy.deepcopy(self._close_result)
            self._closed=True;self._closing=True
            self._close_result=dict(schema='owned-adapter-close-v1',verified=False,service_id=self.service_id,
                owner_id=self.owner_id,service_report=None,ordinary_close=None,obligation=self.obligation_snapshot())
        errors=[];exceptions=[];fatal=False;ordinary=None;report=None
        for name,action in (('ordinary_close',self.client.close),('control_close',self.control.close),
                            ('handle_channels',self.service.close_channel),('service_wait',lambda:self.service.wait(self.close_timeout))):
            try:
                value=action()
                if name=='ordinary_close':ordinary=value
                if name=='service_wait':report=value
            except BaseException as error:
                errors.append(dict(stage=name,error=type(error).__name__))
                exceptions.append(error)
                if not isinstance(error,Exception):fatal=True
        if ordinary is None or ordinary.get('verified') is not True:self._retain('ordinary_close_unverified',ordinary)
        if report is None or report.get('verified') is not True:self._retain('owned_service_exit_unverified',report)
        if errors:self._retain('adapter_close_error',errors)
        obligation=self.obligation_snapshot()
        with self._lock:
            self._close_result.update(ordinary_close=ordinary,service_report=report,obligation=obligation,errors=errors,
                verified=not errors and obligation is None and ordinary is not None and ordinary.get('verified') is True
                         and report is not None and report.get('verified') is True)
            self._closing=False
            result=copy.deepcopy(self._close_result)
        if fatal:
            error=exceptions[0] if len(exceptions)==1 else BaseExceptionGroup('adapter fatal cleanup failures',exceptions)
            error.owner_service_handle=self.service;error.adapter_close_result=result;raise error
        return result
