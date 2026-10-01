import json

def resolve(crop, source, target):
    if crop.get('source')!=source or crop.get('role')!='CANDIDATE': return 'UNKNOWN'
    x,y,w,h=crop.get('box',(0,0,0,0))
    tx,ty=target
    if not (x<=tx<x+w and y<=ty<y+h): return 'UNKNOWN'
    return (x,y,tx-x,ty-y)

def main():
    src='frame-1'; target=(25,25)
    cases=[({'source':src,'role':'CANDIDATE','box':(10,10,30,30)},(10,10,15,15)),({'source':src,'role':'CANDIDATE','box':(0,0,10,10)},'UNKNOWN'),({'source':'frame-0','role':'CANDIDATE','box':(10,10,30,30)},'UNKNOWN'),({'source':src,'role':'OVERVIEW','box':(10,10,30,30)},'UNKNOWN')]
    assert all(resolve(c,src,target)==expected for c,expected in cases)
    result={'cases':len(cases),'mapped':1,'unknown':3,'status':'PASS_MULTIRES_PROVENANCE_CONSTRUCTION_SCOPED','model_localization':None,'byte_reduction':None}
    open('result.json','w').write(json.dumps(result,sort_keys=True,indent=2)+'\n'); print(json.dumps(result,sort_keys=True))
if __name__=='__main__': main()
