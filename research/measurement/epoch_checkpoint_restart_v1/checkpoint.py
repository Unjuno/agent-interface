import hashlib,json,sqlite3
from dataclasses import asdict
from parent_candidate import Manager,SessionState,Record
SCHEMA=1

def _canon(x): return json.dumps(x,sort_keys=True,separators=(',',':'))
def _rec(r): return asdict(r)
def _record(d): return Record(**d)

def export_manager(m):
    sessions={}
    for name in sorted(m.sessions):
        st=m.sessions[name]
        sessions[name]={
            'session':st.session,'epoch':st.epoch,'latest_seq':st.latest_seq,
            'retained_critical':[_rec(r) for r in st.retained_critical],
            'active_overflow':st.overflow,
            'latest_state':[{'target':k[0],'stream':k[1],'record':_rec(v)} for k,v in sorted(st.latest_state.items())],
            'historical_gaps':st.historical_gaps,
            'accepted_resync':None if st.accepted_resync is None else list(st.accepted_resync[:-1])+[list(st.accepted_resync[-1])],
        }
    return {'schema':SCHEMA,'sessions':sessions,'grants_input_authority':False}

def import_manager(obj):
    if not isinstance(obj,dict) or obj.get('schema')!=SCHEMA or obj.get('grants_input_authority') is not False or not isinstance(obj.get('sessions'),dict):
        raise ValueError('checkpoint schema')
    m=Manager()
    for name,d in obj['sessions'].items():
        if d.get('session')!=name: raise ValueError('session identity')
        st=SessionState(name)
        if type(d.get('epoch')) is not int or d['epoch']<1 or type(d.get('latest_seq')) is not int: raise ValueError('epoch/seq')
        st.epoch=d['epoch']; st.latest_seq=d['latest_seq']
        st.retained_critical=[_record(r) for r in d.get('retained_critical',[])]
        st.overflow=None if d.get('active_overflow') is None else dict(d['active_overflow'])
        st.latest_state={}
        for x in d.get('latest_state',[]): st.latest_state[(x['target'],x['stream'])]=_record(x['record'])
        st.historical_gaps=[dict(x) for x in d.get('historical_gaps',[])]
        ar=d.get('accepted_resync')
        if ar is None: st.accepted_resync=None
        else:
            if not isinstance(ar,list) or len(ar)!=7 or not isinstance(ar[-1],list): raise ValueError('accepted_resync')
            st.accepted_resync=tuple(ar[:-1])+(tuple(ar[-1]),)
        m.sessions[name]=st
    return m

def setup_db(path):
    c=sqlite3.connect(path); c.execute('PRAGMA journal_mode=DELETE'); c.execute('PRAGMA synchronous=FULL')
    c.execute('CREATE TABLE IF NOT EXISTS checkpoints(case_id TEXT PRIMARY KEY,schema INTEGER NOT NULL,payload TEXT NOT NULL,sha256 TEXT NOT NULL,expected_view TEXT NOT NULL,current_only TEXT NOT NULL)')
    c.commit(); return c

def store(c,case_id,m,expected_view):
    obj=export_manager(m); payload=_canon(obj); digest=hashlib.sha256(payload.encode()).hexdigest()
    current_only=_canon({'sessions':{name:{'latest_seq':view['latest_seq'],'latest_state_ids':view['latest_state_ids']} for name,view in sorted(expected_view.items())},'grants_input_authority':False})
    c.execute('INSERT INTO checkpoints VALUES(?,?,?,?,?,?)',(case_id,SCHEMA,payload,digest,_canon(expected_view),current_only))

def restore_row(row):
    case_id,schema,payload,digest,expected,current_only=row
    if schema!=SCHEMA: raise ValueError('stored schema')
    if hashlib.sha256(payload.encode()).hexdigest()!=digest: raise ValueError('checkpoint digest')
    obj=json.loads(payload); m=import_manager(obj)
    return case_id,m,json.loads(expected),json.loads(current_only)
