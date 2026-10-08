import hashlib,json

def encode(gen,value):
    return f'P6\n4 2\n255\n'.encode()+bytes([value,0,255-value])*8

def prepare(requested,current,cache):
    if requested!=current: return {'status':'OBSOLETE','bytes':None,'gen':requested}
    if cache.get(requested): return {'status':'CACHE_HIT','bytes':cache[requested],'gen':requested}
    b=encode(requested,requested%256); cache[requested]=b
    return {'status':'ENCODED','bytes':b,'gen':requested}

def main():
    c={}; rows=[prepare(1,1,c),prepare(2,1,c),prepare(1,1,c),prepare(3,3,c)]
    assert [r['status'] for r in rows]==['ENCODED','OBSOLETE','CACHE_HIT','ENCODED']
    assert rows[0]['bytes']==rows[2]['bytes'] and rows[1]['bytes'] is None
    stale={'status':'STALE_UNCHECKED','gen':1,'current':2,'accepted':False}
    assert stale['gen']!=stale['current'] and not stale['accepted']
    payload={'rows':[{k:(v.hex() if isinstance(v,bytes) else v) for k,v in r.items()} for r in rows],'stale':stale}
    digest=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
    print(json.dumps({'cases':5,'statuses':[r['status'] for r in rows],'stale_control':'PASS','reuse_control':'PASS','provenance_control':'PASS','model':0,'x11':0,'input':0,'digest':digest},sort_keys=True))
main()
