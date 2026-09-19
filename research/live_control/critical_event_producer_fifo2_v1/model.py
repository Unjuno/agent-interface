import sqlite3, json, hashlib

def digest(payload): return hashlib.sha256(payload.encode()).hexdigest()

def init_db(path):
    c=sqlite3.connect(path)
    c.executescript('''
    PRAGMA journal_mode=DELETE; PRAGMA synchronous=FULL;
    CREATE TABLE consumer(seq INTEGER PRIMARY KEY, event_id TEXT UNIQUE, payload_sha TEXT NOT NULL);
    CREATE TABLE pending(pos INTEGER PRIMARY KEY, seq INTEGER UNIQUE, event_id TEXT UNIQUE, payload_sha TEXT NOT NULL);
    CREATE TABLE ack(last_seq INTEGER NOT NULL, prefix_sha TEXT NOT NULL);
    INSERT INTO ack VALUES(0,'');
    ''')
    for i in (1,2,3): c.execute('INSERT INTO consumer VALUES(?,?,?)',(i,f'E{i}',digest(f'p{i}')))
    c.commit(); c.close()

def consumer_submit(c, seq, eid, sha):
    row=c.execute('SELECT seq,payload_sha FROM consumer WHERE event_id=?',(eid,)).fetchone()
    if row: return 'EVENT_DUPLICATE' if row==(seq,sha) else 'EVENT_CONFLICT'
    if c.execute('SELECT COUNT(*) FROM consumer').fetchone()[0] >= 3: return 'EVENT_BACKPRESSURE'
    mx=c.execute('SELECT COALESCE(MAX(seq),0) FROM consumer').fetchone()[0]
    if seq <= mx: return 'EVENT_NON_MONOTONIC'
    c.execute('INSERT INTO consumer VALUES(?,?,?)',(seq,eid,sha)); return 'EVENT_ACCEPTED'

def producer_offer(c, cap, seq, eid, sha):
    rows=c.execute('SELECT pos,seq,event_id,payload_sha FROM pending ORDER BY pos').fetchall()
    for _,s,e,h in rows:
        if e==eid or s==seq:
            return 'PENDING_ALREADY' if (s,e,h)==(seq,eid,sha) else 'PENDING_EVENT_CONFLICT'
    if len(rows)>=cap: return 'PRODUCER_PENDING_FULL'
    pos=(rows[-1][0]+1) if rows else 1
    c.execute('INSERT INTO pending VALUES(?,?,?,?)',(pos,seq,eid,sha)); return 'PENDING_RETAINED'

def pending_retry(c, seq, eid, sha):
    rows=c.execute('SELECT pos,seq,event_id,payload_sha FROM pending ORDER BY pos').fetchall()
    if not rows: return 'NO_PENDING'
    p,s,e,h=rows[0]
    if (s,e,h)!=(seq,eid,sha):
        for _,ss,ee,hh in rows:
            if (ss,ee)==(seq,eid): return 'PENDING_EVENT_CONFLICT' if hh!=sha else 'PENDING_HEAD_REQUIRED'
        return 'PENDING_HEAD_REQUIRED'
    st=consumer_submit(c,seq,eid,sha)
    if st=='EVENT_ACCEPTED':
        c.execute('DELETE FROM pending WHERE pos=?',(p,))
        rest=c.execute('SELECT pos FROM pending ORDER BY pos').fetchall()
        for new,(old,) in enumerate(rest,1):
            if new!=old: c.execute('UPDATE pending SET pos=? WHERE pos=?',(1000+new,old))
        c.execute('UPDATE pending SET pos=pos-1000 WHERE pos>=1000')
    return st

def ack_digest(c, through):
    rows=c.execute('SELECT seq,event_id,payload_sha FROM consumer WHERE seq<=? ORDER BY seq',(through,)).fetchall()
    return hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()

def ack_through(c, through, supplied_sha):
    last,prefix=c.execute('SELECT last_seq,prefix_sha FROM ack').fetchone()
    if through==last: return 'ACK_ALREADY_APPLIED' if supplied_sha==prefix else 'ACK_RECEIPT_CONFLICT'
    sha=ack_digest(c,through)
    if supplied_sha!=sha: return 'ACK_RECEIPT_CONFLICT'
    if through<last: return 'ACK_NON_MONOTONIC'
    c.execute('DELETE FROM consumer WHERE seq<=?',(through,)); c.execute('UPDATE ack SET last_seq=?,prefix_sha=?',(through,sha)); return 'ACK_APPLIED'

def snap(path):
    c=sqlite3.connect(path)
    out={'consumer':[r[1] for r in c.execute('SELECT seq,event_id,payload_sha FROM consumer ORDER BY seq')],
         'pending':[r[2] for r in c.execute('SELECT pos,seq,event_id,payload_sha FROM pending ORDER BY pos')],
         'ack':c.execute('SELECT last_seq,prefix_sha FROM ack').fetchone()[0]}
    c.close(); return out
