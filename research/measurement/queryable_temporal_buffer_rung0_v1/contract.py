from __future__ import annotations
from dataclasses import dataclass
from math import ceil

STRATEGIES = frozenset({'UNIFORM','KEYFRAMES','CHANGES'})
ANCHORS = frozenset({'NOW','OBSERVATION','EVENT','ACTION'})

@dataclass(frozen=True)
class Observation:
    observation_id: str
    seq: int
    t_ns: int
    session: str
    surface: str
    width: int
    height: int
    bytes_size: int
    keyframe: bool = False
    changed: bool = True
    current_evidence: bool = False

@dataclass(frozen=True)
class Query:
    session: str
    surface: str
    anchor_kind: str
    anchor_ref: str | None
    before_ns: int
    after_ns: int
    max_frames: int
    max_bytes: int
    strategy: str
    roi: tuple[int,int,int,int] | None = None


def _sid(x): return isinstance(x,str) and bool(x.strip())

def _ival(x): return type(x) is int and x >= 0

def _merge_gap(gaps, lo, hi, reason, session, surface):
    if hi < lo: return
    if gaps and gaps[-1][2:] == (reason,session,surface) and lo <= gaps[-1][1] + 1:
        p = gaps[-1]; gaps[-1] = (p[0], max(p[1],hi), reason, session, surface)
    else:
        gaps.append((lo,hi,reason,session,surface))

