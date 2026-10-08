import hashlib, random, struct, time
CORE = struct.Struct('<16sQQBQ')
DIGEST = 16
RECORD_SIZE = CORE.size + DIGEST
REG_VALID=0; REG_HARD=1; REG_AMBIG=2
REGIMES={REG_VALID:'VALID_CONTINUATION',REG_HARD:'HARD_INVALIDATION',REG_AMBIG:'AMBIGUOUS_BOUNDARY'}
SCOPE=b'scope-A'.ljust(16,b'\0')
GENERATION=7
MAX_AGE_NS=50_000_000

def encode_record(seq, regime, published_ns=None, scope=SCOPE, generation=GENERATION):
    if published_ns is None: published_ns=time.perf_counter_ns()
    core=CORE.pack(scope,generation,seq,regime,published_ns)
    return core+hashlib.blake2b(core,digest_size=DIGEST).digest()

def decode_record(data):
    if type(data) is not bytes or len(data)!=RECORD_SIZE: raise ValueError('record_size')
    core,digest=data[:-DIGEST],data[-DIGEST:]
    if hashlib.blake2b(core,digest_size=DIGEST).digest()!=digest: raise ValueError('checksum')
    scope,generation,seq,regime,published_ns=CORE.unpack(core)
    if regime not in REGIMES: raise ValueError('regime')
    return {'scope':scope,'generation':generation,'seq':seq,'regime':regime,'published_ns':published_ns}

def schedule(seed,count):
    r=random.Random(seed); out=[]
    # frozen 80/10/10 proportions approximately; deterministic fresh corpus
    for _ in range(count):
        x=r.randrange(10); out.append(REG_HARD if x==0 else REG_AMBIG if x==1 else REG_VALID)
    return out
