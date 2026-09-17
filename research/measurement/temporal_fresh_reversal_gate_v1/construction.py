from model import decide
from oracle import expected
cases=[
    (1,1,'CONTINUE'),(-1,-1,'CONTINUE'),
    (1,-1,'YIELD_REVERSAL'),(-1,1,'YIELD_REVERSAL'),
    (1,0,'YIELD_UNKNOWN'),(1,None,'YIELD_UNKNOWN'),
    (0,1,'YIELD_UNKNOWN'),('1',1,'YIELD_UNKNOWN'),
]
for i,(h,f,want) in enumerate(cases):
    got=decide(h,f)
    assert got['disposition']==want, (i,got,want)
    assert got['disposition']==expected(h,f), (i,got,expected(h,f))
    assert got['authority']=='none' and got['task_input'] is False
print('PASS',len(cases))
