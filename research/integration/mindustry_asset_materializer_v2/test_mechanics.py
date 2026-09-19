#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from materialize import materialize,digest
R=Path(__file__).resolve().parent; f=json.loads((R/'fixture.json').read_text()); ids=f['test']
with tempfile.TemporaryDirectory() as td:
 p=Path(td); j=p/'j'; s=p/'s'; j.write_text(ids['jar']['content_utf8']); s.write_text(ids['save']['content_utf8']); out=p/'ready'
 m=materialize(j,s,out,ids); assert m['status']=='ASSETS_READY'; assert (out/'MANIFEST.json').is_file()
 assert digest(out/ids['jar']['name'])==(ids['jar']['bytes'],ids['jar']['sha256'])
 assert digest(out/ids['save']['name'])==(ids['save']['bytes'],ids['save']['sha256'])
print('PASS mechanics')
