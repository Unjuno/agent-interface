"""Audit frozen synthetic observations; run without Python optimization."""
import hashlib,json,pathlib,statistics,sys
if not __debug__:raise RuntimeError('audit requires assertions enabled')
root=pathlib.Path(__file__).resolve().parent
summary=[]
for ident,order in [('segment-r86-a01','ascending'),('segment-r86-a02','descending')]:
    path=root/ident;c=json.loads((path/'conditions.json').read_text())
    assert c['order']==order
    for name,digest in c['source_sha256'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest
    assert json.loads((path/'launcher-result.json').read_text())['returncode']==0
    result=json.loads((path/'output/result.json').read_text())
    assert result==json.loads((path/'stdout').read_text()) and result['status']=='completed'
    assert result['size_order']==order and result['repetitions']==41
    sizes=[0,1000,10000,100000];assert [r['size'] for r in result['results']]==(sizes if order=='ascending' else sizes[::-1])
    for row in result['results']:
        for arm in ('dict_copy','segmented'):
            samples=row['samples_ns'][arm]
            assert len(samples)==41 and all(type(x) is int and x>0 for x in samples)
            assert statistics.median(samples)==row['median_ns'][arm]
            assert type(row['peak_new_bytes'][arm]) is int and row['peak_new_bytes'][arm]>0
        summary.append({'allocation':ident,'size':row['size'],'median_ns':row['median_ns'],'peak_new_bytes':row['peak_new_bytes']})
for mode in ('normal','optimized'):
    assert json.loads((root/'construction-tests'/f'{mode}-result.json').read_text())['returncode']==0
print(json.dumps({'status':'audited','rows':summary},indent=2))
