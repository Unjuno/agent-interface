from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class Observation:
    url:str; uid:str; text:str; observed_ns:int
@dataclass(frozen=True)
class Decision:
    accepted:bool; error:str|None; suffix:str

def suffix_from_text(desired:str, observed:str)->Decision:
    if not desired.startswith(observed): return Decision(False,'NOT_PREFIX','')
    return Decision(True,None,desired[len(observed):])

def precheck_bound(obs:Observation, *, desired:str,target_url:str,current_row:dict,now_ns:int,max_age_ns:int)->Decision:
    if obs.url!=target_url:return Decision(False,'WRONG_DOCUMENT','')
    if current_row.get('url')!=target_url or current_row.get('uid')!=obs.uid:return Decision(False,'STALE_DOCUMENT_ID','')
    if current_row.get('text')!=obs.text:return Decision(False,'STALE_TEXT','')
    if now_ns-obs.observed_ns>max_age_ns:return Decision(False,'STALE_OBSERVATION','')
    return suffix_from_text(desired,obs.text)

def final_focus_guard(bound_xid:int, active_xid:int, focus_xid:int)->str|None:
    if not bound_xid or active_xid!=bound_xid or focus_xid!=bound_xid:return 'FOCUS_MISMATCH'
    return None
