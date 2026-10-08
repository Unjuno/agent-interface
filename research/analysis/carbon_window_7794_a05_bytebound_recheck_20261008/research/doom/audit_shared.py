"""Read-only audit of the scripted shared DOOM readiness cohort."""
import hashlib,json,sys
from pathlib import Path
from audit import audit as audit_frames

HERE=Path(__file__).resolve().parent

def main(folder):
    manifest=json.loads((folder/'manifest.json').read_text())
    for name,digest in manifest['sources'].items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==digest,name
    reports=json.loads((folder/'summary.json').read_text())
    assert len(reports)==len(manifest['cases'])==3
    audited=[]
    for case,report in zip(manifest['cases'],reports):
        assert all(report[k]==v for k,v in case.items()) and report['readiness_pass']
        run=folder/case['mode'];result=audit_frames(run)
        result['scope']='scripted shared-adapter readiness; no model or game-success claim'
        rows=[json.loads(x) for x in (run/'events.jsonl').read_text().splitlines()]
        assert rows==[json.loads(x) for x in (run/'delivered.jsonl').read_text().splitlines()]
        commands=[r['command'] for r in rows if r['event']=='command']
        stale=next(c for c in commands if c.get('id')=='stale')
        first=next(i for i,r in enumerate(rows) if r['event']=='accepted')
        assert any(r['event']=='rejected' and 'expired' in r['reason'] for r in rows[:first])
        assert not any(r['event']=='input_admission' for r in rows[:first])
        assert not any(r['event']=='accepted' and r['id']==stale['id'] for r in rows)
        terminals=[r for r in rows if r['event']=='terminal']
        assert len(terminals)==2 and terminals[1]['id']=='observe'
        assert terminals[1]['status']=='completed'
        expected={'ordinary':'completed','cancel':'cancelled','expiry':'expired'}[case['mode']]
        assert terminals[0]['status']==expected
        admissions=[r for r in rows if r['event']=='input_admission']
        assert admissions and all(r['key']=='Right' for r in admissions)
        assert not any(r['event']=='step_started' and r['id']=='input' and r['step']==1 for r in rows)
        owners=json.loads((run/'owner-events.json').read_text())
        assert owners[-1]['reason']=='close' and all(r['verified'] for r in owners)
        if case['mode']=='cancel':
            cancel=next(r for r in rows if r['event']=='cancel_requested')
            assert cancel['matched'] and admissions[0]['admitted_ns']<cancel['requested_ns']
        if case['mode']=='expiry':
            accepted=next(r for r in rows if r['event']=='accepted')
            assert admissions[0]['admitted_ns']<accepted['valid_until_ns']<=terminals[0]['terminal_ns']
        result.update(mode=case['mode'],stale_rejected=True,tail_input_absent=True,
                      close_verified=True,game_success_claim=False)
        audited.append(result)
    output=dict(episodes=3,readiness_passes=3,exact_frames=sum(r['exact_frames'] for r in audited),
                qualification=False,results=audited)
    (folder/'audit.json').write_text(json.dumps(output,indent=2))
    print(json.dumps({k:v for k,v in output.items() if k!='results'},indent=2))

if __name__=='__main__':main(Path(sys.argv[1]))
