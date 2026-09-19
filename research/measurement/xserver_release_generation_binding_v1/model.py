from dataclasses import dataclass

TERMINAL={'RELEASE_CONFIRMED','RELEASE_UNCONFIRMED_BACKEND_LOST'}

@dataclass
class State:
    owner_id:str
    intent_token:str
    key:str
    server_generation:str
    cleanup_attempt_id:str
    status:str='PENDING'
    verified_empty:bool=False

def step(s,event):
    if s.status in TERMINAL:
        return s.status
    if type(event) is not dict or type(event.get('kind')) is not str:
        raise ValueError('malformed event')
    k=event['kind']
    if k=='backend_lost':
        s.status='RELEASE_UNCONFIRMED_BACKEND_LOST'; s.verified_empty=False
        return s.status
    if k!='release_observation':
        raise ValueError('unknown event')
    required=('owner_id','intent_token','key','server_generation','cleanup_attempt_id','key_up')
    if any(x not in event for x in required) or type(event['key_up']) is not bool:
        raise ValueError('malformed release observation')
    lineage=(event['owner_id']==s.owner_id and event['intent_token']==s.intent_token and event['key']==s.key and
             event['server_generation']==s.server_generation and event['cleanup_attempt_id']==s.cleanup_attempt_id)
    if lineage and event['key_up']:
        s.status='RELEASE_CONFIRMED'; s.verified_empty=True
    return s.status
