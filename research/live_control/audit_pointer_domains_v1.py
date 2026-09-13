"""Audit fixed-v9 adapter integration, including retained startup failure."""
import hashlib,json,sys
from pathlib import Path
from PIL import Image
from session_v4 import Decoder

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'openttd_task'))
from guarded_score import score as road_score
sys.path.insert(0,str(HERE.parent/'benchmark_discovery'))
from mindustry_build_score_v1 import score as flow_score

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    fail=HERE/'results/pointer-domains-01/openttd'
    assert read(fail/'result.json')['success'] is False
    assert read(fail/'result.json')['bridge_returncode']==2
    assert read(fail/'records.json')==[]
    assert '--controller' in (fail/'stderr.txt').read_text()
    rows={}
    for cohort,domain in [('pointer-domains-01','mindustry'),('pointer-domains-02','openttd')]:
        root=HERE/'results'/cohort;out=root/domain;runtime=out/'runtime'
        for path,digest in read(root/'plan.json')['sources'].items():assert sha(HERE.parent/path)==digest,path
        for path,digest in read(runtime/'manifest.json')['sources'].items():assert sha(HERE.parent/path)==digest,path
        result=read(out/'result.json');assert result['success'] and result['bridge_returncode']==0
        records=read(out/'records.json');raw=[json.loads(l) for l in (runtime/'events.jsonl').read_text().splitlines()]
        assert records==raw
        prefix=[];cursor=0
        for exchange in read(out/'exchanges.json'):
            reply=exchange['reply'];assert reply['cursor']==cursor+len(reply['records'])
            prefix+=reply['records'];cursor=reply['cursor']
        assert prefix==raw
        decoder=Decoder('live-control');count=0
        for event in raw:
            if event['event']!='observation':continue
            count+=1;assert event['sequence']==count
            frame=decoder.accept((runtime/f'{count:03d}.ait').read_bytes())
            with Image.open(runtime/Path(event['image']).name) as im:
                assert (im.width,im.height,im.mode,im.tobytes())==(frame.width,frame.height,frame.mode,frame.pixels)
        assert not any(e['event']=='accepted' and e['id']=='expired' for e in raw)
        assert any(e['event']=='cancel_requested' and e['id']=='cancel-hold' and e['matched'] is True for e in raw)
        terminals=[e for e in raw if e['event']=='terminal']
        assert terminals[0]['id']=='cancel-hold' and terminals[0]['status']=='cancelled'
        assert all(t['release']['verified'] is True for t in terminals)
        assert all(t['status']=='completed' for t in terminals[1:])
        cleanup=read(runtime/'cleanup.json');assert cleanup['all_owned_processes_exited'] and cleanup['save_unchanged']
        if domain=='openttd':
            evidence=read(runtime/'evaluation.json');value=road_score(evidence['observation'],evidence['baseline']);assert value['success']
        else:
            value=flow_score(*[read(runtime/n) for n in ('before.json','delivery-before.json','after.json')],read(HERE.parent/'benchmark_discovery/mindustry_flow_plan_v1.json'))
            assert value==read(runtime/'evaluation.json') and value['contract_satisfied'] is True
        rows[domain]={'cohort':cohort,'exact_frames':count,'prefix_records':len(raw),
                      'completed_task_programs':len(terminals)-1,'expired_rejected':True,
                      'active_cancel_released':True,'independent_score':value,
                      'controller':'scripted replay; not an actual-use pair'}
    summary={'retained_startup_failure':'OpenTTD missing --controller, no runtime records/input, exit 2',
             'domains':rows,'scope':'adapter readiness and two live stress checks only; no performance qualification',
             'source_sha256':sha(Path(__file__))}
    target=HERE/'results/pointer-domains-audit-01.json';target.write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
