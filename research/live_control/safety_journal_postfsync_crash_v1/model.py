import hashlib, json, os, sqlite3

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()

def digest(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()

def make_receipt(case_id):
    core = {
        'schema':'cleanup-receipt-v1',
        'receipt_id':f'receipt-{case_id}',
        'case_id':case_id,
        'owner_instance':f'owner-{case_id}',
        'release_verified_ns':123456789000000 + sum(map(ord,case_id)),
        'authority':'none',
        'task_input_granted':False,
        'action_admission_eligible':False,
    }
    core['evidence_digest']=digest(core)
    return core

def init_ledger(path):
    con=sqlite3.connect(path)
    con.execute('pragma journal_mode=DELETE')
    con.execute('pragma synchronous=FULL')
    con.execute('create table if not exists published(receipt_id text primary key, digest text not null, payload text not null)')
    con.commit(); con.close()

def publish(path, receipt):
    payload=canonical(receipt).decode(); d=digest(receipt)
    con=sqlite3.connect(path, isolation_level=None)
    con.execute('pragma synchronous=FULL')
    con.execute('begin immediate')
    row=con.execute('select digest,payload from published where receipt_id=?',(receipt['receipt_id'],)).fetchone()
    if row:
        con.execute('rollback'); con.close()
        if row==(d,payload): return 'ALREADY_PUBLISHED'
        return 'RECEIPT_IDENTITY_CONFLICT'
    con.execute('insert into published values(?,?,?)',(receipt['receipt_id'],d,payload))
    con.execute('commit'); con.close(); return 'PUBLISHED'

def read_journal(path):
    if not os.path.exists(path): return []
    out=[]
    with open(path,'rb') as f:
        for line in f:
            if line.strip(): out.append(json.loads(line))
    return out

def append_fsync(path, receipt):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path,'ab',buffering=0) as f:
        data=canonical(receipt)+b'\n'
        f.write(data); os.fsync(f.fileno())
    dfd=os.open(os.path.dirname(path),os.O_DIRECTORY)
    try: os.fsync(dfd)
    finally: os.close(dfd)

def ledger_rows(path):
    con=sqlite3.connect(path); rows=con.execute('select receipt_id,digest,payload from published order by receipt_id').fetchall(); con.close(); return rows
