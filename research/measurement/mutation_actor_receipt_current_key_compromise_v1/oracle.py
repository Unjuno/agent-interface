from __future__ import annotations
import hashlib,hmac
import predecessor_experiment as parent

FIELDS=('version','key_id','key_epoch','nonce','session_id','intent_id','action_id','target_id','delta_kind','mutation_digest')

def verifier_accepts_current(record:dict,w:dict,current_epoch:int=1,used=None):
    used=set() if used is None else used
    if record.get('mutation') is False: return False
    if w.get('actor_class')!='THIS_INTENT': return False
    ep=w.get('key_epoch'); nonce=w.get('nonce')
    if w.get('version')!=1 or type(ep) is not int or ep!=current_epoch: return False
    if w.get('key_id')!=parent.KEYS[current_epoch][0]: return False
    if not isinstance(nonce,str) or not nonce or (ep,nonce) in used: return False
    mac=w.get('mac')
    if not isinstance(mac,str): return False
    want=hmac.new(parent.KEYS[current_epoch][1], '|'.join(str(w.get(k,'')) for k in FIELDS).encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(want,mac): return False
    for k in ('session_id','intent_id','action_id','target_id','delta_kind','mutation_digest'):
        if w.get(k)!=record.get(k): return False
    return True


def hidden_provenance_disposition(accepted:bool, producer:str):
    if not accepted: return 'REJECTED'
    if producer=='TRUSTED_RUNTIME': return 'TRUSTED_SELF_ACCEPTED'
    if producer=='COMPROMISED_ACTOR': return 'COMPROMISED_FORGE_ACCEPTED_BY_SINGLE_ROOT'
    return 'UNKNOWN_PRODUCER'
