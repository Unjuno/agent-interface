from candidate_contract import Record,reduce_candidate as cand
from parent_contract import Record as PR, reduce_candidate as parent
from reference import R,reduce_ref
r=[Record('a',0,0,'s','t','x','CURRENTNESS_INVALIDATED'),Record('b',1,10,'s','t','x','FRAME'),Record('c',2,11,'s','t','x','FRAME')]
q=cand(r,20,5); z=reduce_ref([R(**x.__dict__) for x in r],20,5); assert q==z; assert q['critical_ids']==['a'] and q['delivered_ids']==['a']
old=[Record('a',0,15,'s','t','x','FOCUS_CHANGED'),Record('b',1,16,'s','t','x','FRAME')]
assert cand(old,20,10)==parent([PR(**x.__dict__) for x in old],20,10)
for rows in [[Record('a',0,0,'s','t','x','CURRENTNESS_INVALIDATED'),Record('a',1,0,'s','t','x','FRAME')],[Record('a',1,0,'s','t','x','FRAME'),Record('b',1,0,'s','t','x','FRAME')],[Record('a',0,0,'s','t','x','MADE_UP')]]:
 try: cand(rows,20,5); raise AssertionError
 except ValueError: pass
print('MECHANICS_PASS')
