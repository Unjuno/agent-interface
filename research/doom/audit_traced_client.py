"""Audit lossless local client delivery and report explicitly scoped endpoints."""
import hashlib,json
from pathlib import Path
from audit import audit

HERE=Path(__file__).resolve().parent

def main():
    root=HERE/'results/traced-assistant-01';run=root/'runtime'
    manifest=json.loads((root/'manifest.json').read_text())
    for name,digest in manifest['sources'].items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==digest,name
    report=audit(run)
    events=[json.loads(x) for x in (run/'events.jsonl').read_text().splitlines()]
    delivered=[json.loads(x) for x in (run/'delivered.jsonl').read_text().splitlines()]
    trace=[json.loads(x) for x in (root/'client.jsonl').read_text().splitlines()]
    received=[x for x in trace if x['event']=='runtime_received']
    assert events==delivered==[x['record'] for x in received]
    commands=[x for x in trace if x['event']=='command_received']
    assert [x['command'] for x in commands]==[x['command'] for x in events if x['event']=='command']
    assert trace[-1]['event']=='client_closed' and trace[-1]['child_returncode']==0
    assert not trace[-1]['reader_alive'] and not trace[-1]['errors']
    owners=json.loads((run/'owner-events.json').read_text())
    assert owners[-1]['reason']=='close' and all(x['verified'] for x in owners)
    assert all(x['status']=='completed' for x in events if x['event']=='terminal')
    assert report['post_control_score']['episode_finished'] and not report['post_control_score']['player_dead']
    accepted=[x for x in events if x['event']=='accepted'];metrics=[]
    for a in accepted:
        sent=next(x for x in commands if x['command'].get('id')==a['id'])
        first=next(x for x in received if x['record']['event']=='observation' and x['record']['id']==a['id'])
        obs=first['record']
        metrics.append(dict(id=a['id'],client_command_to_accept_ms=(a['accepted_ns']-sent['client_ns'])/1e6,
            accept_to_first_image_ready_ms=(obs['image_ready_ns']-a['accepted_ns'])/1e6,
            image_ready_to_local_client_receipt_ms=(first['received_ns']-obs['image_ready_ns'])/1e6,
            emit_start_to_local_client_receipt_ms=(first['received_ns']-obs['emit_ns'])/1e6))
    tools=json.loads((root/'tool-times.json').read_text())
    spans=[dict(id=x['id'],write_tool_ms=x['writeReturn']-x['start'],
                feedback_read_and_image_tool_ms=x['imageToolReturned']-x['writeReturn'],
                combined_call_body_ms=x['imageToolReturned']-x['start']) for x in tools]
    report.update(local_client_metrics=metrics,tool_body_spans=spans,
        between_runtime_accepts_ms=(accepted[1]['accepted_ns']-accepted[0]['accepted_ns'])/1e6,
        between_image_tool_return_and_next_call_body_ms=tools[1]['start']-tools[0]['imageToolReturned'],
        clock_note='Runtime/client: WSL monotonic. Tool body: separate wall clock; no cross-clock subtraction.',
        scope='Actual assistant integration; local receipt is not model receipt; no causal speed estimate',
        actual_tokens=None,qualification=False)
    (root/'audit.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k in ('local_client_metrics','tool_body_spans','between_runtime_accepts_ms','between_image_tool_return_and_next_call_body_ms','exact_frames')},indent=2))

if __name__=='__main__':main()
