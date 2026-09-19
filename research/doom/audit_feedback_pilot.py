"""Audit every preregistered pilot case, retaining failed/aborted outcomes."""
import hashlib,json
from pathlib import Path
from PIL import Image
from audit import audit

HERE=Path(__file__).resolve().parent

def main():
    root=HERE/'results/feedback-pilot-01';plan=json.loads((root/'plan.json').read_text())
    for name,digest in plan['sources'].items():assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==digest
    results=[];initial={}
    for case in plan['cases']:
        folder=root/case['id'];run=folder/'runtime';m=json.loads((folder/'manifest.json').read_text())
        assert m['seed']==case['seed'] and m['sources']==plan['sources']
        report=audit(run)
        rows=[json.loads(x) for x in (run/'events.jsonl').read_text().splitlines()]
        client=[json.loads(x) for x in (folder/'client.jsonl').read_text().splitlines()]
        assert rows==[json.loads(x) for x in (run/'delivered.jsonl').read_text().splitlines()]
        assert rows==[x['record'] for x in client if x['event']=='runtime_received']
        assert client[-1]['event']=='client_closed' and client[-1]['child_returncode']==0 and not client[-1]['errors']
        assert not client[-1]['reader_alive']
        commands=[r for r in rows if r['event']=='command'];accepts=[r for r in rows if r['event']=='accepted']
        assert [r['command'] for r in commands]==[r['command'] for r in client if r['event']=='command_received']
        owner=json.loads((run/'owner-events.json').read_text());assert owner[-1]['reason']=='close' and all(r['verified'] for r in owner)
        finish=next(r for r in commands if r['command']['op']=='finish')
        score=report['post_control_score'];success=score['episode_finished'] and not score['player_dead']
        rejected=[r for r in rows if r['event']=='rejected']
        if case['id']=='a2':
            assert len(rejected)==1 and 'expired' in rejected[0]['reason'] and not success
            assert not any(r['id']=='fire' for r in accepts)
            assert [r['command']['steps'] for r in commands if r['command'].get('id')=='recover-observe']==[[{'op':'observe'}]]
            assert [r['key'] for r in rows if r['event']=='input_admission']==['Left']
        else:assert success and not rejected
        obs=[r for r in rows if r['event']=='observation']
        with Image.open(run/Path(obs[0]['image']).name) as im:initial[case['id']]=im.convert('RGB').crop((321,181,961,580)).tobytes()
        with Image.open(run/Path(obs[-1]['image']).name) as im:
            pix=list(im.convert('RGB').crop((321,181,961,580)).getdata())
            nonblack=sum(any(c>15 for c in rgb) for rgb in pix)/len(pix)
        result=dict(**case,success=success,exact_frames=report['exact_frames'],accepted_programs=len(accepts),
            rejected=len(rejected),clock_commands=sum(r['command']['op']=='clock' for r in commands),
            first_accept_to_finish_command_seconds=(finish['received_ns']-accepts[0]['accepted_ns'])/1e9,
            between_accepts_seconds=[(b['accepted_ns']-a['accepted_ns'])/1e9 for a,b in zip(accepts,accepts[1:])],
            final_world_nonblack_fraction=nonblack,
            disposition='completed' if success else 'aborted after expired shot and perceived black recovery presentation; saved PNG contains scene; not successful completion')
        results.append(result)
    assert initial['a1']==initial['b1'] and initial['a2']==initial['b2']
    output=dict(results=results,paired_initial_world_pixels_identical=True,total_exact_frames=sum(r['exact_frames'] for r in results),
        study_status='pilot completed; no statistical promotion',qualification=False,
        outcome='combined 2/2 complete; separate 1/2 complete; failure retained, no aggregate speedup claim')
    (root/'audit.json').write_text(json.dumps(output,indent=2));print(json.dumps(output,indent=2))

if __name__=='__main__':main()