class TemporalBuffer:
    def __init__(self, max_items:int, max_bytes:int, max_age_ns:int, max_gap_entries:int=64, max_anchor_refs:int=128):
        if not all(_ival(x) for x in (max_items,max_bytes,max_age_ns,max_gap_entries,max_anchor_refs)) or max_items == 0 or max_gap_entries == 0 or max_anchor_refs == 0:
            raise ValueError('config')
        self.max_items=max_items; self.max_bytes=max_bytes; self.max_age_ns=max_age_ns
        self.max_gap_entries=max_gap_entries; self.max_anchor_refs=max_anchor_refs
        self.items=[]; self.total_bytes=0; self.gaps=[]; self.gap_overflow=None; self.anchor_refs={}
        self._seen=set(); self._last_seq=None; self._last_t=None

    def bind_anchor(self, kind:str, ref:str, t_ns:int, session:str, surface:str):
        if kind not in ('EVENT','ACTION') or not all(_sid(x) for x in (ref,session,surface)) or not _ival(t_ns):
            raise ValueError('anchor')
        key=(kind,ref)
        if key in self.anchor_refs: raise ValueError('duplicate_anchor')
        self.anchor_refs[key]=(t_ns,session,surface)
        while len(self.anchor_refs)>self.max_anchor_refs:
            victim=min(self.anchor_refs, key=lambda k:(self.anchor_refs[k][0],k[0],k[1]))
            del self.anchor_refs[victim]

    def note_gap(self, start_ns:int, end_ns:int, reason:str, session:str, surface:str):
        if not _ival(start_ns) or not _ival(end_ns) or end_ns < start_ns or not all(_sid(x) for x in (reason,session,surface)):
            raise ValueError('gap')
        self._record_gap(start_ns,end_ns,reason,session,surface)

    def _record_gap(self, lo, hi, reason, session, surface):
        before=len(self.gaps)
        _merge_gap(self.gaps,lo,hi,reason,session,surface)
        if len(self.gaps)>self.max_gap_entries:
            self.gaps.pop()
            if self.gap_overflow is None:
                self.gap_overflow={'first_unretained_start_ns':lo,'last_unretained_end_ns':hi,'unretained_count':1}
            else:
                self.gap_overflow['last_unretained_end_ns']=max(self.gap_overflow['last_unretained_end_ns'],hi)
                self.gap_overflow['unretained_count']+=1

    def append(self, obs:Observation, now_ns:int):
        if not isinstance(obs,Observation) or not _ival(now_ns) or obs.t_ns > now_ns:
            raise ValueError('observation')
        if not all(_sid(x) for x in (obs.observation_id,obs.session,obs.surface)):
            raise ValueError('identity')
        if obs.observation_id in self._seen: raise ValueError('duplicate_observation')
        if type(obs.seq) is not int or obs.seq < 0 or not _ival(obs.t_ns): raise ValueError('time_or_seq')
        if any(type(x) is not int or x <= 0 for x in (obs.width,obs.height,obs.bytes_size)):
            raise ValueError('shape')
        if self._last_seq is not None and obs.seq <= self._last_seq: raise ValueError('nonmonotonic_seq')
        if self._last_t is not None and obs.t_ns < self._last_t: raise ValueError('nonmonotonic_time')
        self._seen.add(obs.observation_id); self._last_seq=obs.seq; self._last_t=obs.t_ns
        self.items.append(obs); self.total_bytes += obs.bytes_size
        self._evict(now_ns)

    def _evict(self, now_ns):
        while self.items and now_ns - self.items[0].t_ns > self.max_age_ns:
            x=self.items.pop(0); self.total_bytes-=x.bytes_size
            self._record_gap(x.t_ns,x.t_ns,'RETENTION_EXPIRED',x.session,x.surface)
        while self.items and (len(self.items)>self.max_items or self.total_bytes>self.max_bytes):
            x=self.items.pop(0); self.total_bytes-=x.bytes_size
            self._record_gap(x.t_ns,x.t_ns,'RETENTION_CAPACITY',x.session,x.surface)
        cutoff=max(0,now_ns-self.max_age_ns)
        for key,info in list(self.anchor_refs.items()):
            if info[0] < cutoff: del self.anchor_refs[key]

    def _resolve_anchor(self,q:Query, now_ns:int):
        if q.anchor_kind=='NOW': return now_ns
        if q.anchor_kind=='OBSERVATION':
            for x in self.items:
                if x.observation_id==q.anchor_ref and x.session==q.session and x.surface==q.surface: return x.t_ns
            raise KeyError('anchor_unavailable')
        info=self.anchor_refs.get((q.anchor_kind,q.anchor_ref))
        if info is None: raise KeyError('anchor_unavailable')
        t,sess,surf=info
        if sess!=q.session or surf!=q.surface: raise KeyError('anchor_scope')
        return t

    @staticmethod
    def _roi_size(obs, roi):
        if roi is None: return obs.bytes_size, None
        x,y,w,h=roi
        if any(type(v) is not int for v in roi) or x<0 or y<0 or w<=0 or h<=0 or x+w>obs.width or y+h>obs.height:
            raise ValueError('roi')
        n=max(1,ceil(obs.bytes_size*(w*h)/(obs.width*obs.height)))
        return n, {'x':x,'y':y,'width':w,'height':h,'source_width':obs.width,'source_height':obs.height}

    @staticmethod
    def _uniform_indices(n,m):
        if m<=0 or n<=0: return []
        if m>=n: return list(range(n))
        if m==1: return [n-1]
        return [round(i*(n-1)/(m-1)) for i in range(m)]

    def query(self,q:Query,now_ns:int):
        if not isinstance(q,Query) or not _ival(now_ns): raise ValueError('query')
        if self._last_t is not None and now_ns < self._last_t: raise ValueError('query_before_capture')
        self._evict(now_ns)
        if not all(_sid(x) for x in (q.session,q.surface)) or q.anchor_kind not in ANCHORS or q.strategy not in STRATEGIES:
            raise ValueError('query')
        if q.anchor_kind!='NOW' and not _sid(q.anchor_ref): raise ValueError('anchor_ref')
        if not all(_ival(x) for x in (q.before_ns,q.after_ns,q.max_frames,q.max_bytes)):
            raise ValueError('budget')
        anchor=self._resolve_anchor(q,now_ns)
        if anchor > now_ns: raise ValueError('future_anchor')
        lo=max(0,anchor-q.before_ns); hi=anchor+q.after_ns
        eligible=[x for x in self.items if x.session==q.session and x.surface==q.surface and lo<=x.t_ns<=hi]
        if q.strategy=='KEYFRAMES': pool=[x for x in eligible if x.keyframe]
        elif q.strategy=='CHANGES': pool=[x for x in eligible if x.changed]
        else: pool=eligible
        sizes=[]
        for x in pool: sizes.append(self._roi_size(x,q.roi)[0])
        selected_idx=[]
        for m in range(min(q.max_frames,len(pool)),0,-1):
            idx=self._uniform_indices(len(pool),m)
            if len(set(idx))!=len(idx): continue
            if sum(sizes[i] for i in idx) <= q.max_bytes:
                selected_idx=idx; break
        selected={i for i in selected_idx}
        items=[]
        for i,x in enumerate(pool):
            if i not in selected: continue
            n,transform=self._roi_size(x,q.roi)
            role='CURRENT_AT_QUERY' if x.current_evidence and x.t_ns==now_ns else 'HISTORICAL'
            items.append({'observation_id':x.observation_id,'captured_at_ns':x.t_ns,'age_at_query_ns':now_ns-x.t_ns,
                          'role':role,'payload_bytes':n,'spatial_transform':transform,'grants_input_authority':False})
        pool_ids={x.observation_id for x in pool}
        selected_ids={pool[i].observation_id for i in selected_idx}
        omitted_budget=[x.observation_id for x in pool if x.observation_id not in selected_ids]
        omitted_strategy=[x.observation_id for x in eligible if x.observation_id not in pool_ids]
        unavailable=[]
        for a,b,r,sess,surf in self.gaps:
            if (sess,surf)!=(q.session,q.surface): continue
            x=max(a,lo); y=min(b,hi)
            if x<=y: unavailable.append({'start_ns':x,'end_ns':y,'reason':r,'session':sess,'surface':surf})
        unavailable.sort(key=lambda z:(z['start_ns'],z['end_ns'],z['reason']))
        available_scope=[x for x in self.items if x.session==q.session and x.surface==q.surface]
        return {'anchor_ns':anchor,'window':[lo,hi],'items':items,'omitted_due_to_budget':omitted_budget,
                'omitted_by_strategy':omitted_strategy,'unavailable_intervals':unavailable,
                'oldest_available_at':available_scope[0].t_ns if available_scope else None,
                'newest_available_at':available_scope[-1].t_ns if available_scope else None,
                'coverage_complete':self.gap_overflow is None,
                'gap_metadata_overflow':dict(self.gap_overflow) if self.gap_overflow else None,
                'grants_input_authority':False}
