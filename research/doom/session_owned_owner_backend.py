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
    owned_generation_rotation_supported=True
    def __init__(self,session,out,emit,signal_readers,*,_owner_factory=None,renewal_passive_observer=False,timed_hold=False):
        if type(timed_hold) is not bool:raise ValueError('timed_hold must be boolean')
        self._timed_hold_enabled=timed_hold
        self.owned_service=None;self._session_out=Path(out);self._startup_hash=None
        self._owner_factory=_owner_factory;self._rotation_broken=False;self._rotation_handle=None
        self._session_lock=threading.RLock();self._session_close=None;self._session_error=None
        try:
            options=dict(display=session.name,out=self._session_out/'input-owner-service',
                         cancellation=True,_owner_factory=_owner_factory)
            if timed_hold:options['timed_up']=True
            self.owned_service=launch_owner_service(**options)
            super().__init__(session,out,emit,signal_readers,owner_service=self.owned_service,
                             renewal_passive_observer=renewal_passive_observer)
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

    def claim_executor_custody(self, token):
        with self._executor_custody_lock:
            if self._rotation_broken:
                raise ValueError('owned service rotation incomplete; no new authority')
            return super().claim_executor_custody(token)

    def rotate_input_owner_after_cancel(self, terminal):
        """Retire a verified owned generation before creating a fresh one."""
        from input_owner_service_adapter import OwnedOwnerAdapter
        from verified_interruption_release_v1 import qualified_interruption_release
        ordinary_cancel=(type(terminal) is dict and terminal.get('status')=='cancelled')
        if (type(terminal) is not dict or terminal.get('event')!='terminal'
                or not (ordinary_cancel or qualified_interruption_release(terminal))):
            raise ValueError('verified cancelled or qualified interruption terminal required')
        identifier=terminal.get('id'); release=terminal.get('release')
        reader=release.get('target_process_identity_reader') if type(release) is dict else None
        if (type(identifier) is not str or not identifier or identifier in self._consumed_rotation_terminals
                or type(terminal.get('input_owner_generation')) is not int
                or terminal['input_owner_generation'] != self._owner_generation
                or terminal.get('input_owner_id') != self.owner.owner_id
                or type(reader) is not dict or reader.get('retired') is not True
                or release.get('verified') is not True
                or any(release.get(k) != [] for k in ('keys_down','buttons_down','keys_unknown','key_state_errors'))):
            raise ValueError('current verified empty cancelled terminal with retired reader required')
        with self._session_lock, self._executor_custody_lock:
            if (identifier in self._consumed_rotation_terminals
                    or terminal['input_owner_generation'] != self._owner_generation
                    or terminal['input_owner_id'] != self.owner.owner_id):
                raise ValueError('owned generation changed before rotation')
            if (self._rotation_broken or self._session_close is not None
                    or self._executor_custody_owner is not None or self._executor_release_obligation is not None
                    or self.owner.obligation_snapshot() is not None):
                raise ValueError('owned generation custody not settled')
            if self._owner_generation >= 2:
                raise ValueError('owned generation rotation budget exhausted')
            old=self.owner; old_service=self.owned_service; old_generation=self._owner_generation
            self._consumed_rotation_terminals.add(identifier)
            self._rotation_broken=True
            self._rotation_handle=old_service
            old_close=old.close()
            if type(old_close) is not dict or old_close.get('verified') is not True:
                raise OwnerServiceCleanupUnverified(old_close)
            archive=dict(schema='map01-owned-generation-close-v1',generation=old_generation,
                startup_sha256=self._startup_hash,service_id=old_service.service_id,
                owner_id=old.owner_id,adapter=old_close,grants_input_authority=False)
            archive_hash=publish_json_exclusive(self._session_out/f'owner-generation-{old_generation}-close.json',archive)
            self._archived_owner_records.extend(old.records)
            next_generation=old_generation+1
            new_service=None; new_owner=None
            try:
                options=dict(display=self.session.name,
                    out=self._session_out/f'input-owner-service-generation-{next_generation}',
                    cancellation=True,_owner_factory=self._owner_factory)
                if self._timed_hold_enabled:options['timed_up']=True
                new_service=launch_owner_service(**options)
                new_owner=OwnedOwnerAdapter(new_service,display=self.session.name)
                if new_owner.owner_id==old.owner_id or new_service.service_id==old_service.service_id:
                    raise ValueError('new owned service identity must differ')
                startup=dict(schema='map01-owned-generation-startup-v1',generation=next_generation,
                    previous_close_sha256=archive_hash,startup=new_service.startup,
                    spawn_pid=new_service.process.pid,grants_input_authority=False)
                startup_hash=publish_json_exclusive(self._session_out/f'owner-generation-{next_generation}-startup.json',startup)
            except BaseException as primary:
                handle=new_service or getattr(primary,'owner_service_handle',None)
                if handle is not None:self._rotation_handle=handle
                errors=[]
                if new_owner is not None:
                    try:
                        cleanup=new_owner.close()
                        if cleanup.get('verified') is not True:errors.append(OwnerServiceCleanupUnverified(cleanup))
                    except BaseException as error:errors.append(error)
                elif handle is not None:
                    try:handle.close_channel(); handle.wait(5)
                    except BaseException as error:errors.append(error)
                _raise(errors,primary,handle or old_service)
            self.owner=self._provided_input_owner=new_owner
            self.owned_service=new_service;self._startup_hash=startup_hash
            self._owner_generation=next_generation
            self._source_identity=None;self._source_window_identity=None;self._source_renewal_window_identity=None
            self._rotation_broken=False
            self._rotation_handle=None
            return dict(event='input_owner_generation',terminal_id=identifier,generation=next_generation,
                previous_generation=old_generation,previous_owner_id=old.owner_id,owner_id=new_owner.owner_id,
                source_invalidated=True,grants_input_authority=False,previous_close_sha256=archive_hash)

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
            rotation_incomplete=getattr(self,'_rotation_broken',False)
            receipt=dict(schema='map01-owned-session-close-v1',startup_sha256=self._startup_hash,
                service_id=self.owned_service.service_id,adapter=adapter,grants_input_authority=False,
                rotation_incomplete=rotation_incomplete,
                rotation_service_id=getattr(getattr(self,'_rotation_handle',None),'service_id',None),
                verified=not rotation_incomplete and not errors and self._startup_hash is not None
                         and type(adapter) is dict and adapter.get('verified') is True)
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
