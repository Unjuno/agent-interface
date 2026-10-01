from candidate import *
from oracle import reduce_oracle

def R(i,kind='FOCUS_CHANGED',s='A',target='T',stream='S',t=100): return Record(f'e{i}',i,t,s,target,stream,kind)
def eq(rows,now=100,maxage=50):
    a=reduce_composed(rows,now,maxage); b=reduce_oracle(rows,now,maxage); assert a==b; return a

def main():
    n=0
    a=eq([R(i) for i in range(1,4)]); assert len(a['retained_critical_ids'])==3 and not a['overflow_by_session']; n+=1
    a=eq([R(i) for i in range(1,5)]); assert len(a['retained_critical_ids'])==4 and not a['overflow_by_session']; n+=1
    a=eq([R(i) for i in range(1,6)]); assert a['overflow_by_session']['A']['first_unretained_seq']==5 and a['overflow_by_session']['A']['unretained_count']==1; n+=1
    a=eq([R(i) for i in range(1,11)]); assert a['retained_critical_ids']==['e1','e2','e3','e4'] and a['overflow_by_session']['A']['unretained_count']==6; n+=1
    rows=[R(i) for i in range(1,7)]+[R(7,'STATUS',t=90),R(8,'STATUS',t=95),R(9,'FRAME',target='U',t=96)]
    a=eq(rows); assert a['overflow_by_session']['A']['first_unretained_seq']==5 and a['overflow_by_session']['A']['unretained_count']==2 and 'e8' in a['delivered_ids'] and 'e7' in a['coalesced_ids']; n+=1
    rows=[R(1,s='A'),R(2,s='A'),R(3,s='A'),R(4,s='A'),R(5,s='A'),R(6,s='B'),R(7,s='B')]
    a=eq(rows); assert 'A' in a['overflow_by_session'] and 'B' not in a['overflow_by_session']; n+=1
    a=eq([R(1,'STATUS',t=10),R(2,'STATUS',t=90)]); assert a['stale_ids']==['e1'] and a['delivered_ids']==['e2']; n+=1
    rows=[R(1,'STATUS',t=90),R(2),R(3,'STATUS',t=91),R(4),R(5),R(6),R(7),R(8,'STATUS',t=99)]
    a=eq(rows); assert a['retained_critical_ids']==['e2','e4','e5','e6'] and a['overflow_by_session']['A']['first_unretained_seq']==7 and a['delivered_ids'][-1]=='e8'; n+=1
    bad=[
      ([Record('',1,1,'A','T','S','STATUS')],10,10),
      ([R(1),R(1)],100,10),
      ([R(2),R(1)],100,10),
      ([Record('x',1,101,'A','T','S','STATUS')],100,10),
      ([Record('x',1,1,'A','T','S','BOGUS')],100,10),
    ]
    for rows,now,age in bad:
        try: reduce_composed(rows,now,age)
        except ValueError: n+=1
        else: raise AssertionError('malformed accepted')
    print({'controls_passed':n})
if __name__=='__main__': main()
