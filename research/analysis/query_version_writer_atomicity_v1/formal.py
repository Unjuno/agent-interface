import json
PROTOCOLS={
 'ATOMIC':lambda m:[('pre',m,0),('post',1-m,1)],
 'MEMBERSHIP_FIRST':lambda m:[('pre',m,0),('mid',1-m,0),('post',1-m,1)],
 'VERSION_FIRST':lambda m:[('pre',m,0),('mid',m,1),('post',1-m,1)],
 'NO_VERSION':lambda m:[('pre',m,0),('post',1-m,0)],
}
summary={}
directions={'insert':0,'remove':0}
for name,fn in PROTOCOLS.items():
    unsafe=false=accepted=rejected=0
    rows=[]
    for m in (0,1):
        directions['insert' if m==0 else 'remove']+=1 if name=='ATOMIC' else 0
        for stage,current_m,q in fn(m):
            accept=(q==0)
            safe=(current_m==m)
            accepted+=int(accept); rejected+=int(not accept)
            unsafe+=int(accept and not safe)
            false+=int((not accept) and safe)
            rows.append({'prepared_m':m,'stage':stage,'current_m':current_m,'q':q,'accept':accept,'safe_accept':safe})
    summary[name]={'unsafe_acceptances':unsafe,'false_invalidations':false,'accepted':accepted,'rejected':rejected,'rows':rows}
result={'summary':summary,'directions':directions,'decision':None}
pass_gate=(summary['ATOMIC']['unsafe_acceptances']==0 and summary['ATOMIC']['false_invalidations']==0 and
 summary['MEMBERSHIP_FIRST']['unsafe_acceptances']>0 and summary['NO_VERSION']['unsafe_acceptances']>0 and
 summary['VERSION_FIRST']['unsafe_acceptances']==0 and summary['VERSION_FIRST']['false_invalidations']>0 and
 directions['insert']>0 and directions['remove']>0)
result['decision']='PASS_QUERY_VERSION_WRITER_ATOMICITY_SCOPED' if pass_gate else 'FAIL_QUERY_VERSION_WRITER_ATOMICITY'
print(json.dumps(result,indent=2,sort_keys=True))
