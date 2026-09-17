from candidate import Actuation,Effect,clock_bound
from oracle_independent import classify
A=Actuation('a',10,14,'mono','ep1')
rows=[
 (Effect('e','a',20,True,True,'mono','ep1'),'useful_bound'),
 (Effect('e','a',20,True,True,'other','ep1'),'temporal_clock_mismatch'),
 (Effect('e','a',20,True,True,None,'ep1'),'temporal_clock_unknown'),
 (Effect('e','a',12,True,False,'mono','ep1'),'temporal_ambiguous'),
 (Effect('e',None,20,True,True,'other','ep2'),'useful_unbound')]
for e,want in rows:
 assert clock_bound(e,[A])==classify(e,[A])==want
print('MECHANICS_PASS')
