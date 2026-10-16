"""Audit the preregistered no-model OpenTTD tree-transparency view transform."""
import hashlib,json,sys
from pathlib import Path
from PIL import Image,ImageChops
import audit_openttd_matched_v2 as shared
from append_checkpoint_v1 import load
from received_continuation_v1 import advance,start
HERE=Path(__file__).resolve().parent;ROOT=HERE/'results/openttd-view-transform-01';RUN=ROOT/'run';runtime=RUN/'runtime'
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    prereg=read(ROOT/'preregistration.json');assert prereg['status']=='PREREGISTERED_BEFORE_EXECUTION' and prereg['model_calls']==0
    for name,digest in prereg['sources'].items():
        path=HERE.parent/name if name.startswith('openttd_task/') else HERE/name
        shared.source_with_hash(path,digest)
    manifest=read(runtime/'manifest.json')
    for name,digest in manifest['sources'].items():shared.source_with_hash(HERE.parent/name,digest)
    endpoint=read(ROOT/'endpoint.json');events=[json.loads(line) for line in (runtime/'events.jsonl').read_text().splitlines()];calls=read(ROOT/'calls.json');state=start(endpoint['socket'])
    def replay(exchange):
        nonlocal state
        request,reply=exchange['request'],exchange['reply'];assert request['after']==state['cursor'] and reply['records']==events[request['after']:reply['cursor']];state=advance(state,endpoint['socket'],request['after'],reply);expected=exchange['state']['continuation'] if 'state' in exchange else exchange['continuation'];assert state==expected
    replay(read(ROOT/'initial.json'))
    for call in calls:replay(call);assert call['state']['pending'] is None
    assert load(RUN/'journal.jsonl')==calls[-1]['state'];replay(read(ROOT/'finish.json'))
    assert [call['request']['command']['op'] for call in calls]==['clock','submit','clock','submit'];assert calls[1]['request']['command']['steps']==[{'op':'observe'}] and calls[3]['request']['command']['steps']==[{'op':'chord','modifier':'Control_L','key':'2'},{'op':'observe'}]
    started=[e for e in events if e.get('event')=='step_started'];assert sum(e.get('operation')=='chord' for e in started)==1 and not any(str(e.get('operation','')).startswith('pointer_') for e in started)
    result=read(ROOT/'result.json');evaluation=result['evaluation'];assert result['model_calls']==0 and result['image_changed'] and result['save_unchanged'] and evaluation['success'] is False and evaluation['checks']=={'target_owned_roads':False,'ordered_bidirectional_connections':False,'forbidden_tiles_clear':True,'surrounding_road_owner_unchanged':True} and evaluation['changed_surrounding_tiles']==[]
    before=runtime/result['before_image'];after=runtime/result['after_image'];assert sha(before)==result['before_sha256'] and sha(after)==result['after_sha256']
    with Image.open(before) as a,Image.open(after) as b:
        difference=ImageChops.difference(a.convert('RGB'),b.convert('RGB')).convert('L');hist=difference.histogram();changed=a.width*a.height-hist[0];total=a.width*a.height;dimensions=[a.width,a.height]
    cleanup=read(runtime/'cleanup.json');assert cleanup=={'all_owned_processes_exited':True,'save_unchanged':True}
    report={'audit_passed':True,'preregistered':True,'model_calls':0,'durable_calls':len(calls),'method':{'id':'openttd.transparent_trees','expanded_step':{'op':'chord','modifier':'Control_L','key':'2'},'source_url':prereg['method_url']},'image':{'dimensions':dimensions,'before_sha256':result['before_sha256'],'after_sha256':result['after_sha256'],'changed_pixels':changed,'total_pixels':total,'changed_fraction':changed/total},'task_state':{'independent_success':False,'checks':evaluation['checks'],'changed_surrounding_tiles':[],'save_unchanged':True},'decision':'retain as an app-specific learned view optimizer and expose it separately from task mutation; fresh model recovery remains untested','scope':prereg['scope'],'audit_sha256':sha(Path(__file__))}
    (ROOT/'audit.json').write_bytes((json.dumps(report,indent=2)+'\n').encode('utf-8'));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
