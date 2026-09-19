"""Compare actual same-runtime self-use cohorts without causal speedup inference."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;rows=[];programs=[]
for cohort in ('request-outcome-self-use-01','receipt-clock-self-use-01'):
    root=HERE/'results'/cohort
    events=list(map(json.loads,(root/'events.jsonl').read_text().splitlines()))
    submitted=[e['command'] for e in events if e['event']=='command' and e['command']['op']=='submit']
    programs.append([c['steps'] for c in submitted])
    initial=next(e for e in events if e['event']=='observation')
    accepted=[e for e in events if e['event']=='accepted'];terminals=[e for e in events if e['event']=='terminal']
    effect=next(e for e in events if e['event']=='effect_evidence')
    read=json.loads((root/'read-effect.json').read_text())
    rows.append(dict(cohort=cohort,initial_to_first_admission_ms=(accepted[0]['accepted_ns']-initial['capture_ns'])/1e6,
                     modal_to_confirmation_ms=(accepted[1]['accepted_ns']-terminals[0]['terminal_ns'])/1e6,
                     first_capture_to_effect_read_ms=(read['returned_ns']-initial['capture_ns'])/1e6,
                     clocks=sum(e['event']=='clock' for e in events),effect=effect['effect']['status']))
assert programs[0]==programs[1]
(HERE/'results/receipt-clock-comparison.json').write_text(json.dumps(dict(same_program_steps=True,rows=rows,
    limitation='sequential familiar self-use; second run includes a wrong-image-path attempt; no causal speedup or model-token measurement'),indent=2)+'\n')
print(json.dumps(rows,indent=2))
