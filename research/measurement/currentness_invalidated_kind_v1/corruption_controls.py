from candidate_contract import Record,reduce_candidate
cs=[]
def rej(name,rows):
 try: reduce_candidate(rows,20,5); ok=False
 except ValueError: ok=True
 cs.append({'name':name,'rejected':ok})
rej('duplicate_id',[Record('a',0,0,'s','t','x','CURRENTNESS_INVALIDATED'),Record('a',1,0,'s','t','x','FRAME')]);rej('nonmonotonic',[Record('a',1,0,'s','t','x','FRAME'),Record('b',1,0,'s','t','x','CURRENTNESS_INVALIDATED')]);rej('unknown_kind',[Record('a',0,0,'s','t','x','CURRENTNESS_CHANGED')])
r=reduce_candidate([Record('a',0,0,'s','t','x','CURRENTNESS_INVALIDATED')],20,0); cs.append({'name':'stale_new_kind_retained','rejected':r['delivered_ids']==['a'] and r['critical_ids']==['a']}); cs.append({'name':'no_authority','rejected':r['grants_input_authority'] is False}); assert all(x['rejected'] for x in cs); print('CORRUPTION_PASS',len(cs))
