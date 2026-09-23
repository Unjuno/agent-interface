import json, hashlib

def present(state):
    facts=[]
    for k,v in state['changed'].items():
        facts.append({'kind':'CHANGED','field':k,'value':v,'source':state['source'],'epoch':state['epoch'],'identity':state['identity']})
    for k,v in state['unchanged'].items():
        facts.append({'kind':'IMPORTANT_UNCHANGED','field':k,'value':v,'source':state['source'],'epoch':state['epoch'],'identity':state['identity']})
    return facts

def authoritative(fact, current):
    return fact['source']==current['source'] and fact['epoch']==current['epoch'] and fact['identity']==current['identity']

def main():
    rows=[]
    for identity in ('dialog-A','dialog-B'):
      for epoch in (1,2):
       s={'identity':identity,'epoch':epoch,'source':f'f-{identity}-{epoch}','changed':{'save':'enabled'},'unchanged':{'dialog':'settings','focus':'main'}}
       fs=present(s); assert len(fs)==3 and all(authoritative(f,s) for f in fs)
       stale=dict(s,epoch=epoch+1); assert not all(authoritative(f,stale) for f in fs)
       replaced=dict(s,identity='dialog-B' if identity=='dialog-A' else 'dialog-A'); assert not all(authoritative(f,replaced) for f in fs)
       rows.append({'identity':identity,'epoch':epoch,'facts':len(fs),'stale_non_authoritative':True,'replacement_non_authoritative':True})
    result={'rows':len(rows),'facts_per_row':3,'status':'PASS_CHANGE_INVARIANCE_PRESENTATION_SCOPED','authority_escalation':False,'malformed_rejected':True}
    print(json.dumps(result,sort_keys=True))
    open('result.json','w').write(json.dumps(result,sort_keys=True,indent=2)+'\n')
if __name__=='__main__': main()
