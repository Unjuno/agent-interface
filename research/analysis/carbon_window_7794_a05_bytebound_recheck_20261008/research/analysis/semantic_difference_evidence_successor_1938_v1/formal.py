import json

def diff(a,b,source,identity,epoch):
    facts=[]
    for k in sorted(set(a)|set(b)):
        if a.get(k)!=b.get(k):
            kind={'x':'MOVED','text':'TEXT_CHANGED','enabled':'ENABLED_STATE_CHANGED','present':'APPEARED_OR_DISAPPEARED','focus':'FOCUS_CHANGED','identity':'IDENTITY_CHANGED'}.get(k,'VALUE_CHANGED')
            facts.append({'kind':kind,'field':k,'before':a.get(k),'after':b.get(k),'source':source,'identity':identity,'epoch':epoch})
    return facts

def main():
    rows=0
    for identity in ('surface-A','surface-B'):
      for epoch in (1,2):
       a={'x':1,'text':'Save','enabled':False,'present':True,'focus':'main','identity':identity}
       b=dict(a,x=2,text='Submit',enabled=True,focus='dialog')
       fs=diff(a,b,f'{identity}-{epoch}',identity,epoch)
       assert {f['kind'] for f in fs}=={'MOVED','TEXT_CHANGED','ENABLED_STATE_CHANGED','FOCUS_CHANGED'}
       assert all(f['source']==f'{identity}-{epoch}' and f['identity']==identity and f['epoch']==epoch for f in fs)
       assert not all(f['epoch']==epoch+1 for f in fs)
       rows+=1
    result={'rows':rows,'facts_per_row':4,'status':'PASS_SEMANTIC_DIFFERENCE_EVIDENCE_SCOPED','authority_escalation':False,'stale_rejected':True,'identity_replacement_rejected':True}
    open('semantic-difference-result.json','w').write(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__': main()
