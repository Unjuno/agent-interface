from candidate import Record,Snapshot,CRITICAL,CAPACITY,MAX_AGE_NS

def reduce_epoch(records,now_ns):
    retained=[]; overflow=None; latest={}; latest_seq=-1
    for r in records:
        latest_seq=max(latest_seq,r.seq)
        if r.kind in CRITICAL:
            if len(retained)<CAPACITY: retained.append(r)
            elif overflow is None: overflow={'status':'RESYNC_REQUIRED','first_unretained_event_id':r.event_id,'first_unretained_seq':r.seq,'first_unretained_kind':r.kind,'unretained_count':1}
            else: overflow['unretained_count']+=1
        elif now_ns-r.t_ns<=MAX_AGE_NS: latest[(r.target,r.stream)]=r
    return retained,overflow,latest,latest_seq

def reconstruct(pre_by_session,snapshot,post_by_session,final_now):
    out={}
    all_sessions=sorted(set(pre_by_session)|set(post_by_session)|{snapshot.session})
    for session in all_sessions:
        pre=pre_by_session.get(session,[]); post=post_by_session.get(session,[])
        pre_ret,pre_ov,pre_latest,pre_seq=reduce_epoch(pre,1_000_000)
        if session==snapshot.session:
            if pre_ov is None: raise AssertionError('primary requires overflow')
            hist=dict(pre_ov); hist.update(status='HISTORICAL_GAP_RETAINED',epoch=1,source_epoch=1)
            snaprec=Record(snapshot.snapshot_id,snapshot.seq,snapshot.t_ns,session,snapshot.target,snapshot.stream,'STATUS')
            cur=[snaprec]+post
            ret,ov,latest,seq=reduce_epoch(cur,final_now)
            out[session]={'session':session,'epoch':2,'latest_seq':seq,'retained_critical_ids':[r.event_id for r in ret],
                'active_overflow':None if ov is None else dict(ov,epoch=2),'historical_gaps':[hist],
                'latest_state_ids':{f'{t}|{st}':r.event_id for (t,st),r in latest.items() if final_now-r.t_ns<=MAX_AGE_NS},
                'coverage_complete':ov is None,'grants_input_authority':False}
        else:
            cur=pre+post; ret,ov,latest,seq=reduce_epoch(cur,final_now)
            out[session]={'session':session,'epoch':1,'latest_seq':seq,'retained_critical_ids':[r.event_id for r in ret],
                'active_overflow':None if ov is None else dict(ov,epoch=1),'historical_gaps':[],
                'latest_state_ids':{f'{t}|{st}':r.event_id for (t,st),r in latest.items() if final_now-r.t_ns<=MAX_AGE_NS},
                'coverage_complete':ov is None,'grants_input_authority':False}
    return out
