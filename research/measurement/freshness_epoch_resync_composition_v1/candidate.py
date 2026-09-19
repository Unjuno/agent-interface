from dataclasses import dataclass,asdict
CAPACITY=4
MAX_AGE_NS=500_000
CRITICAL=frozenset({'FOCUS_CHANGED','AUTHORITY_REVOKED','LEASE_EXPIRED','ACTION_REJECTED','SAFETY_VIOLATION','EFFECT_VERIFIED'})
STATE_KINDS=frozenset({'FRAME','STATUS','POINTER_STATE','QUEUE_HEALTH'})
ALL_KINDS=CRITICAL|STATE_KINDS

@dataclass(frozen=True)
class Record:
    event_id:str; seq:int; t_ns:int; session:str; target:str; stream:str; kind:str
@dataclass(frozen=True)
class Snapshot:
    snapshot_id:str; seq:int; t_ns:int; session:str; target:str; stream:str; expected_overflow:tuple

def _id(x): return isinstance(x,str) and bool(x.strip())
class SessionState:
    def __init__(self,session):
        self.session=session; self.epoch=1; self.latest_seq=-1; self.retained_critical=[]; self.overflow=None
        self.latest_state={}; self.historical_gaps=[]; self.accepted_resync=None
    def append(self,r,now_ns):
        if not isinstance(r,Record) or r.session!=self.session: raise ValueError('scope')
        if not _id(r.event_id) or not all(_id(x) for x in (r.session,r.target,r.stream)): raise ValueError('identity')
        if r.kind not in ALL_KINDS or type(r.seq) is not int or type(r.t_ns) is not int or r.seq<=self.latest_seq or r.t_ns<0 or r.t_ns>now_ns: raise ValueError('record')
        self.latest_seq=r.seq
        if r.kind in CRITICAL:
            if len(self.retained_critical)<CAPACITY: self.retained_critical.append(r)
            elif self.overflow is None:
                self.overflow={'status':'RESYNC_REQUIRED','epoch':self.epoch,'first_unretained_event_id':r.event_id,
                    'first_unretained_seq':r.seq,'first_unretained_kind':r.kind,'unretained_count':1}
            else: self.overflow['unretained_count']+=1
        elif now_ns-r.t_ns<=MAX_AGE_NS:
            self.latest_state[(r.target,r.stream)]=r
    def overflow_identity(self):
        if self.overflow is None:return None
        o=self.overflow
        return (o['epoch'],o['first_unretained_event_id'],o['first_unretained_seq'],o['first_unretained_kind'],o['unretained_count'])
    def resync(self,s,now_ns):
        if not isinstance(s,Snapshot): raise ValueError('snapshot')
        req=(s.snapshot_id,s.seq,s.t_ns,s.session,s.target,s.stream,s.expected_overflow)
        if self.accepted_resync==req: return 'ALREADY_RESYNCED_SELF'
        if s.session!=self.session:return 'RESYNC_SCOPE_MISMATCH'
        if self.overflow is None:return 'RESYNC_NOT_REQUIRED'
        if s.expected_overflow!=self.overflow_identity():return 'RESYNC_OVERFLOW_MISMATCH'
        if not _id(s.snapshot_id) or not all(_id(x) for x in (s.session,s.target,s.stream)) or type(s.seq) is not int or type(s.t_ns) is not int or s.seq<self.latest_seq or s.t_ns<0 or s.t_ns>now_ns:
            return 'STALE_RESYNC_SNAPSHOT'
        old=dict(self.overflow); old['status']='HISTORICAL_GAP_RETAINED'; old['source_epoch']=self.epoch
        self.historical_gaps.append(old); self.epoch+=1; self.latest_seq=s.seq
        self.retained_critical=[]; self.overflow=None; self.latest_state={}
        self.latest_state[(s.target,s.stream)]=Record(s.snapshot_id,s.seq,s.t_ns,s.session,s.target,s.stream,'STATUS')
        self.accepted_resync=req
        return 'RESYNC_ACCEPTED'
    def view(self,now_ns):
        latest={f'{t}|{st}':r.event_id for (t,st),r in self.latest_state.items() if now_ns-r.t_ns<=MAX_AGE_NS}
        return {'session':self.session,'epoch':self.epoch,'latest_seq':self.latest_seq,
            'retained_critical_ids':[r.event_id for r in self.retained_critical],
            'active_overflow':None if self.overflow is None else dict(self.overflow),
            'historical_gaps':[dict(x) for x in self.historical_gaps],
            'latest_state_ids':latest,'coverage_complete':self.overflow is None,'grants_input_authority':False}
class Manager:
    def __init__(self):self.sessions={}
    def get(self,s):
        if s not in self.sessions:self.sessions[s]=SessionState(s)
        return self.sessions[s]
    def append(self,r,now_ns):self.get(r.session).append(r,now_ns)
    def resync(self,target_session,s,now_ns):return self.get(target_session).resync(s,now_ns)
    def view(self,now_ns):return {s:self.sessions[s].view(now_ns) for s in sorted(self.sessions)}
