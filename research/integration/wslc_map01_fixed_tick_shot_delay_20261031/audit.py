from pathlib import Path
import json
here=Path(__file__).resolve().parent
def load(n):
 d=here/n
 assert (d/'exit.txt').read_text(encoding='utf-8-sig').strip()=='0'
 raw=(d/'raw.log').read_text(encoding='utf-8-sig')
 return json.loads(raw[raw.index('{'):])
a=load('p03'); b=load('p04')
assert [r['arm'] for r in a['runs']]==['withhold','fire','fire','withhold']
assert all(r['prefix']==a['runs'][0]['prefix'] for r in a['runs'])
for r in a['runs']:
 assert r['prefix'][3]['variables'][-1]==50 and r['prefix'][4]['variables'][-1]==49
 assert r['after']['variables'][-1]==(48 if r['arm']=='fire' else 49)
 assert r['final']['variables'][3:5]==[94,0]
assert [r['arm'] for r in b['runs']]==['idle','attack','attack','idle']
assert all(r['samples'][0]==b['runs'][0]['samples'][0] for r in b['runs'])
for r in b['runs']:
 s=r['samples']; assert s[3]['tic']==134 and s[3]['ammo']==50
 drops=[x for x in s if x['ammo']<50]
 if r['arm']=='attack': assert drops and drops[0]['tic']==136 and drops[0]['phase']=='released' and drops[0]['ammo']==49
 else: assert not drops
assert b['runs'][1]['samples']==b['runs'][2]['samples'] and b['runs'][0]['samples']==b['runs'][3]['samples']
print('p03 branch and p04 per-tick controls verified')
