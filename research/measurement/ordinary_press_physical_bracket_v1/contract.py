from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Times:
    call_start:int; pre_start:int; pre_end:int; press_request:int; sync_return:int; post_start:int; post_end:int; call_return:int
    def validate(self):
        xs=(self.call_start,self.pre_start,self.pre_end,self.press_request,self.sync_return,self.post_start,self.post_end,self.call_return)
        if any(type(x) is not int or x<0 for x in xs): raise ValueError('invalid timestamp')
        if list(xs)!=sorted(xs): raise ValueError('timestamp order')
@dataclass(frozen=True)
class Evidence:
    press_id:str; owner_id:str; intent_token:str; key:str
    owner_owned_before:bool; pre_key_down:bool; press_attempted:bool; sync_succeeded:bool; post_key_down:bool; owner_owned_after:bool
    times:Times

def _id(x):return isinstance(x,str) and bool(x.strip())
def build(e):
    if any(not _id(x) for x in (e.press_id,e.owner_id,e.intent_token,e.key)):raise ValueError('invalid lineage')
    bs=(e.owner_owned_before,e.pre_key_down,e.press_attempted,e.sync_succeeded,e.post_key_down,e.owner_owned_after)
    if any(type(x) is not bool for x in bs):raise ValueError('invalid boolean')
    e.times.validate()
    if e.sync_succeeded and not e.press_attempted:raise ValueError('sync without press')
    iv=None
    if e.owner_owned_before:status='OWNER_ALREADY_HELD'
    elif e.pre_key_down:status='PREEXISTING_PHYSICAL_DOWN'
    elif e.press_attempted and e.sync_succeeded and e.post_key_down and e.owner_owned_after:
        status='CONFIRMED_PHYSICAL_DOWN';iv=[e.times.pre_end,e.times.post_end]
    else:status='PRESS_UNCONFIRMED'
    return {'status':status,'physical_down_interval':iv,'press_id':e.press_id,'owner_id':e.owner_id,'intent_token':e.intent_token,'key':e.key,'grants_input_authority':False,'application_consumption_observed':False}
