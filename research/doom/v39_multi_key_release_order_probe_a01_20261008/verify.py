import hashlib
import itertools
import json
from pathlib import Path

p=Path(__file__).resolve().parent
src=(p/'session_map01_v19.py').read_bytes()
assert hashlib.sha256(src).hexdigest().upper()=='2C5304BD246118F8124D5F7B50B81F869FB35EA3EE76887F4682748FDF95618A'
assert hashlib.sha1(b'blob '+str(len(src)).encode()+b'\0'+src).hexdigest()=='93acee5927751fcf3b4eabadc24efe3dc4483b80'
r=json.loads((p/'result.json').read_text(encoding='utf-8'))
assert r['source']['head']=='7ec4e3ef405919bf5f1bfd9eeddbe630f3a5b32e'
for case in r['cases']:
 n=case['key_count']; keys=[chr(65+i) for i in range(n)]
 expected={(a,rel) for a in itertools.permutations(keys) for rel in itertools.permutations(keys)}
 rows=case['schedules']; observed={(tuple(x['admission_order']),tuple(x['release_order'])) for x in rows}
 assert observed==expected and len(rows)==len(expected)
 matched=0
 for x in rows:
  should_match=x['admission_order'][-1]==x['release_order'][-1]
  assert x['matched']==should_match
  assert x.get('candidate')!='none'
  assert x['held_after']==[]
  assert x['candidate_up_key']==x['release_order'][-1]
  assert x['candidate_down_key']==x['admission_order'][-1]
  matched+=x['matched']
 assert matched==len(rows)//n
 assert case['matched_pairs']==matched and case['censored_no_pair']==len(rows)-matched
 assert abs(case['match_rate']-1/n)<1e-12
print('independent schedule audit: PASS (1+4+36 cases)')
