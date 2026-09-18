from __future__ import annotations
import hashlib, json

RELATIONS = ('control','observation','operation_schema','capability_snapshot','observation_catalog','events','fallback')

def semantic_manifest():
    return {
      'schema':'agent-interface/service-manifest-r2',
      'service':{'id':'agent-interface'},
      'protocol':{'id':'agent-interface','major':1},
      'relations':{name:f'rel.{name}' for name in RELATIONS},
      'semantics':{'authority':'runtime_grant_required','freshness':'generation_bound','handback':'typed_receipt'}
    }

def canonical_hash(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def binding(service_id, protocol_major, epoch, adapter, endpoints):
    return {'service_id':service_id,'protocol_major':protocol_major,'transport_epoch':epoch,
            'adapter':adapter,'endpoints':dict(endpoints)}

def inline_manifest(scope, epoch, adapter, endpoints):
    m=semantic_manifest(); m['transport']={'scope':scope,'epoch':epoch,'adapter':adapter,'endpoints':dict(endpoints)}; return m

def _valid_endpoint(x):
    return isinstance(x,str) and bool(x) and '\n' not in x and '\r' not in x

def resolve(manifest, current_service, current_protocol_major, current_epoch, b, relation):
    if not isinstance(manifest,dict): return ('MANIFEST_INVALID',None)
    rels=manifest.get('relations')
    if not isinstance(rels,dict) or relation not in rels or 'fallback' not in rels:
        return ('MANIFEST_INCOMPLETE',None)
    logical=rels[relation]; fallback=rels['fallback']
    if not isinstance(b,dict): return ('DISCOVER_BINDING',None)
    if b.get('service_id')!=current_service or b.get('protocol_major')!=current_protocol_major or b.get('transport_epoch')!=current_epoch:
        return ('DISCOVER_BINDING',None)
    eps=b.get('endpoints')
    if not isinstance(eps,dict): return ('DISCOVER_BINDING',None)
    target=eps.get(logical)
    if _valid_endpoint(target): return ('BOUND',target)
    fb=eps.get(fallback)
    if _valid_endpoint(fb): return ('FALLBACK',fb)
    return ('BINDING_INCOMPLETE',None)
