import json
import numpy as np
LABELS=['CTRL_WHEEL','NATIVE_SCALE','STALE_CAPABILITY','UNSUPPORTED']
HSTAT=['LIVE','MISSING','STALE','AMBIGUOUS','UNKNOWN','SCOPE_MISMATCH']

def truth(x):
    ns,nc,cp,np_,s,w,g,l=map(int,x)
    if not (s and w and g and l): return 2
    if not (ns or nc): return 3
    if cp: return 0
    if np_ and ns and not nc: return 1
    return 3

def make_payload(bits, handle_status, nonce):
    ns,nc,cp,np_,s,w,g=bits
    caps=[]
    if cp:
        caps.append({'route':'ctrl_wheel','effect_dimensions':['scale','center'],'evidence_role':'CAPABILITY','authority':'none','dependencies':{'session_id':'S1','surface_id':'W1','geometry_epoch':7}})
    if np_:
        caps.append({'route':'native_scale','effect_dimensions':['scale'],'evidence_role':'CAPABILITY','authority':'none','dependencies':{'session_id':'S1','surface_id':'W1','geometry_epoch':7}})
    return json.dumps({'request':{'required_effect_dimensions':(['scale'] if ns else [])+(['center'] if nc else []),'authority':'none'},'capabilities':caps,'current':{'session_id':'S1' if s else 'S2','surface_id':'W1' if w else 'W2','geometry_epoch':7 if g else 8,'target_handle_status':handle_status},'provenance':{'receipt_digest':'a'*64,'source':'retained-route-capability','nonce':int(nonce)}},separators=(',',':'),sort_keys=True)

def extract_validate(payload):
    o=json.loads(payload)
    req=o['request']; caps=o['capabilities']; cur=o['current']; prov=o['provenance']
    if req.get('authority')!='none': raise ValueError('authority')
    if len(prov.get('receipt_digest',''))!=64: raise ValueError('digest')
    dims=set(req.get('required_effect_dimensions',[]))
    if not dims <= {'scale','center'}: raise ValueError('dimension')
    by={}
    for c in caps:
        if c.get('evidence_role')!='CAPABILITY' or c.get('authority')!='none': raise ValueError('capability_provenance')
        if c.get('route') not in {'ctrl_wheel','native_scale'}: raise ValueError('route')
        by[c['route']]=c
    ref=(by.get('ctrl_wheel') or by.get('native_scale'))
    if ref is None:
        deps={'session_id':'S1','surface_id':'W1','geometry_epoch':7}
    else:
        deps=ref['dependencies']
        for c in by.values():
            if c['dependencies']!=deps: raise ValueError('dependency_divergence')
    hs=cur.get('target_handle_status')
    if hs not in HSTAT: raise ValueError('handle_status')
    return np.array(['scale' in dims,'center' in dims,'ctrl_wheel' in by,'native_scale' in by,cur.get('session_id')==deps['session_id'],cur.get('surface_id')==deps['surface_id'],cur.get('geometry_epoch')==deps['geometry_epoch'],hs=='LIVE'],dtype=np.float64)
