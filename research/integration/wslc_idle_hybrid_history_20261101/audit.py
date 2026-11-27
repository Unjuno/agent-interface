"""Audit an extracted raw archive with assertions enabled."""
import hashlib,json,pathlib,statistics
if not __debug__:raise RuntimeError('audit requires assertions enabled')
root=pathlib.Path(__file__).resolve().parent

def source_path(name,case):
    return (root/'source'/name) if name.startswith('src/') else (root/case/name)

def verify_manifest(case):
    path=root/case;data=(path/'manifest.json').read_bytes();manifest=json.loads(data)
    for name,digest in manifest.items():
        assert hashlib.sha256(source_path(name,case).read_bytes()).hexdigest()==digest,(case,name)
    return hashlib.sha256(data).hexdigest()

for mode in ('normal','optimized'):
    tests=root/'construction-tests';c=json.loads((tests/(mode+'-conditions.json')).read_text())
    assert json.loads((tests/(mode+'-result.json')).read_text())['returncode']==0
    assert 'Ran 88 tests' in (tests/(mode+'-stderr')).read_text() and 'OK' in (tests/(mode+'-stderr')).read_text()
    for name,digest in c['source_manifest'].items():assert hashlib.sha256((root/'source'/name).read_bytes()).hexdigest()==digest

manifest_sha=verify_manifest('realx')
for ident,mode in [('hybrid-publication-a01','cancel'),('hybrid-publication-a02','publish')]:
    p=root/'realx'/ident;c=json.loads((p/'conditions.json').read_text())
    assert c['mode']==mode and c['manifest_sha256']==manifest_sha
    assert json.loads((p/'launcher-result.json').read_text())['returncode']==0
    r=json.loads((p/'output/result.json').read_text());assert r['status']=='passed' and r['mode']==mode
    assert r['sequence_while_staged']==0 and not r['visible_while_staged'] and r['mint_while_staged']=='rejected'
    assert r['sequence_after']==(0 if mode=='cancel' else 1) and r['visible_after']==(mode=='publish')
    assert r['input_neutral'] and r['target_exit']==0 and r['server_exit']==0
    assert r['target_result']['value']=='a' and [e['type'] for e in r['target_result']['events'] if e['key']=='a']==['press','release']
    assert r['action']['result']['execution']['releases'][-1]['verified']
    events=[e['name'] for e in r['events']]
    assert events.index('staged')<events.index('stage_resumed')<events.index('capture_returned')<events.index('fresh_action_returned')
    if mode=='cancel':assert events.index('staged')<events.index('cancel_returned')<events.index('stage_resumed')

manifest_sha=verify_manifest('cost');summary=[]
for ident,order in [('hybrid-r91-a01','ascending'),('hybrid-r91-a02','descending')]:
    p=root/'cost'/ident;c=json.loads((p/'conditions.json').read_text());assert c['order']==order and c['manifest_sha256']==manifest_sha
    assert json.loads((p/'launcher-result.json').read_text())['returncode']==0
    result=json.loads((p/'output/result.json').read_text());assert result==json.loads((p/'stdout').read_text())
    assert result['status']=='completed' and result['order']==order and result['repetitions']==41 and result['fallback_repetitions']==9
    sizes=[1000,10000,100000];assert [r['size'] for r in result['rows']]==(sizes if order=='ascending' else sizes[::-1])
    for row in result['rows']:
        for name,samples in row['samples_ns'].items():
            assert len(samples)==41 and all(type(n) is int and n>0 for n in samples)
            assert statistics.median(samples)==row['medians_ns'][name]
        assert len(row['fallback_overwrite_ns'])==9 and statistics.median(row['fallback_overwrite_ns'])==row['fallback_median_ns']
        summary.append({'allocation':ident,'size':row['size'],'medians_ns':row['medians_ns'],'fallback_median_ns':row['fallback_median_ns']})

probe=json.loads((root/'source'/'iterator-probe-confirmation.json').read_text(encoding='utf-8-sig'))
assert probe['baseline']['error']=='RuntimeError' and probe['hybrid']['error'] is None
print(json.dumps({'status':'audited','cost_rows':summary,'iterator_probe':probe},indent=2))
