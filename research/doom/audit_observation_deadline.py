"""Audit the observation-anchored deadline self-use trace, not a speed claim."""
import hashlib,json,sys
from pathlib import Path
from audit import audit

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'live_control'))
from lease import Lease,Expired

def main():
    folder=HERE/'results/observation-deadline-01'
    plan=json.loads((HERE/'observation_deadline_plan.json').read_text())
    assert hashlib.sha256((HERE/plan['entrypoint']).read_bytes()).hexdigest()==plan['entrypoint_sha256']
    report=audit(folder)
    rows=[json.loads(x) for x in (folder/'events.jsonl').read_text().splitlines()]
    assert rows==[json.loads(x) for x in (folder/'delivered.jsonl').read_text().splitlines()]
    owners=json.loads((folder/'owner-events.json').read_text())
    assert owners[-1]['reason']=='close' and all(x['verified'] for x in owners)
    observations={};submits=[];clocks=0
    for r in rows:
        if r['event']=='observation':observations[r['sequence']]=r
        if r['event']!='command':continue
        c=r['command'];clocks+=c['op']=='clock'
        if c['op']!='submit':continue
        assert c['expected_sequence']==max(observations)
        anchor=observations[c['expected_sequence']]['capture_ns']
        assert c['valid_until_ns']==anchor+25_000_000_000
        assert r['received_ns']<c['valid_until_ns']
        # Deterministic boundary check uses the existing runtime Lease, not an
        # observed late-GUI submission or a new freshness guarantee.
        Lease(c['valid_until_ns'],clock=lambda:c['valid_until_ns']-1).check()
        try:Lease(c['valid_until_ns'],clock=lambda:c['valid_until_ns']).check()
        except Expired:pass
        else:raise AssertionError('deadline boundary was accepted')
        submits.append(dict(id=c['id'],observation_age_at_receipt_ms=(r['received_ns']-anchor)/1e6,
                            remaining_validity_at_receipt_ms=(c['valid_until_ns']-r['received_ns'])/1e6))
    accepted=[r for r in rows if r['event']=='accepted'];assert clocks==0 and len(accepted)==2
    assert not any(r['event']=='rejected' for r in rows)
    assert all(r['status']=='completed' for r in rows if r['event']=='terminal')
    score=report['post_control_score'];assert score['episode_finished'] and not score['player_dead']
    first=next(r for r in rows if r['event']=='observation')
    report.update(clock_commands=clocks,submits=submits,
        initial_capture_to_first_accept_ms=(accepted[0]['accepted_ns']-first['capture_ns'])/1e6,
        between_accepts_ms=(accepted[1]['accepted_ns']-accepted[0]['accepted_ns'])/1e6,
        plan_sha256=hashlib.sha256((HERE/'observation_deadline_plan.json').read_bytes()).hexdigest(),
        boundary_check='deterministic Lease clock; no late GUI input trial',
        actual_model_tokens=None,qualification=False,
        comparison='different seed and learning; no causal speed estimate')
    (folder/'deadline-audit.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
