import json

def main():
    with open('RESULT.json',encoding='utf-8') as f: p=json.load(f)
    with open('PROVENANCE.json',encoding='utf-8') as f: v=json.load(f)
    assert p['decision']=='PASS_CONTAINER_REVALIDATION_SCOPED'
    assert p['statuses']==['ENCODED','OBSOLETE','CACHE_HIT','ENCODED']
    assert p['stale_control']==p['reuse_control']==p['provenance_control']=='PASS'
    assert p['model']==p['x11']==p['input']==0
    assert v['parent_blob_sha']=='2bcb877a2fbd59b2a854122017ff2956d8866524'
    assert v['parent_path'].endswith('/experiment.py')
    assert v['source_sha256'] and v['image_digest'].startswith('python@sha256:')
    assert v['result_sha256'] and v['stdout'].strip()
    assert v['independent_audit']=='PASS' and v['model']==v['x11']==v['input']==0
    print('INDEPENDENT_AUDIT_PASS_PROVENANCE_COMPLETE')
if __name__=='__main__': main()
