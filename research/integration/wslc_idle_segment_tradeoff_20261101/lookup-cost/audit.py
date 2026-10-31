import hashlib,json,pathlib,statistics
if not __debug__:raise RuntimeError('audit requires assertions enabled')
root=pathlib.Path(__file__).resolve().parent;summary=[]
for ident,order in [('segment-r87-a01','ascending'),('segment-r87-a02','descending')]:
    path=root/ident;c=json.loads((path/'conditions.json').read_text());assert c['order']==order
    for name,digest in c['source_sha256'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest
    assert json.loads((path/'launcher-result.json').read_text())['returncode']==0
    result=json.loads((path/'output/result.json').read_text());assert result==json.loads((path/'stdout').read_text())
    assert result['status']=='completed' and result['order']==order and result['repetitions']==41
    sizes=[1000,10000,100000];assert [r['size'] for r in result['rows']]==(sizes if order=='ascending' else sizes[::-1])
    for row in result['rows']:
        for name,samples in row['samples_ns_per_1024'].items():
            assert len(samples)==41 and all(type(n) is int and n>0 for n in samples)
            assert statistics.median(samples)/1024==row['median_ns_per_lookup'][name]
        summary.append({'allocation':ident,'size':row['size'],'median_ns_per_lookup':row['median_ns_per_lookup']})
print(json.dumps({'status':'audited','rows':summary},indent=2))
