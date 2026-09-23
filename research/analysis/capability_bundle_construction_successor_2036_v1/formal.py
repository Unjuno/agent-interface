import json

def compile_bundle(items, allowed):
    out=[]
    for item in items:
        if item.get('role')!='EVIDENCE' or item.get('timestamp') is None: continue
        if item.get('family') not in allowed: continue
        out.append(item)
    return out

def main():
    items=[
      {'family':'pixels','role':'EVIDENCE','timestamp':1,'value':'visual'},
      {'family':'semantic','role':'EVIDENCE','timestamp':1,'value':'enabled'},
      {'family':'debug','role':'EVIDENCE','timestamp':1,'value':'secret'},
      {'family':'logs','role':'EVIDENCE','timestamp':None,'value':'missing-time'},
      {'family':'unsupported','role':'EVIDENCE','timestamp':1,'value':'unknown'},
      {'family':'geometry','role':'SUMMARY','timestamp':1,'value':'not-evidence'},
    ]
    b=compile_bundle(items,{'pixels','semantic','logs'})
    assert [x['family'] for x in b]==['pixels','semantic']
    assert all(x['family']!='debug' for x in b)
    assert [x['family'] for x in compile_bundle(items,{'debug'})]==['debug']
    result={'input_items':len(items),'emitted_items':len(b),'omitted_items':len(items)-len(b),'status':'PASS_CAPABILITY_BUNDLE_PROVENANCE_CONSTRUCTION_SCOPED','model_utility':None,'action_authority':False}
    open('result.json','w').write(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__': main()
