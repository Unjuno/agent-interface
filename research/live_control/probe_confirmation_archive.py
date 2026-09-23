"""HTTP policy and independent attempt log survive fixture temp cleanup."""
import hashlib, json, tempfile, urllib.request
from pathlib import Path
from confirmation_browser_entry_v2 import fixture_server
HERE=Path(__file__).resolve().parent
out=HERE/'results/confirmation-archive-01';out.mkdir(exist_ok=False)
archive=out/'attempts.jsonl'
with tempfile.TemporaryDirectory() as temporary:
    saved=Path(temporary)/'submitted.txt'
    server=fixture_server(saved,archive)
    url=f'http://127.0.0.1:{server.server_port}/submit'
    try:
        with urllib.request.urlopen(url,data=b'value=test-value') as response:body=response.read()
        assert b'Nothing has been saved' in body and not saved.exists()
        with urllib.request.urlopen(url,data=b'value=test-value&confirm=yes') as response:body=response.read()
        assert b'Submission received' in body and saved.read_text()=='value=test-value'
    finally:server.shutdown();server.server_close()
assert not saved.exists()
records=[json.loads(line) for line in archive.read_text().splitlines()]
assert [r['accepted'] for r in records]==[False,True]
assert records[0]['fields']=={'value':['test-value']}
assert records[1]['fields']=={'value':['test-value'],'confirm':['yes']}
result=dict(attempts=2,unconfirmed_not_saved=True,confirmed_saved=True,log_survives_temp_cleanup=True,
    scope='HTTP fixture-only probe; does not restore missing log from earlier GUI self-use')
(out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
(out/'sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest()
    for p in (Path(__file__),HERE/'confirmation_browser_entry_v2.py')},indent=2)+'\n')
print(json.dumps(result))
