import hashlib, struct, time
CORE = struct.Struct('<16sQQBQQB')
DIGEST = 16
RECORD_SIZE = CORE.size + DIGEST
REG_VALID=0; REG_HARD=1; REG_AMBIG=2
READY=1; NONREADY=0
SCOPE=b'scope-A'.ljust(16,b'\0')
GENERATION=7
MAX_AGE_NS=50_000_000

def encode_record(seq, regime, readiness_generation, readiness_state, published_ns=None, scope=SCOPE, generation=GENERATION):
    if published_ns is None: published_ns=time.perf_counter_ns()
    core=CORE.pack(scope,generation,seq,regime,published_ns,readiness_generation,readiness_state)
    return core+hashlib.blake2b(core,digest_size=DIGEST).digest()

def decode_record(data):
    if type(data) is not bytes or len(data)!=RECORD_SIZE: raise ValueError('record_size')
    core,digest=data[:-DIGEST],data[-DIGEST:]
    if hashlib.blake2b(core,digest_size=DIGEST).digest()!=digest: raise ValueError('checksum')
    scope,generation,seq,regime,published_ns,ready_gen,ready_state=CORE.unpack(core)
    if regime not in (REG_VALID,REG_HARD,REG_AMBIG): raise ValueError('regime')
    if ready_state not in (READY,NONREADY): raise ValueError('readiness_state')
    return {'scope':scope,'generation':generation,'seq':seq,'regime':regime,'published_ns':published_ns,'readiness_generation':ready_gen,'readiness_state':ready_state}
