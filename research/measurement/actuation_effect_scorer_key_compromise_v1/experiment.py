from __future__ import annotations
import hashlib,hmac,json,sys
KEY=b'\x55'*32
WRONG=b'\x66'*32
FIELDS=('version','key_id','nonce','session_id','actuation_id','target_id','effect_kind','effect_ns','effect_digest')

def canonical(r):
    return '|'.join(str(r[k]) for k in FIELDS).encode()

def base(i):
    return {'version':1,'key_id':'score-current','nonce':f'n{i}','session_id':f's{i%101}','actuation_id':f'act{i}','target_id':f't{i%397}','effect_kind':('VALUE','VISIBILITY','SELECTION','PROGRESS')[i%4],'effect_ns':3_000_000_000+i*10000,'effect_digest':hashlib.sha256(f'effect:{i}'.encode()).hexdigest()}

def sign(r,key=KEY):
    x=dict(r); x['mac']=hmac.new(key,canonical(x),hashlib.sha256).hexdigest(); return x

def verify(r):
    if not isinstance(r,dict): return False
    if r.get('version')!=1 or r.get('key_id')!='score-current': return False
    for k in FIELDS:
        if k not in r: return False
    mac=r.get('mac')
    if not isinstance(mac,str) or len(mac)!=64: return False
    return hmac.compare_digest(mac,hmac.new(KEY,canonical(r),hashlib.sha256).hexdigest())

def pair(i):
    rec=sign(base(i))
    # Hidden producer provenance is deliberately not verifier-visible.
    trusted={'producer':'TRUSTED_SCORER','receipt':json.loads(json.dumps(rec,sort_keys=True))}
    compromised={'producer':'COMPROMISED_SCORER','receipt':json.loads(json.dumps(rec,sort_keys=True))}
    wrong=sign(base(i+10_000_000),WRONG); wrong['key_id']='score-current'
    altered=sign(base(i+20_000_000)); altered['actuation_id']+='x'
    return trusted,compromised,wrong,altered

def visible(r):
    return json.dumps(r,sort_keys=True,separators=(',',':')).encode()

def run_batch(start,count):
    legit=comp=ident=wrong_rej=alter_rej=auth=0
    h=hashlib.sha256()
    for i in range(start,start+count):
        t,c,w,a=pair(i)
        tv=visible(t['receipt']); cv=visible(c['receipt'])
        legit+=int(verify(t['receipt'])); comp+=int(verify(c['receipt'])); ident+=int(tv==cv)
        wrong_rej+=int(not verify(w)); alter_rej+=int(not verify(a))
        h.update(tv);h.update(b'\n');h.update(cv);h.update(b'\n')
    return {'start':start,'count':count,'end':start+count,'legit_accept':legit,'compromised_accept':comp,'visible_byte_identical_pairs':ident,'wrong_key_reject':wrong_rej,'altered_after_sign_reject':alter_rej,'authority_promotions':auth,'pair_sha256':h.hexdigest()}

def construction():
    r=run_batch(900000,128)
    assert r['legit_accept']==r['compromised_accept']==r['visible_byte_identical_pairs']==128
    assert r['wrong_key_reject']==r['altered_after_sign_reject']==128 and r['authority_promotions']==0
    return r
if __name__=='__main__':
    if len(sys.argv)==1: print(json.dumps(construction(),sort_keys=True))
    else: print(json.dumps(run_batch(int(sys.argv[1]),int(sys.argv[2])),sort_keys=True))
