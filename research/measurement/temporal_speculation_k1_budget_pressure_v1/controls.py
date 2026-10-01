from contract import Case,current_only_select,temporal_select,admit,K

def main():
    cs=[]
    r=Case(0,(-3,-2,-1),1,'right');cs.append(('right',K==1 and current_only_select(r)==(1,) and temporal_select(r)==(1,)))
    l=Case(1,(3,2,1),-1,'left');cs.append(('left',current_only_select(l)==(1,) and temporal_select(l)==(-1,)))
    a=Case(2,(-1,1,0),1,'amb');cs.append(('amb',temporal_select(a)==(1,)))
    cs.append(('fresh_required',not admit((-1,),-1,authority=False)))
    cs.append(('expiry',not admit((-1,),-1,expired=True)))
    cs.append(('wrong',not admit((-1,),1)))
    cs.append(('forced_reversal_no_pre_admit',not admit((-1,),1)))
    assert all(x[1] for x in cs),cs
    print({'controls':len(cs),'passed':sum(x[1] for x in cs)})
if __name__=='__main__':main()
