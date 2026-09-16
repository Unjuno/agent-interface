from __future__ import annotations
import hashlib, json

class LineageError(ValueError):
    pass

def _canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()

def program_digest(program):
    return hashlib.sha256(_canon(program)).hexdigest()

def receipt_fields(r):
    return {
        'receipt_id': r['receipt_id'], 'role': r['role'], 'currentness': r['currentness'],
        'point': list(r['point']), 'observation_seq': r['observation_seq'],
        'binding_revision': r['binding_revision'], 'source_receipt_id': r.get('source_receipt_id'),
    }

def receipt_digest(r):
    return hashlib.sha256(_canon(receipt_fields(r))).hexdigest()

def seal_receipt(r):
    out=dict(r); out['digest']=receipt_digest(out); return out

def sidecar_fields(s):
    return {
        'program_digest': s['program_digest'], 'evidence_receipt_digest': s['evidence_receipt_digest'],
        'role': s['role'], 'currentness': s['currentness'], 'point': list(s['point']),
        'observation_seq': s['observation_seq'], 'binding_revision': s['binding_revision'],
    }

def sidecar_digest(s):
    return hashlib.sha256(_canon(sidecar_fields(s))).hexdigest()

def seal_sidecar(program, receipt):
    s={
        'program_digest': program_digest(program), 'evidence_receipt_digest': receipt['digest'],
        'role': receipt['role'], 'currentness': receipt['currentness'], 'point': list(receipt['point']),
        'observation_seq': receipt['observation_seq'], 'binding_revision': receipt['binding_revision'],
    }
    s['digest']=sidecar_digest(s); return s

def _pointer_point(program):
    pts=[(op['x'],op['y']) for op in program.get('ops',[]) if op.get('op')=='pointer_move']
    if len(pts)!=1: raise LineageError('PROGRAM_POINTER_SHAPE_UNSUPPORTED')
    return list(pts[0])

def validate_gate(program, receipt, sidecar):
    if receipt.get('digest') != receipt_digest(receipt): raise LineageError('EVIDENCE_RECEIPT_DIGEST_MISMATCH')
    if sidecar.get('digest') != sidecar_digest(sidecar): raise LineageError('SIDECAR_DIGEST_MISMATCH')
    if sidecar['program_digest'] != program_digest(program): raise LineageError('PROGRAM_DIGEST_MISMATCH')
    if sidecar['evidence_receipt_digest'] != receipt['digest']: raise LineageError('EVIDENCE_DIGEST_MISMATCH')
    for k in ('role','currentness','point','observation_seq','binding_revision'):
        if sidecar[k] != receipt[k]: raise LineageError('SIDECAR_RECEIPT_MISMATCH')
    if receipt['role']!='ADMISSION_DEPENDENCY' or receipt['currentness']!='CURRENT':
        raise LineageError('LINEAGE_NOT_CURRENT_ADMISSION')
    if program.get('source') != {'observation_seq':receipt['observation_seq'],'binding_revision':receipt['binding_revision']}:
        raise LineageError('PROGRAM_SOURCE_MISMATCH')
    if _pointer_point(program) != list(receipt['point']): raise LineageError('PROGRAM_POINT_MISMATCH')
    return True

def dispatch_with_gate(api, program, receipt, sidecar, targets, *, current_observation_seq, current_binding_revision, display_name=None):
    try:
        validate_gate(program,receipt,sidecar)
    except (LineageError,KeyError,TypeError,ValueError) as e:
        return {'schema':'agent-interface/lineage-dispatch-result-v1','status':'lineage_rejected','error':str(e)}
    out=api.dispatch(program,targets,current_observation_seq=current_observation_seq,current_binding_revision=current_binding_revision,display_name=display_name)
    return {'schema':'agent-interface/lineage-dispatch-result-v1','status':'delegated','cli_result':out}
