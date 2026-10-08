import copy,json
import model,oracle
# Disjoint negative-index construction; no formal index consumed.
ids=list(range(-20000,0))
mis=0;fixed=query=0;by={k:[0,0,0] for k in model.CLASSES}
for i in ids:
 a=model.one(i);o=oracle.one(i);mis+=int(a['class']!=o['class'] or a['fixed_covered']!=o['fixed_covered'] or a['query_covered']!=o['query_covered']);fixed+=a['fixed_covered'];query+=a['query_covered'];z=by[a['class']];z[0]+=1;z[1]+=a['fixed_covered'];z[2]+=a['query_covered']
assert mis==0
# Directed fail-closed validation controls.
frames,req=model.history(-1);sel=model.select_query(frames,req)
controls=[]
def chk(name,x,expect_not_ok=True):
 v=model.validate_selection(x,req);controls.append((name,v));assert (v!='OK')==expect_not_ok
x=copy.deepcopy(sel);x[-1]=copy.deepcopy(x[0]);chk('duplicate_id',x)
x=copy.deepcopy(sel);x[0]['scope']='scope-99';chk('cross_scope',x)
x=copy.deepcopy(sel);x[0]['age_ms']=-1;chk('future',x)
x=copy.deepcopy(sel);x[0]['bytes']=600;chk('byte_budget',x)
print(json.dumps({'construction_n':len(ids),'mismatch':mis,'fixed_rate':fixed/len(ids),'query_rate':query/len(ids),'delta_pp':(query-fixed)*100/len(ids),'by_class':by,'controls':controls},indent=2))
