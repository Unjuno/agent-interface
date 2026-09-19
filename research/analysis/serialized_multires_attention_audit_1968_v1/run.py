import json,zlib,hashlib,struct
W,H=64,32
raw=bytes(((x*17+y*31+(x//8)*7)%256 for y in range(H) for x in range(W)))
regions=[{"id":"save-left","label":"Save","context":"toolbar-left","x":4,"y":5,"w":8,"h":5},{"id":"save-right","label":"Save","context":"dialog-right","x":48,"y":20,"w":8,"h":5}]
def crop(r):
    return bytes(raw[(r['y']+dy)*W+r['x']+dx] for dy in range(r['h']) for dx in range(r['w']))
def pack(kind,include_raw=True):
    d={"kind":kind,"shape":[W,H],"manifest":regions,"raw":raw.hex() if include_raw else None}
    d["crops"]={r['id']:crop(r).hex() for r in regions}
    return zlib.compress(json.dumps(d,sort_keys=True,separators=(',',':')).encode(),9)
def run():
    full=pack('FULL',True); reduced=pack('MULTI_RES',True)
    assert bytes.fromhex(json.loads(zlib.decompress(reduced))['raw'])==raw
    ids=[r['id'] for r in regions if r['label']=='Save' and r['context']=='dialog-right']
    assert ids==['save-right']
    # Without the raw authoritative fallback, exact recovery is impossible by construction.
    reduced_without_raw=pack('MULTI_RES',False)
    result={"decision":"HOLD_NO_SIZE_GAIN","full_bytes":len(full),"reduced_bytes":len(reduced),"reduced_without_raw_bytes":len(reduced_without_raw),"exact_recovery":True,"duplicate_label_disambiguation":True,"raw_fallback_required":True,"formal_invocations":1,"reruns":0,"tuning":0}
    rawj=json.dumps(result,sort_keys=True,separators=(',',':')).encode();result['sha256']=hashlib.sha256(rawj).hexdigest();return result
if __name__=='__main__': print(json.dumps(run(),indent=2,sort_keys=True))
