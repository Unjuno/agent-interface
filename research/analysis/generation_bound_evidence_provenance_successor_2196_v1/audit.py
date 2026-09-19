import json

def main():
    with open('RESULT.json',encoding='utf-8') as f: p=json.load(f)
    assert p['decision']=='PASS_CONTAINER_PROVENANCE_COMPLETE_SCOPED'
    assert p['statuses']==['ENCODED','OBSOLETE','CACHE_HIT','ENCODED']
    assert p['stale_control']==p['reuse_control']==p['provenance_control']=='PASS'
    assert p['model']==p['x11']==p['input']==0
    print('INDEPENDENT_AUDIT_PASS')
if __name__=='__main__': main()
