from __future__ import annotations
from dataclasses import dataclass

STATUSES=('CONFIRMED_PHYSICAL_UP','NOOP_ALREADY_UP','FOREIGN_OR_STALE_DOWN','OWNER_PHYSICAL_MISMATCH','RELEASE_UNCONFIRMED')

@dataclass(frozen=True)
class Times:
    call_start:int; pre_start:int; pre_end:int; release_request:int; sync_return:int; post_start:int; post_end:int; call_return:int
    def validate(self):
        vals=(self.call_start,self.pre_start,self.pre_end,self.release_request,self.sync_return,self.post_start,self.post_end,self.call_return)
        if any(type(x) is not int or x<0 for x in vals): raise ValueError('invalid timestamp')
        if list(vals)!=sorted(vals): raise ValueError('timestamp order')

@dataclass(frozen=True)
class Evidence:
    release_id:str; owner_id:str; intent_token:str; key:str
    owner_owned:bool; pre_key_down:bool; release_attempted:bool; sync_succeeded:bool; post_key_down:bool
    times:Times

def _id(x): return isinstance(x,str) and bool(x.strip())

def build(e:Evidence):
    for x in (e.release_id,e.owner_id,e.intent_token,e.key):
        if not _id(x): raise ValueError('invalid lineage')
    for x in (e.owner_owned,e.pre_key_down,e.release_attempted,e.sync_succeeded,e.post_key_down):
        if type(x) is not bool: raise ValueError('invalid boolean')
    e.times.validate()
    if e.sync_succeeded and not e.release_attempted: raise ValueError('sync without release')
    if e.release_attempted and not e.owner_owned: raise ValueError('release without ownership')
    interval=None
    if not e.owner_owned:
        status='FOREIGN_OR_STALE_DOWN' if e.pre_key_down else 'NOOP_ALREADY_UP'
    elif not e.pre_key_down:
        status='OWNER_PHYSICAL_MISMATCH'
    elif e.release_attempted and e.sync_succeeded and not e.post_key_down:
        status='CONFIRMED_PHYSICAL_UP'; interval=[e.times.pre_end,e.times.post_end]
    else:
        status='RELEASE_UNCONFIRMED'
    return {'status':status,'physical_up_interval':interval,'release_id':e.release_id,'owner_id':e.owner_id,'intent_token':e.intent_token,'key':e.key,'grants_input_authority':False,'application_consumption_observed':False}
