from __future__ import annotations

def valid_ep(x): return type(x) is str and len(x)>0 and '\n' not in x and '\r' not in x

def decide(manifest,service,major,epoch,binding,relation):
    if type(manifest) is not dict:return ('MANIFEST_INVALID',None)
    r=manifest.get('relations')
    if type(r) is not dict or relation not in r or 'fallback' not in r:return ('MANIFEST_INCOMPLETE',None)
    if type(binding) is not dict:return ('DISCOVER_BINDING',None)
    if binding.get('service_id')!=service or binding.get('protocol_major')!=major or binding.get('transport_epoch')!=epoch:return ('DISCOVER_BINDING',None)
    e=binding.get('endpoints')
    if type(e) is not dict:return ('DISCOVER_BINDING',None)
    v=e.get(r[relation])
    if valid_ep(v):return ('BOUND',v)
    f=e.get(r['fallback'])
    if valid_ep(f):return ('FALLBACK',f)
    return ('BINDING_INCOMPLETE',None)
