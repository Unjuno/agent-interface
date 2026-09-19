"""Audit one actual assistant recovery, with explicit endpoint scopes."""
import hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
HERE=Path(__file__).resolve().parent;out=HERE/'results/servo-recovery-01'
for name,h in json.loads((out/'sources.json').read_text()).items():assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==h
events=[json.loads(x) for x in (out/'events.jsonl').read_text().splitlines()];decoder=Decoder('live-control');count=0
for r in events:
    if r['event']!='observation':continue
    count+=1;assert count==r['sequence']
    f=decoder.accept((out/f'{count:03d}.ait').read_bytes())
    with Image.open(out/Path(r['image']).name) as im:assert im.size==(f.width,f.height) and im.tobytes()==f.pixels
accepted={r['id']:r for r in events if r['event']=='accepted'}
terminals={r['id']:r for r in events if r['event']=='terminal'}
assert set(accepted)=={'attempt','reobserve','recover','save'}
assert all(r['status']=='completed' and r['release']['verified'] for r in terminals.values())
assert terminals['attempt']['terminal_ns']<accepted['reobserve']['accepted_ns']<accepted['recover']['accepted_ns']
commands=[r for r in events if r['event']=='command']
recovery=next(r for r in commands if r['command'].get('id')=='recover')['command']
assert recovery['expected_sequence']==9 and recovery['steps'][0]['source_sequence']==9
assert recovery['valid_until_ns']!=accepted['attempt']['valid_until_ns']
evaluation=next(r for r in events if r['event']=='independent_evaluation');assert evaluation['success']
rect=ET.parse(out/'shape.svg').getroot().find('{http://www.w3.org/2000/svg}rect')
assert all(rect.get(k)==v for k,v in evaluation['actual'].items())
dx=(float(rect.get('x'))-50)*1.18;assert abs(dx-24)<=1
assert [rect.get(k) for k in ('y','width','height','transform')]==['50','40','30',None]
report=dict(exact_frames=count,saved_dx=dx,programs=len(accepted),clock_commands=sum(r['command']['op']=='clock' for r in commands),
            first_accept_to_independent_score_ms=(evaluation['known_ns']-accepted['attempt']['accepted_ns'])/1e6,
            false_terminal_to_recovery_accept_ms=(accepted['recover']['accepted_ns']-terminals['attempt']['terminal_ns'])/1e6,
            program_ms={key:(terminals[key]['terminal_ns']-value['accepted_ns'])/1e6 for key,value in accepted.items()},
            semantic_caveat='first false goal identified by assistant from known-fixture GUI; not an automatic semantic verifier')
(HERE/'results/servo-recovery-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
