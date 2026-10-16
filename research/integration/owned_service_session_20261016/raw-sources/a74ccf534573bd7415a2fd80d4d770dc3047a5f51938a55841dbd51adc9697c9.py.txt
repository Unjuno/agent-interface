"""Explicit V15 service selection with immutable session cleanup evidence."""
import copy
from pathlib import Path
import sys
import threading

from doom_process_identity_backend_v1 import Backend as Previous
from input_owner_process_v3 import launch_owner_service,publish_json_exclusive


class OwnerServiceCleanupUnverified(RuntimeError):
    def __init__(self,receipt):
        super().__init__('owned input service cleanup unverified; custody retained')
        self.receipt=copy.deepcopy(receipt)


def _raise(errors,primary,handle,receipt=None):
    errors=list(errors)
    if primary is not None and not any(error is primary for error in errors):errors.insert(0,primary)
    if not errors:return
    error=errors[0] if len(errors)==1 else BaseExceptionGroup('session owner operation and cleanup failures',errors)
    error.owner_service_handle=handle
    if receipt is not None:error.session_owner_receipt=copy.deepcopy(receipt)
    raise error


class Backend(Previous):
    def __init__(self,session,out,emit,signal_readers,*,_owner_factory=None):
        self.owned_service=None;self._session_out=Path(out);self._startup_hash=None
        self._session_lock=threading.RLock();self._session_close=None;self._session_error=None
        try:
            self.owned_service=launch_owner_service(display=session.name,out=self._session_out/'input-owner-service',
                cancellation=True,_owner_factory=_owner_factory)
            super().__init__(session,out,emit,signal_readers,owner_service=self.owned_service)
            startup=dict(schema='map01-owned-session-startup-v1',startup=self.owned_service.startup,
                         spawn_pid=self.owned_service.process.pid,grants_input_authority=False)
            self._startup_hash=publish_json_exclusive(self._session_out/'session-owner-service-startup.json',startup)
        except BaseException as primary:
            handle=self.owned_service or getattr(primary,'owner_service_handle',None)
            self.owned_service=handle;errors=[];report=None
            if getattr(self,'owner',None) is not None:
                try:super().close()
                except BaseException as error:errors.append(error)
            if handle is not None:
                try:handle.close_channel()
                except BaseException as error:errors.append(error)
                try:report=handle.wait(5)
                except BaseException as error:errors.append(error)
            failure=dict(schema='map01-owned-session-startup-failure-v1',verified=False,
                error_type=type(primary).__name__,service_report=report,
                spawn_pid=getattr(getattr(handle,'process',None),'pid',None),grants_input_authority=False)
            try:publish_json_exclusive(self._session_out/'session-owner-service-startup-failure.json',failure)
            except BaseException as error:errors.append(error)
            _raise(errors,primary,handle,failure)

    def close(self):
        primary=sys.exception()
        with self._session_lock:
            if self._session_close is not None:
                if self._session_error is not None:_raise([self._session_error],primary,self.owned_service,self._session_close)
                return copy.deepcopy(self._session_close)
            errors=[];adapter=None
            try:adapter=super().close()
            except BaseException as error:
                errors.append(error);adapter=getattr(error,'adapter_close_result',None)
            receipt=dict(schema='map01-owned-session-close-v1',startup_sha256=self._startup_hash,
                service_id=self.owned_service.service_id,adapter=adapter,grants_input_authority=False,
                verified=not errors and self._startup_hash is not None and type(adapter) is dict and adapter.get('verified') is True)
            self._session_close=copy.deepcopy(receipt)
            try:publish_json_exclusive(self._session_out/'session-owner-service-close.json',receipt)
            except BaseException as error:
                errors.append(error)
                receipt=dict(receipt,verified=False,evidence_error=type(error).__name__)
                self._session_close=copy.deepcopy(receipt)
            if not receipt['verified']:errors.append(OwnerServiceCleanupUnverified(receipt))
            if errors:
                self._session_error=errors[0] if len(errors)==1 else BaseExceptionGroup('session owner close/evidence failed',errors)
                _raise([self._session_error],primary,self.owned_service,receipt)
            return copy.deepcopy(receipt)
