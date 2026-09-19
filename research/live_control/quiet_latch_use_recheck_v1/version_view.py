"""Fresh condition evidence with optional use-time source-version recheck.

The initial condition sample is historical evidence by the time it is consumed.
A version recheck can invalidate it but never grants authority or mutates history.
"""
from __future__ import annotations
import time, uuid
MAX_AGE_NS=100_000_000

class VersionedConditionView:
    def __init__(self, scope:str, producer_epoch:str, source_epoch:str, arm:str):
        if arm not in ('baseline','recheck'): raise ValueError('arm')
        if not all(type(x) is str and x for x in (scope,producer_epoch,source_epoch)): raise ValueError('identity')
        self.scope=scope; self.producer_epoch=producer_epoch; self.source_epoch=source_epoch; self.arm=arm
        self.initial_request=None; self.evidence=None; self.recheck_request_data=None; self.recheck=None; self.reason='NOT_CHECKED'
    def request(self,event_sequence:int)->dict:
        if type(event_sequence) is not int or event_sequence<1: raise ValueError('event sequence')
        self.initial_request=dict(scope=self.scope,producer_epoch=self.producer_epoch,source_epoch=self.source_epoch,
          event_sequence=event_sequence,request_id=uuid.uuid4().hex,requested_ns=time.perf_counter_ns())
        return dict(self.initial_request)
    def accept(self,receipt:object,current_sequence:int,now_ns:int|None=None)->dict:
        now=time.perf_counter_ns() if now_ns is None else now_ns; req=self.initial_request; self.initial_request=None; self.evidence=None
        reason=None
        if req is None: reason='NO_REQUEST'
        elif type(receipt) is not dict: reason='MISSING'
        else:
            for k in ('scope','producer_epoch','source_epoch','event_sequence','request_id'):
                if type(receipt.get(k)) is not type(req[k]) or receipt[k]!=req[k]: reason='BINDING_'+k.upper(); break
            if reason is None and current_sequence!=req['event_sequence']: reason='EVENT_CHANGED'
            if reason is None:
                if any(type(receipt.get(k)) is not int for k in ('sample_start_ns','sample_end_ns','source_version')): reason='METADATA'
                elif receipt['source_version']<1: reason='VERSION'
                elif not req['requested_ns']<=receipt['sample_start_ns']<=receipt['sample_end_ns']<=now: reason='TIME'
                elif now-receipt['sample_start_ns']>MAX_AGE_NS: reason='STALE'
                elif type(receipt.get('active')) is not bool: reason='CONDITION'
        if reason is None: self.evidence=dict(receipt); self.reason='FRESH'
        else: self.reason=reason
        return dict(accepted=reason is None,reason=self.reason,grants_input_authority=False,evaluated_ns=now)
    def request_recheck(self,current_sequence:int)->dict:
        e=self.evidence
        self.recheck=None
        if e is None: raise ValueError('no initial evidence')
        if current_sequence!=e['event_sequence']: raise ValueError('event changed')
        self.recheck_request_data=dict(scope=self.scope,producer_epoch=self.producer_epoch,source_epoch=self.source_epoch,
          event_sequence=current_sequence,request_id=uuid.uuid4().hex,expected_source_version=e['source_version'],requested_ns=time.perf_counter_ns())
        return dict(self.recheck_request_data)
    def accept_recheck(self,receipt:object,current_sequence:int,now_ns:int|None=None)->dict:
        now=time.perf_counter_ns() if now_ns is None else now_ns; req=self.recheck_request_data; self.recheck_request_data=None
        reason=None
        if req is None: reason='NO_RECHECK_REQUEST'
        elif type(receipt) is not dict: reason='MISSING_RECHECK'
        else:
            for k in ('scope','producer_epoch','source_epoch','event_sequence','request_id'):
                if type(receipt.get(k)) is not type(req[k]) or receipt[k]!=req[k]: reason='RECHECK_BINDING_'+k.upper(); break
            if reason is None and current_sequence!=req['event_sequence']: reason='EVENT_CHANGED'
            if reason is None:
                if any(type(receipt.get(k)) is not int for k in ('sample_start_ns','sample_end_ns','source_version')): reason='RECHECK_METADATA'
                elif not req['requested_ns']<=receipt['sample_start_ns']<=receipt['sample_end_ns']<=now: reason='RECHECK_TIME'
                elif now-receipt['sample_start_ns']>MAX_AGE_NS: reason='RECHECK_STALE'
                elif receipt['source_version']!=req['expected_source_version']: reason='SOURCE_VERSION_CHANGED'
        self.recheck=dict(accepted=reason is None,reason=reason or 'UNCHANGED',receipt=dict(receipt) if type(receipt) is dict else None,
                          expected_source_version=req['expected_source_version'] if req else None,evaluated_ns=now,grants_input_authority=False)
        return dict(self.recheck)
    def consume(self,current_sequence:int,now_ns:int|None=None)->dict:
        now=time.perf_counter_ns() if now_ns is None else now_ns; e=self.evidence; reason=self.reason; state='UNKNOWN'
        if e is not None:
            if current_sequence!=e['event_sequence']: reason='EVENT_CHANGED'
            elif now<e['sample_end_ns'] or now-e['sample_start_ns']>MAX_AGE_NS: reason='STALE'
            elif self.arm=='recheck' and (self.recheck is None or not self.recheck['accepted']):
                reason='RECHECK_REQUIRED' if self.recheck is None else self.recheck['reason']
            else:
                state='ACTIVE' if e['active'] else 'RESOLVED'; reason='FRESH_AT_USE' if self.arm=='recheck' else 'BASELINE_NO_USE_RECHECK'
        return dict(current_state=state,reason=reason,evidence=e,recheck=self.recheck,evaluated_ns=now,grants_input_authority=False)
