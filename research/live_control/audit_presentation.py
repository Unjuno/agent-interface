import json,sys
from pathlib import Path
from presentation import Presentation

def encoded(rows):return ''.join(json.dumps(r)+'\n' for r in rows).encode()
for name in sys.argv[1:]:
    folder=Path(name)
    raw=[json.loads(s) for s in (folder/'events.jsonl').read_text().splitlines()]
    p=Presentation();selected=[item for record in raw for item in p.project(record)]
    mode=next(r for r in raw if r['event']=='ready').get('presentation','full')
    recorded=folder/'delivered.jsonl'
    if recorded.exists():
        actual=[json.loads(s) for s in recorded.read_text().splitlines()]
        assert actual==(selected if mode=='compact' else raw)
    for r in raw:
        if r['event'] in ('terminal','settle_result','rejected','independent_evaluation') or (r['event']=='observation' and r.get('focus_samples_match') is False):
            assert r in selected
    first=next(r['accepted_ns'] for r in raw if r['event']=='accepted')
    score=next(r for r in raw if r['event']=='independent_evaluation')
    terms=[r for r in raw if r['event']=='terminal']
    result=dict(mode=mode,raw_records=len(raw),compact_records=len(selected),raw_json_bytes=len(encoded(raw)),
        compact_json_bytes=len(encoded(selected)),same_trace_json_reduction=1-len(encoded(selected))/len(encoded(raw)),
        raw_observations=sum(r['event']=='observation' for r in raw),compact_observations=sum(r['event']=='observation' for r in selected),
        task_success=score['success'],accepted_programs=len(terms),first_accept_to_evaluation_seconds=(score['known_ns']-first)/1e9,
        program_duration_ms=[(t['terminal_ns']-next(r['accepted_ns'] for r in raw if r['event']=='accepted' and r['id']==t['id']))/1e6 for t in terms],
        scope='serialization and local runtime timestamps; output log precedes stdout, not client acknowledgement or model tokens')
    (folder/'presentation-audit.json').write_text(json.dumps(result,indent=2));print(name,json.dumps(result))
