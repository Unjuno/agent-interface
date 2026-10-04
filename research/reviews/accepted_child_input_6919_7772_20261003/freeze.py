"""Prospective metadata-only freeze; does not invoke the experimental processes."""
import hashlib,json,pathlib,sys
from datetime import datetime,timezone
ROOT=pathlib.Path(__file__).resolve().parent
paths=['SOURCE.json','source-diff.patch','DECK.json','PLAN.md','CONSTRUCTION.md','owner.mjs','peer_v2.py','collect.py','audit.py','freeze.py']
paths += [str(p.relative_to(ROOT)).replace('\\','/') for p in sorted((ROOT/'source').rglob('*.mjs'))]
record=dict(allocation='accepted-child-input-7772-v1',utc=datetime.now(timezone.utc).isoformat(),
  files={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},output='matrix-v1',
  construction='first metadata fixture error retained separately; v2 ordinary EOF fixture succeeded before this freeze',
  original_author_producer_invocations=0,original_author_auditor_invocations=0,formal_deck_invocations_allowed=1)
with (ROOT/'FREEZE.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(dict(allocation=record['allocation'],files=len(paths),utc=record['utc'])))
