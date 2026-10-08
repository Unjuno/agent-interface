from __future__ import annotations
import hashlib, json

class BridgeError(ValueError):
    pass

def canonical_receipt_fields(r):
    return {
        'receipt_id': r['receipt_id'],
        'role': r['role'],
        'currentness': r['currentness'],
        'target_id': r['target_id'],
        'point': list(r['point']),
        'observation_seq': r['observation_seq'],
        'binding_revision': r['binding_revision'],
        'source_receipt_id': r.get('source_receipt_id'),
    }

def receipt_digest(r):
    return hashlib.sha256(json.dumps(canonical_receipt_fields(r), sort_keys=True, separators=(',',':')).encode()).hexdigest()

def seal(r):
    out=dict(r); out['digest']=receipt_digest(out); return out

def validate_receipt(r):
    if not isinstance(r,dict) or r.get('digest') != receipt_digest(r):
        raise BridgeError('RECEIPT_DIGEST_MISMATCH')
    if r['role'] not in {'HINT','ADMISSION_DEPENDENCY'}: raise BridgeError('UNSUPPORTED_ROLE')
    if r['currentness'] not in {'HISTORICAL','CURRENT'}: raise BridgeError('BAD_CURRENTNESS')
    if not isinstance(r['point'],(list,tuple)) or len(r['point'])!=2: raise BridgeError('BAD_POINT')
    return r

def build_program(program_id, evidence, lease_id='lease-1', expires_at_ns=10_000_000_000):
    x,y=evidence['point']
    return {
      'schema':'agent-interface/program-v1','program_id':program_id,
      'source':{'observation_seq':evidence['observation_seq'],'binding_revision':evidence['binding_revision']},
      'authority':{'lease_id':lease_id,'expires_at_ns':expires_at_ns},
      'terminal':{'release_all_required':True},
      'ops':[{'op':'pointer_move','frame':'screen_physical_px','x':x,'y':y},{'op':'release_all'}],
    }

def naive_bridge(program_id, target_evidence, source_override):
    validate_receipt(target_evidence)
    laundered=dict(target_evidence)
    laundered['observation_seq']=source_override['observation_seq']
    laundered['binding_revision']=source_override['binding_revision']
    return {'status':'PROGRAM_CONSTRUCTED','program':build_program(program_id,laundered),'lineage_receipt_id':target_evidence['receipt_id']}

def typed_bridge(program_id, target_evidence, revalidation=None):
    validate_receipt(target_evidence)
    if target_evidence['role']=='ADMISSION_DEPENDENCY' and target_evidence['currentness']=='CURRENT':
        if target_evidence.get('source_receipt_id') is not None:
            raise BridgeError('DIRECT_CURRENT_MUST_NOT_CLAIM_REVALIDATION_SOURCE')
        return {'status':'PROGRAM_CONSTRUCTED','program':build_program(program_id,target_evidence),'lineage_receipt_id':target_evidence['receipt_id']}
    if target_evidence['role']=='HINT' and target_evidence['currentness']=='HISTORICAL':
        if revalidation is None: raise BridgeError('HINT_REQUIRES_CURRENT_REVALIDATION')
        validate_receipt(revalidation)
        if revalidation['role']!='ADMISSION_DEPENDENCY' or revalidation['currentness']!='CURRENT':
            raise BridgeError('REVALIDATION_NOT_CURRENT_ADMISSION')
        if revalidation.get('source_receipt_id') != target_evidence['receipt_id']:
            raise BridgeError('REVALIDATION_SOURCE_MISMATCH')
        if revalidation['target_id'] != target_evidence['target_id']:
            raise BridgeError('REVALIDATION_TARGET_MISMATCH')
        return {'status':'PROGRAM_CONSTRUCTED','program':build_program(program_id,revalidation),'lineage_receipt_id':revalidation['receipt_id']}
    raise BridgeError('EVIDENCE_NOT_ACTUATOR_ADMISSIBLE')
