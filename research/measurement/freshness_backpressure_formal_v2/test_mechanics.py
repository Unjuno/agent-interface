from contract import Record,reduce_candidate
from oracle_independent import reduce_oracle
rows=[Record('a',0,90,'s','t','r','FRAME'),Record('b',1,99,'s','t','r','STATUS'),Record('c',2,1,'s','t','r','LEASE_EXPIRED')]
a=reduce_candidate(rows,100,20);b=reduce_oracle(rows,100,20)
assert a==b
assert a['delivered_ids']==['b','c'] and a['critical_ids']==['c'] and a['coalesced_ids']==['a']
print('MECHANICS_PASS')
