from __future__ import annotations
import hashlib,json,random,time,uuid,sys
BASE='8888ce1b5642932c00c40668c557ff8341b93555'
V10_BLOB='341b3c01649943ddaad5f28431a792c4889cc36e'
SEED=100720260917001
N=100_000

def admission(owner_id,key,admitted,ack,deadline):
    if not isinstance(owner_id,str) or not owner_id: raise ValueError('owner')
    if not isinstance(key,str) or not key: raise ValueError('key')
    if any(type(x) is not int for x in (admitted,ack,deadline)): raise ValueError('clock type')
    if admitted<0 or ack<admitted or deadline<ack: raise ValueError('clock order')
    return dict(event='input_admission',key=key,admitted_ns=admitted,input_ack_ns=ack,valid_until_ns=deadline)

def controls():
    n=0
    a=admission('oa','F8',10,20,100); b=admission('ob','F8',10,20,100)
    assert a==b and 'owner_id' not in a; n+=2
    for variant in [admission('oa','W',10,20,100),admission('oa','F8',11,20,100),admission('oa','F8',10,21,100),admission('oa','F8',10,20,101)]:
        assert variant!=a; n+=1
    for x in [('', 'F8',10,20,100),('oa','',10,20,100),('oa','F8',20,10,100),('oa','F8',10,20,15)]:
        try: admission(*x)
        except ValueError: n+=1
        else: raise AssertionError(x)
    return n

def main():
    t0=time.perf_counter(); fixed=controls(); rng=random.Random(SEED); dig=hashlib.sha256(); mism=0; hidden_same=0
    for _ in range(N):
        oa=uuid.UUID(int=rng.getrandbits(128)).hex; ob=uuid.UUID(int=rng.getrandbits(128)).hex
        if oa==ob: hidden_same+=1
        key=rng.choice(['F8','W','A','SPACE','ENTER'])
        a=rng.randrange(0,1_000_000_000); b=a+rng.randrange(0,100_000); deadline=b+rng.randrange(0,10_000_000_000)
        ra=admission(oa,key,a,b,deadline); rb=admission(ob,key,a,b,deadline)
        if ra!=rb: mism+=1
        dig.update(json.dumps([oa,ob,ra],sort_keys=True,separators=(',',':')).encode())
    assert mism==0 and hidden_same==0
    print(json.dumps(dict(task='ORDINARY-ADMISSION-OWNER-IDENTITY-DISCRIMINATOR-20260917-001',base=BASE,v10_git_blob=V10_BLOB,
        decision='PASS_ORDINARY_ADMISSION_OWNER_ALIAS_SCOPED',seed=SEED,matched_pairs=N,hidden_owner_different=N,
        public_receipt_identical=N,public_mismatches=mism,controls_passed=fixed,formal=False,live_actions=0,
        digest=dig.hexdigest(),python=sys.version.split()[0],wall_s=time.perf_counter()-t0),indent=2,sort_keys=True))
if __name__=='__main__': main()
