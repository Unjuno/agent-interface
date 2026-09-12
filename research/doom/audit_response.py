"""Audit exploratory response cohorts, keeping input and game outcomes separate."""
import hashlib,json
from pathlib import Path
from audit import audit

HERE=Path(__file__).resolve().parent
COHORTS=('response-01','refresh-diagnostic-01','attack-response-01','delta-response-01')

def main():
    reports=[]
    for name in COHORTS:
        root=HERE/'results'/name;manifest=json.loads((root/'manifest.json').read_text())
        for source,digest in manifest['sources'].items():
            assert hashlib.sha256((HERE/source).read_bytes()).hexdigest()==digest,source
        folder=root/'0';result=audit(folder)
        result['scope']='scripted response diagnostic; not assistant gameplay or performance comparison'
        rows=[json.loads(x) for x in (folder/'events.jsonl').read_text().splitlines()]
        assert rows==[json.loads(x) for x in (folder/'delivered.jsonl').read_text().splitlines()]
        owner=json.loads((folder/'owner-events.json').read_text())
        assert owner[-1]['reason']=='close' and all(r['verified'] for r in owner)
        state=json.loads((folder/'post-control-angle.json').read_text())
        score=result['post_control_score']
        if name=='attack-response-01':
            assert state['initial']['AMMO2']==50 and state['final']['AMMO2']==49
            assert score['episode_finished'] and not score['player_dead']
        else:
            before=state.get('initial',{}).get('ANGLE',state.get('initial_angle'))
            after=state.get('final',{}).get('ANGLE',state.get('final_angle'))
            assert before==after==0 and not score['episode_finished']
        result.update(post_control_state=state,qualification=False)
        (root/'audit.json').write_text(json.dumps(result,indent=2))
        reports.append(dict(cohort=name,exact_frames=result['exact_frames'],game_finished=score['episode_finished']))
    print(json.dumps(reports,indent=2))

if __name__=='__main__':main()
