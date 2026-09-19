import itertools,json,hashlib
E=('CURRENT','TEMPORAL','VERIFY','FULL')
PACKAGES=(('CURRENT',1,{'CURRENT'}),('TEMPORAL',2,{'CURRENT','TEMPORAL'}),('VERIFY',2,{'CURRENT','VERIFY'}),('FULL',4,set(E)))
def typed(required,budget):
    fits=[p for p in PACKAGES if p[1]<=budget and required<=p[2]]
    return min(fits,key=lambda p:p[1])[0] if fits else 'DEFER'
def scalar_highest(budget):
    fits=[p for p in PACKAGES if p[1]<=budget]
    return max(fits,key=lambda p:p[1])[0] if fits else 'DEFER'
def run():
    rows=[]
    for n in range(1,5):
      for req in itertools.combinations(E,n):
       req=set(req)
       for budget in range(0,5):
        t=typed(req,budget); s=scalar_highest(budget)
        rows.append({'required':sorted(req),'budget':budget,'typed':t,'scalar':s,'typed_safe':t=='DEFER' or req<=dict((x[0],x[2]) for x in PACKAGES)[t],'scalar_safe':s=='DEFER' or req<=dict((x[0],x[2]) for x in PACKAGES)[s]})
    assert all(r['typed_safe'] for r in rows)
    unsafe_scalar=sum(not r['scalar_safe'] for r in rows)
    assert unsafe_scalar>0
    result={'decision':'PASS_TYPED_ATTENTION_BUDGET_ADMISSION_SCOPED','rows':len(rows),'typed_unsafe':0,'scalar_unsafe':unsafe_scalar,'formal_invocations':1,'reruns':0,'tuning':0}
    raw=json.dumps(result,sort_keys=True,separators=(',',':')).encode();result['sha256']=hashlib.sha256(raw).hexdigest();return result
if __name__=='__main__':print(json.dumps(run(),indent=2,sort_keys=True))
