import json,tempfile
from pathlib import Path
from run_formal import inspect_file
f=json.loads((Path(__file__).resolve().parent/'fixture.json').read_text())
assert f['jar']['repo_sha256']==f['jar']['official_sha256']
assert f['jar']['repo_bytes']==f['jar']['official_bytes']==87022576
assert f['save']['sha256']=='8fff67b0c130ee59a3838c92754b73225a506902bd4838dcc3f1fb5be286cbed'
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'x'; p.write_bytes(b'abc'); rows=inspect_file([p], '00'*32, 3); assert len(rows)==1 and rows[0]['identity_ok'] is False
print('PASS mechanics')
