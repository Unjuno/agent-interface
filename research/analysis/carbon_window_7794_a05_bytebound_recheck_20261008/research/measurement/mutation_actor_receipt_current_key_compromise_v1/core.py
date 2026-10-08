from __future__ import annotations
import hashlib,hmac,json
from copy import deepcopy
import predecessor_experiment as parent

TASK='MUTATION-ACTOR-RECEIPT-CURRENT-KEY-COMPROMISE-20260918-001'
SEED=127720260918001
BATCHES=4
PAIRS_PER_BATCH=50000


def visible_witness(i:int, nonce:str|None=None):
    # Exact predecessor signer grammar/current key epoch. Hidden producer provenance
    # is deliberately not serialized into the verifier-visible receipt.
    return parent.signed(i, 1, nonce=nonce or f'p{i}')


def compromised_forge_identical(legit:dict):
    # An actor holding the same active key can emit byte-identical verifier input.
    # deepcopy makes producer construction independent while preserving all visible bytes.
    w=deepcopy(legit)
    # Recompute rather than copy MAC to show current-key knowledge is sufficient.
    w.pop('mac',None)
    w['mac']=hmac.new(parent.KEYS[1][1], parent.canonical(w), hashlib.sha256).hexdigest()
    return w


def canonical_visible(w:dict)->bytes:
    return json.dumps(w,sort_keys=True,separators=(',',':')).encode()


def verify_visible(record:dict):
    return parent.Candidate().verify(record)


def pair_case(i:int):
    legit=visible_witness(i)
    forge=compromised_forge_identical(legit)
    assert canonical_visible(legit)==canonical_visible(forge)
    rec_legit=parent.rec(i,[legit])
    rec_forge=parent.rec(i,[forge])
    return {
        'visible_equal': canonical_visible(legit)==canonical_visible(forge),
        'legit': verify_visible(rec_legit),
        'forge': verify_visible(rec_forge),
        'visible_sha256': hashlib.sha256(canonical_visible(legit)).hexdigest(),
    }


def fixed_controls():
    out={}
    i=9900001
    # valid current trusted/compromised pair (candidate cannot see provenance)
    q=pair_case(i); out['legit_current']=q['legit']; out['compromised_current']=q['forge']; out['visible_equal']=q['visible_equal']
    # wrong key: claims current epoch/key id but MAC made with retired epoch1 key after rotate2
    c=parent.Candidate(); c.rotate(2)
    w=parent.signed(i+1,1,key_epoch=2,key_id='k2')
    out['wrong_key']=c.verify(parent.rec(i+1,[w]))
    # retired epoch after rotation
    c=parent.Candidate(); c.rotate(2); out['retired_epoch']=c.verify(parent.rec(i+2,[parent.signed(i+2,1)]))
    # future epoch while current2
    c=parent.Candidate(); c.rotate(2); out['future_epoch']=c.verify(parent.rec(i+3,[parent.signed(i+3,3)]))
    # same-epoch replay: first accepted, second rejected as unattributed
    c=parent.Candidate(); c.rotate(2); w=parent.signed(i+4,2,nonce='replay')
    out['replay_first']=c.verify(parent.rec(i+4,[w])); out['replay_second']=c.verify(parent.rec(i+4,[w]))
    # external and conflict preserve predecessor semantics
    ext={'actor_class':'EXTERNAL_PROCESS','target_id':parent.line(i+5)['target_id'],'delta_kind':parent.line(i+5)['delta_kind']}
    out['external']=parent.Candidate().verify(parent.rec(i+5,[ext]))
    out['conflict']=parent.Candidate().verify(parent.rec(i+6,[parent.signed(i+6,1),{'actor_class':'HUMAN','target_id':parent.line(i+6)['target_id'],'delta_kind':parent.line(i+6)['delta_kind']}]))
    out['no_mutation']=parent.Candidate().verify(parent.rec(i+7,[],False))
    return out
