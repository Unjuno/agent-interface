from __future__ import annotations
import copy

class IdentityBindingError(ValueError):
    pass

def bind_authority_end_identity(receipt, terminal):
    if type(receipt) is not dict or type(terminal) is not dict:
        raise IdentityBindingError('receipt and terminal required')
    if terminal.get('status') != 'authority_ended':
        raise IdentityBindingError('authority_ended terminal required')
    intr=terminal.get('interruption')
    if type(intr) is not dict:
        raise IdentityBindingError('interruption evidence required')
    rid=intr.get('intent_token')
    if type(rid) is not str or not rid:
        raise IdentityBindingError('runtime interruption intent_token required')
    rec=intr.get('record')
    if type(rec) is not dict or rec.get('reason') != 'expired':
        raise IdentityBindingError('verified expiry interruption required')
    if rec.get('verified') is not True or rec.get('keys_down') != [] or rec.get('buttons_down') != []:
        raise IdentityBindingError('verified empty expiry interruption required')
    rel=terminal.get('release')
    if type(rel) is not dict or rel.get('verified') is not True or rel.get('keys_down') != [] or rel.get('buttons_down') != []:
        raise IdentityBindingError('verified empty terminal release required')
    rel_token=rel.get('intent_token')
    if rel_token is not None and rel_token != rid:
        raise IdentityBindingError('release/interruption intent_token mismatch')
    supplied=receipt.get('authority_end_id')
    if supplied is not None and (type(supplied) is not str or not supplied):
        raise IdentityBindingError('caller authority_end_id must be nonempty when supplied')
    out=copy.deepcopy(receipt)
    out['authority_end_id']=supplied if supplied is not None else rid
    return out
