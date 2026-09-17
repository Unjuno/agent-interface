import copy,json,tempfile,subprocess,sys
from pathlib import Path
corpus=json.load(open('CORPUS.json')); result=json.load(open('RESULT.json'))
controls=[]
def check(name,rows,res):
    with tempfile.TemporaryDirectory() as d:
        cp=Path(d)/'c.json'; rp=Path(d)/'r.json'; cp.write_text(json.dumps(rows)); rp.write_text(json.dumps(res))
        q=subprocess.run([sys.executable,'independent_audit.py',str(cp),str(rp)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        controls.append({'name':name,'rejected':q.returncode!=0})
# leakage
x=copy.deepcopy(corpus); x[0]['candidate_input']['teacher_label']='CLICK'; check('visible_leakage',x,result)
# alias same visible input with changed acceptable/facts
x=copy.deepcopy(corpus); x[1]['candidate_input']=copy.deepcopy(x[0]['candidate_input']); check('alias',x,result)
# split leakage
x=copy.deepcopy(corpus); x[-1]['scenario_unit_id']=x[0]['scenario_unit_id']; x[-1]['split_group_id']=x[0]['split_group_id']; check('split_leakage',x,result)
# oracle mutation
x=copy.deepcopy(corpus); x[2]['acceptable']=[{'op':'NO_LOCAL_ACTION','reason':'ALREADY_SATISFIED'}]; check('oracle_mutation',x,result)
# digest/result mutation
r=copy.deepcopy(result); r['corpus_digest_sha256']='0'*64; check('digest_mutation',corpus,r)
print(json.dumps({'controls':controls,'all_rejected':all(c['rejected'] for c in controls)},sort_keys=True)); assert all(c['rejected'] for c in controls)
