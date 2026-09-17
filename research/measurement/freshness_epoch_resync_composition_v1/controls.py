from candidate import *

def r(i,kind='FOCUS_CHANGED',s='A',t=900000,target='T',stream='X'):return Record(f'{s}-e{i}',i,t,s,target,stream,kind)
def overflow_mgr():
    m=Manager()
    for i in range(1,7):m.append(r(i),1_000_000)
    return m

def main():
    n=0
    m=overflow_mgr(); a=m.get('A'); oid=a.overflow_identity(); before=a.view(1_000_000)
    s=Snapshot('snap-A',6,1_400_000,'A','T','X',oid); assert m.resync('A',s,1_400_000)=='RESYNC_ACCEPTED'; v=a.view(1_400_000); assert v['epoch']==2 and v['historical_gaps'][0]['unretained_count']==2 and v['active_overflow'] is None;n+=1
    oldgap=dict(v['historical_gaps'][0]); m.append(Record('A-state7',7,1_500_000,'A','T','X','STATUS'),1_500_000); m.append(Record('A-state8',8,1_600_000,'A','T','X','STATUS'),1_600_000); v=a.view(1_600_000); assert v['latest_state_ids']['T|X']=='A-state8' and v['historical_gaps'][0]==oldgap;n+=1
    for i in range(9,14):m.append(Record(f'A-c{i}',i,1_600_000,'A','T','X','EFFECT_VERIFIED'),1_600_000)
    v=a.view(1_600_000); assert v['active_overflow']['first_unretained_seq']==13 and v['historical_gaps'][0]==oldgap;n+=1
    m=overflow_mgr(); a=m.get('A'); oid=a.overflow_identity(); snap=Snapshot('s',5,1_400_000,'A','T','X',oid); pre=a.view(1_400_000); assert m.resync('A',snap,1_400_000)=='STALE_RESYNC_SNAPSHOT' and a.view(1_400_000)==pre;n+=1
    m=overflow_mgr(); a=m.get('A'); oid=a.overflow_identity(); bad=tuple(list(oid[:-1])+[999]); pre=a.view(1_400_000); assert m.resync('A',Snapshot('s',6,1_400_000,'A','T','X',bad),1_400_000)=='RESYNC_OVERFLOW_MISMATCH' and a.view(1_400_000)==pre;n+=1
    m=overflow_mgr(); a=m.get('A'); oid=a.overflow_identity(); pre=a.view(1_400_000); assert m.resync('A',Snapshot('s',6,1_400_000,'B','T','X',oid),1_400_000)=='RESYNC_SCOPE_MISMATCH' and a.view(1_400_000)==pre;n+=1
    m=overflow_mgr(); a=m.get('A'); oid=a.overflow_identity(); s=Snapshot('s',6,1_400_000,'A','T','X',oid); assert m.resync('A',s,1_400_000)=='RESYNC_ACCEPTED'; pre=a.view(1_400_000); assert m.resync('A',s,1_400_000)=='ALREADY_RESYNCED_SELF' and a.view(1_400_000)==pre;n+=1
    m=Manager(); [m.append(r(i),1_000_000) for i in range(1,4)]; a=m.get('A'); assert m.resync('A',Snapshot('s',3,1_400_000,'A','T','X',None),1_400_000)=='RESYNC_NOT_REQUIRED';n+=1
    m=overflow_mgr(); [m.append(r(i,s='B'),1_000_000) for i in range(1,3)]; bpre=m.get('B').view(1_400_000); a=m.get('A'); s=Snapshot('s',6,1_400_000,'A','T','X',a.overflow_identity()); m.resync('A',s,1_400_000); assert m.get('B').view(1_400_000)==bpre;n+=1
    # Naive same-epoch clear negative: gap disappears by construction.
    m=overflow_mgr(); a=m.get('A'); assert a.overflow is not None; a.overflow=None; assert a.view(1_400_000)['coverage_complete'] and not a.view(1_400_000)['historical_gaps'];n+=1
    print({'controls_passed':n})
if __name__=='__main__':main()
