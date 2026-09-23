from candidate import RequestOriginBound,InstallTimeOnly,VALID,HARD,AMBIG
from oracle import new_state,apply,snapshot

def drive(ops):
    c=RequestOriginBound();o=new_state()
    for op in ops:
        if op['op']=='BEGIN':cr=c.begin(op['scope'],op['request_id'],op['planner_generation'],op.get('authority',False))
        elif op['op']=='INVALIDATE':cr=c.invalidate(op['scope'],op['invalidation_id'])
        elif op['op']=='INSTALL':cr=c.install(op['scope'],op['request_id'],op['response_id'],op['planner_generation'],op.get('authority',False))
        elif op['op']=='OBSERVE':cr=c.observe(op['scope'],op['regime'])
        else:cr=c.use(op['scope'])
        orr=apply(o,op);assert cr==orr,(cr,orr);assert c.snapshot()==snapshot(o)
    return cr
ops=[{'op':'BEGIN','scope':'A','request_id':'c-r1','planner_generation':7},{'op':'INVALIDATE','scope':'A','invalidation_id':'c-i1'},{'op':'INSTALL','scope':'A','request_id':'c-r1','response_id':'c-p1','planner_generation':65535},{'op':'OBSERVE','scope':'A','regime':VALID},{'op':'USE','scope':'A'}]
assert drive(ops)=={'status':'NO_CACHE','effect':False}
u=InstallTimeOnly();u.begin('A','c-u1',1);u.invalidate('A','c-ui1');u.install('A','c-u1','c-up1',2);u.observe('A',VALID);assert u.use('A')['effect'] is True
print('PASS_CONSTRUCTION')
