"""Two sequential assistant episodes: endpoint decomposition, not causal A/B."""
import hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
HERE=Path(__file__).resolve().parent
report=[];programs=[]
for n in (1,2):
    root=HERE/f'results/servo-recovery-{n:02d}'
    for name,h in json.loads((root/'sources.json').read_text()).items():assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==h
    events=[json.loads(x) for x in (root/'events.jsonl').read_text().splitlines()]
    delivered=[json.loads(x) for x in (root/'delivered.jsonl').read_text().splitlines()]
    accepted={r['id']:r for r in events if r['event']=='accepted'};terminal={r['id']:r for r in events if r['event']=='terminal'}
    commands=[r for r in events if r['event']=='command'];submitted=[r for r in commands if r['command']['op']=='submit']
    normalized=[]
    for r in submitted:
        steps=json.loads(json.dumps(r['command']['steps']))
        for s in steps:s.pop('source_sequence',None)
        normalized.append((r['command']['id'],steps))
    programs.append(normalized)
    assert all(r['status']=='completed' and r['release']['verified'] for r in terminal.values())
    decoder=Decoder('live-control');count=0;latest=None;receipts=0
    for r in events:
        if r['event']!='observation':continue
        count+=1;assert count==r['sequence'];f=decoder.accept((root/f'{count:03d}.ait').read_bytes())
        with Image.open(root/Path(r['image']).name) as im:assert im.size==(f.width,f.height) and im.tobytes()==f.pixels
    for r in delivered:
        if r['event']=='observation':latest=r
        if 'review' in r:
            receipts+=1;o=r['review']['observation'];assert o['sequence']==latest['sequence'] and o['image']==latest['image']
    evaluation=next(r for r in events if r['event']=='independent_evaluation');assert evaluation['success']
    rect=ET.parse(root/'shape.svg').getroot().find('{http://www.w3.org/2000/svg}rect')
    assert all(rect.get(k)==v for k,v in evaluation['actual'].items())
    dx=(float(rect.get('x'))-50)*1.18;assert abs(dx-24)<=1
    durations={k:(terminal[k]['terminal_ns']-a['accepted_ns'])/1e6 for k,a in accepted.items()}
    gaps=[]
    for previous,next_id in [('attempt','reobserve'),('reobserve','recover'),('recover','save')]:
        command=next(r for r in submitted if r['command']['id']==next_id)
        gaps.append(dict(previous=previous,next=next_id,terminal_to_command_ms=(command['received_ns']-terminal[previous]['terminal_ns'])/1e6,
                         command_to_accept_ms=(accepted[next_id]['accepted_ns']-command['received_ns'])/1e6))
    report.append(dict(cohort=n,exact_frames=count,receipts=receipts,clock_commands=sum(r['command']['op']=='clock' for r in commands),saved_dx=dx,
                       first_accept_to_score_ms=(evaluation['known_ns']-accepted['attempt']['accepted_ns'])/1e6,
                       false_terminal_to_recovery_accept_ms=(accepted['recover']['accepted_ns']-terminal['attempt']['terminal_ns'])/1e6,
                       program_ms=durations,between_programs=gaps,
                       save_terminal_to_score_ms=(evaluation['known_ns']-terminal['save']['terminal_ns'])/1e6,
                       delivered_json_bytes=(root/'delivered.jsonl').stat().st_size))
assert programs[0]==programs[1],'task programs differ beyond sequence and lease envelopes'
(HERE/'results/recovery-boundary-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
