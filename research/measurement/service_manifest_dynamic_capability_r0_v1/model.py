from __future__ import annotations
import hashlib, json

FALLBACK='universal_raw_control'
BASE_CAPS=('observe_raw','pointer','keyboard')

def stable_manifest():
    return {
      'schema':'agent-interface/service-manifest-r0',
      'service_id':'agent-interface',
      'protocol':{'id':'agent-interface','major':1},
      'relations':{'operation_schema':'schema://operations','capability_snapshot':'cap://session','events':'events://session','control':'control://session'},
      'semantics':{'authority':'runtime_grant_required','freshness':'generation_bound','handback':'typed_receipt'},
      'fallback':FALLBACK,
    }

def inline_manifest(scope,generation,caps):
    x=stable_manifest(); x['session_capabilities']={'scope':scope,'generation':generation,'caps':sorted(caps)}; return x

def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def validate_manifest(m):
    if not isinstance(m,dict): return False,'manifest_type'
    rel=m.get('relations')
    if not isinstance(rel,dict) or not rel.get('capability_snapshot'): return False,'capability_discovery'
    if m.get('fallback') != FALLBACK: return False,'fallback'
    p=m.get('protocol')
    if not isinstance(p,dict) or p.get('id')!='agent-interface' or not isinstance(p.get('major'),int): return False,'protocol'
    sem=m.get('semantics')
    if not isinstance(sem,dict) or sem.get('authority')!='runtime_grant_required' or sem.get('freshness')!='generation_bound': return False,'semantics'
    return True,'ok'

def snapshot(scope,generation,caps):
    return {'scope':scope,'generation':generation,'caps':tuple(sorted(caps))}

def linked_select(manifest,current_scope,current_generation,current_caps,snap,requested):
    ok,_=validate_manifest(manifest)
    if not ok: return 'MANIFEST_INCOMPLETE'
    if not isinstance(snap,dict): return 'DISCOVER_CAPABILITIES'
    if snap.get('scope')!=current_scope or snap.get('generation')!=current_generation: return 'DISCOVER_CAPABILITIES'
    caps=set(snap.get('caps',()))
    if requested in caps: return 'SUPPORTED'
    return 'FALLBACK'
