import copy
import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent
def require(value,message):
    if not value:raise ValueError(message)
def load():
    case=ROOT/'case'
    replies={i:json.loads((case/'replies'/f'{i:03}.json').read_text()) for i in range(1,8)}
    values={i:json.loads((case/'exchange'/f'original-reply-{i}.json').read_text()) for i in range(1,8)}
    meta={i:json.loads(next(b['text'] for b in values[i]['result']['content'] if b['type']=='text')) for i in (1,3,5,7)}
    return {'replies':replies,'values':values,'meta':meta,
      'events':[json.loads(x) for x in (case/'events.jsonl').read_text().splitlines()],
      'host_events':[json.loads(x) for x in (case/'host/host-events.jsonl').read_text().splitlines()],
      'cleanup':json.loads((case/'cleanup.json').read_text()),
      'terminal':json.loads((case/'host-terminal.json').read_text()),
      'captures':len(list((case/'calls').rglob('observation-*.json'))),
      'programs':len(list((case/'calls').rglob('program-guarded-*.json')))}
def audit(data):
    r=data['replies'];m=data['meta'];e=data['events'];h=data['host_events']
    require([x['event'] for x in e]==['save','app_ack'],'one Save and one app acknowledgment')
    require(e[0]['token']=='t1001074' and e[1]['status']=='SAVED','task-bound independent effect')
    sends=[x for x in h if x['kind']=='send_requested']
    require([x['tool'] for x in sends]==['interface_guarded_observe','interface_guarded_mint','interface_guarded_input','interface_close'],'exact public requests')
    require(data['captures']==6 and data['programs']==1,'six captures and one input')
    require(all(x['caller_state']['stopped'] is None for x in r.values()),'no hidden primary STOP')
    require(data['cleanup']['host_exit']==0 and data['cleanup']['child_exit_codes']==[0,-15,0],'terminal owned cleanup')
    require(data['terminal']['exit']=={'code':0,'signal':None},'terminal transport')
    require(m[7]['status']=='closed' and m[7]['release']['verified'] is True and m[7]['release']['keys_down']==[] and m[7]['release']['buttons_down']==[],'explicit neutral close')
    require(m[5]['status']=='completed' and m[5]['feedback']['status']=='matched' and m[5]['feedback']['title']=='SAVED-1001074' and m[5]['feedback']['task_success'] is None and m[5]['feedback']['authority_granted'] is False,'cue completion is not task authority')
    require(all(x['verified'] is True and x['keys_down']==[] and x['buttons_down']==[] for x in m[5]['result']['execution']['releases']),'neutral input release')
    for i in (1,5):
        image=r[i]['images'];require(len(image)==1,'one delivered image')
        blob=(ROOT/'case'/'exchange'/f'image-{i}-1.png').read_bytes()
        digest=hashlib.sha256(blob).hexdigest()
        require(image[0]['sha256']==digest==m[i]['source']['native']['artifact']['sha256'],'file/descriptor/native PNG identity')
        require(image[0]['bytes']==len(blob),'encoded byte count')
    require(m[1]['source']['sequence']==1 and m[5]['source']['sequence']==6,'retained source identities')
    require(m[1]['source']['capture_ns']<e[0]['ns']<e[1]['ns']<=m[5]['source']['capture_ns'],'source-to-effect time order')
    for i in range(1,8):
        request=json.loads((ROOT/'case'/'commands'/f'{i:03}.json').read_text())
        require(request==json.loads((ROOT/'case'/'exchange'/f'request-{i}.json').read_text()),'exact submitted request snapshot')
        require(request['id']==i and r[i]['id']==i and r[i]['next_id']==i+1,'ordered command identities')
        require(data['values'][i]==json.loads((ROOT/'case'/'exchange'/f'original-reply-{i}.json').read_text()),'returned value identity')
    for index,attempt in ((2,1),(6,3)):
        require(data['values'][index]==json.loads((ROOT/'case'/'host'/f'review-{attempt}.json').read_text()),'original explicit image review retained')
    require(data['values'][4]==json.loads((ROOT/'case'/'host'/'text-acknowledgment-2.json').read_text()),'explicit original mint acknowledgment')
    return {'public_requests':4,'primary_commands':7,'delivered_images':2,'primary_image_views':2,
      'native_captures':data['captures'],'input_programs':1,'save_effects':1,'app_acknowledgments':1,
      'app_ack_delay_ms':(e[1]['ns']-e[0]['ns'])/1e6,
      'saved_capture_after_ack_ms':(m[5]['source']['capture_ns']-e[1]['ns'])/1e6,
      'input_command_duration_ms':(int(r[5]['ended_ns'])-int(r[5]['started_ns']))/1e6,
      'saved_review_after_ack_ms':(int(r[6]['ended_ns'])-e[1]['ns'])/1e6,
      'host_first_send_to_close_ms':h[-1]['host_monotonic_ms']-sends[0]['host_monotonic_ms']}
if __name__=='__main__':
    data=load();metrics=audit(data);controls=[]
    for name in ('duplicate-save','unverified-close','changed-image-hash'):
        changed=copy.deepcopy(data)
        if name=='duplicate-save':changed['events'].insert(1,copy.deepcopy(changed['events'][0]))
        elif name=='unverified-close':changed['meta'][7]['release']['verified']=False
        else:changed['replies'][5]['images'][0]['sha256']='0'*64
        try:audit(changed)
        except ValueError as error:controls.append({'name':name,'rejected':True,'reason':str(error)})
        else:raise ValueError('counterexample accepted')
    manifest=json.loads((ROOT/'frozen-manifest.json').read_text())
    require(manifest['source_revision']=='36621a2a91705228f5b236ed91988fc1a57382fa','candidate source pin')
    require(manifest['sha256']==hashlib.sha256((ROOT/'frozen-runtime.pyz').read_bytes()).hexdigest(),'archive source artifact identity')
    repo=ROOT.parents[2]
    for name in ('PLAN.md','keeper.py','fixture.py','host-keeper.mjs'):
        expected=subprocess.check_output(['git','-C',str(repo),'show','712354e5b:runtime/results/primary-exchange-live-01/'+name])
        require((ROOT/name).read_bytes()==expected,'prelaunch scaffold freeze')
    for name in ('primary_exchange.mjs','primary_caller.mjs','relay_client.mjs','relay_host.mjs','README.md','FEEDBACK.md'):
        expected=subprocess.check_output(['git','-C',str(repo),'show',manifest['source_revision']+':runtime/host_v1/'+name])
        require((ROOT/'frozen-host'/name).read_bytes()==expected,'packaged host committed source')
    print(json.dumps({'status':'PASS_FUNCTIONAL','source':manifest['source_revision'],'metrics':metrics,
      'counterexamples':controls,'scope':'One authored app case; not general speed, token, perception or durability proof'},indent=2))
