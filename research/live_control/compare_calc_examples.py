"""Sequential same-task assistant comparison; familiarity and timing confounded."""
import hashlib,json
from pathlib import Path
from PIL import Image
from openpyxl import load_workbook
from session_v9 import Decoder
HERE=Path(__file__).resolve().parent
rows=[];programs=[];goals=[]
for n in (1,2):
    root=HERE/f'results/journal-calc-{n:02d}'
    for name,h in json.loads((root/'sources.json').read_text()).items():assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==h
    events=[json.loads(x) for x in (root/'events.jsonl').read_text().splitlines()]
    delivered=[json.loads(x) for x in (root/'delivered.jsonl').read_text().splitlines()]
    flushed=[json.loads(x) for x in (root/'delivery-flush.jsonl').read_text().splitlines()]
    assert [r['delivery_id'] for r in delivered]==[r['delivery_id'] for r in flushed]
    by_id={r['delivery_id']:r for r in flushed}
    for r in delivered:
        if r['event']=='decision_evidence':
            obs=by_id[r['source_delivery_id']]['observation']
            assert obs['sequence']==r['observation_sequence'] and obs['image']==r['image']
    ready=next(r for r in events if r['event']=='ready');goals.append(ready['goal'])
    if n==2:assert ready['basic_step_examples'][2]==dict(op='chord',modifier='Control_L',key='s')
    accepted=[r for r in events if r['event']=='accepted'];ids={r['id'] for r in accepted}
    commands=[r for r in events if r['event']=='command']
    submitted=[r for r in commands if r['command']['op']=='submit']
    programs.append([r['command']['steps'] for r in submitted if r['command']['id'] in ids])
    terminal=[r for r in events if r['event']=='terminal']
    assert len(terminal)==2 and all(r['status']=='completed' and r['release']['verified'] for r in terminal)
    score=next(r for r in events if r['event']=='independent_evaluation');assert score['success']
    wb=load_workbook(root/'sheet.xlsx');assert [wb.active['A1'].value,wb.active['A2'].value]==[532,590]
    decoder=Decoder('live-control');count=0
    for r in events:
        if r['event']!='observation':continue
        count+=1;assert r['sequence']==count
        f=decoder.accept((root/f'{count:03d}.ait').read_bytes())
        with Image.open(root/Path(r['image']).name) as im:assert im.size==(f.width,f.height) and im.tobytes()==f.pixels
    confirm=next(r for r in submitted if r['command']['id']=='confirm_excel')
    reject=next((r for r in events if r['event']=='rejected'),None)
    first_observation=next(r for r in events if r['event']=='observation')
    rows.append(dict(cohort=n,exact_frames=count,submit_commands=len(submitted),accepted_programs=len(accepted),
                     rejections=sum(r['event']=='rejected' for r in events),clock_commands=sum(r['command']['op']=='clock' for r in commands),
                     first_observation_to_score_ms=(score['known_ns']-first_observation['capture_ns'])/1e6,
                     first_accept_to_score_ms=(score['known_ns']-accepted[0]['accepted_ns'])/1e6,
                     modal_terminal_to_confirm_command_ms=(confirm['received_ns']-terminal[0]['terminal_ns'])/1e6,
                     last_terminal_to_score_ms=(score['known_ns']-terminal[-1]['terminal_ns'])/1e6,
                     rejection_to_retry_accept_ms=None if reject is None else (accepted[0]['accepted_ns']-reject['emit_started_ns'])/1e6,
                     local_program_ms=[(t['terminal_ns']-a['accepted_ns'])/1e6 for a,t in zip(accepted,terminal)],
                     delivered_bytes=(root/'delivered.jsonl').stat().st_size))
assert goals[0]==goals[1] and programs[0]==programs[1]
(HERE/'results/calc-examples-comparison.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows,indent=2))
