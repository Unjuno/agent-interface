import copy,json
import audit
r=json.load(open('FORMAL_RESULT.json'))
expected=audit.formal.run()
audit.formal.run=lambda: expected
muts=[]
def mut(path,val):
    x=copy.deepcopy(r); cur=x
    for p in path[:-1]: cur=cur[p]
    cur[path[-1]]=val; return x
muts=[
 ('digest',mut(['row_digest_sha256'],'0'*64)),
 ('choice',mut(['choices','INDEX_LOG'],0)),
 ('escape',mut(['errors','index_bound_escape'],1)),
 ('unsupported',mut(['unsupported_refused'],9999)),
 ('invoke',mut(['formal_invocations'],2)),
 ('affine',mut(['maxima','affine_residual'],1.0)),
]
out={name:(not audit.audit(x)['pass']) for name,x in muts}
print(json.dumps({'schema':'postformal-cached-corruption-driver-v1','controls':out,'pass':all(out.values()),'note':'uses exact frozen audit.audit with one cached exact expected regeneration; scientific source unchanged'},indent=2,sort_keys=True))
raise SystemExit(0 if all(out.values()) else 1)
