from __future__ import annotations

UNCHANGED='UNCHANGED'
IRRELEVANT_CHANGE='IRRELEVANT_CHANGE'
DUPLICATE_TARGET='DUPLICATE_TARGET'
VALID_CROP='VALID_CROP'
TARGET_REMOVED='TARGET_REMOVED'
TARGET_CHANGED='TARGET_CHANGED'


def _validate_outside(states):
    states=tuple(states)
    if len(states)!=10:
        raise ValueError('bad_outside_count')
    allowed={UNCHANGED,IRRELEVANT_CHANGE,DUPLICATE_TARGET}
    if any(s not in allowed for s in states):
        raise ValueError('bad_outside_state')
    return states


def required_reuse(*,source_current:bool,critical_event:bool,outside_states,crop_state:str=VALID_CROP)->bool:
    states=_validate_outside(outside_states)
    if not isinstance(source_current,bool) or not isinstance(critical_event,bool):
        raise ValueError('bad_flag')
    if crop_state not in {VALID_CROP,TARGET_REMOVED,TARGET_CHANGED}:
        raise ValueError('bad_crop_state')
    return bool(source_current and not critical_event and crop_state==VALID_CROP and DUPLICATE_TARGET not in states)


def crop_only(*,source_current:bool,critical_event:bool,outside_states,crop_state:str=VALID_CROP)->dict:
    _validate_outside(outside_states)
    if not source_current:
        return {'action':'STALE_SOURCE_REJECTED','reason':'STALE_SOURCE'}
    if critical_event:
        return {'action':'FORWARD_CRITICAL','reason':'CRITICAL_EVENT'}
    if crop_state!=VALID_CROP:
        return {'action':'RAW_FALLBACK','reason':'CROP_CHANGED'}
    return {'action':'REUSE_CONTEXT','reason':'CROP_UNCHANGED'}


def support_closure(*,source_current:bool,critical_event:bool,outside_states,crop_state:str=VALID_CROP,uniqueness_bound:bool=True)->dict:
    states=_validate_outside(outside_states)
    if not isinstance(uniqueness_bound,bool):
        raise ValueError('bad_uniqueness_binding')
    if not source_current:
        return {'action':'STALE_SOURCE_REJECTED','reason':'STALE_SOURCE'}
    if critical_event:
        return {'action':'FORWARD_CRITICAL','reason':'CRITICAL_EVENT'}
    if crop_state!=VALID_CROP:
        return {'action':'RAW_FALLBACK','reason':'CROP_CHANGED'}
    if not uniqueness_bound:
        return {'action':'UNIQUENESS_RECEIPT_REJECTED','reason':'UNBOUND_UNIQUENESS_EVIDENCE'}
    if DUPLICATE_TARGET in states:
        return {'action':'RAW_FALLBACK','reason':'AMBIGUOUS_TARGET'}
    return {'action':'REUSE_CONTEXT','reason':'GLOBAL_UNIQUENESS_PROVEN'}
