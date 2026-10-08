import base64
import copy
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parent
def require(value,message):
    if not value:raise ValueError(message)
def load():
    case=ROOT/'case';raw=(case/'primary-stream.jsonl').read_bytes()
    rows=[json.loads(line) for line in raw.decode().splitlines()]
    replies={row['result']['id']:row['result'] for row in rows if row['status']=='returned'}
    values={i:json.loads((case/'exchange'/f'original-reply-{i}.json').read_text()) for i in range(1,8)}
    meta={i:json.loads(next(b['text'] for b in values[i]['result']['content'] if b['type']=='text')) for i in (1,3,5,7)}
    return {'raw':raw,'rows':rows,'replies':replies,'values':values,'meta':meta,
      'events':[json.loads(x) for x in (case/'events.jsonl').read_text().splitlines()],
      'host_events':[json.loads(x) for x in (case/'host/host-events.jsonl').read_text().splitlines()],
      'cleanup':json.loads((case/'cleanup.json').read_text()),
      'captures':len(list((case/'calls').rglob('observation-*.json'))),
      'programs':len(list((case/'calls').rglob('program-guarded-*.json')))}
def audit(data):
    r=data['replies'];m=data['meta'];e=data['events'];h=data['host_events'];rows=data['rows']
    require(b'\x1b' not in data['raw'],'raw JSON stream has no terminal rendering')
    require([x['status'] for x in rows]==['ready']+['returned']*7+['terminal'],'exact stream without busy/refused/replayed commands')
    require(all(x['schema']=='agent-interface/primary-stdio-v1' for x in rows),'typed stream records')
    require([x['event'] for x in e]==['save','app_ack'] and e[0]['token']=='t1001075' and e[1]['status']=='SAVED','single independent task-bound Save/ack')
    sends=[x for x in h if x['kind']=='send_requested']
    require([x['tool'] for x in sends]==['interface_guarded_observe','interface_guarded_mint','interface_guarded_input','interface_close'],'four exact public requests')
    require(data['captures']==6 and data['programs']==1,'six captures and one input')
    require(all(x['caller_state']['stopped'] is None for x in r.values()),'no hidden STOP or recovery')
    require(data['cleanup']['host_exit']==0 and data['cleanup']['child_exit_codes']==[0,-15,0],'owned terminal cleanup')
    require(rows[-1]['exit']=={'code':0,'signal':None} and rows[-1]['state']['next_id']==8,'original transport terminal')
    require(m[7]['status']=='closed' and m[7]['release']['verified'] is True and m[7]['release']['keys_down']==[] and m[7]['release']['buttons_down']==[],'explicit neutral public close')
    require(m[5]['status']=='completed' and m[5]['feedback']['status']=='matched' and m[5]['feedback']['title']=='SAVED-1001075' and m[5]['feedback']['task_success'] is None and m[5]['feedback']['authority_granted'] is False,'matched cue does not grant authority or task success')
    releases=m[5]['result']['execution']['releases']
    require(releases and all(x['verified'] is True and x['keys_down']==[] and x['buttons_down']==[] for x in releases),'neutral input release')
    for i in (1,5):
        blob=(ROOT/'case'/'exchange'/f'image-{i}-1.png').read_bytes()
        images=r[i]['images'];require(len(images)==1,'one image per image-bearing response')
        digest=hashlib.sha256(blob).hexdigest()
        require(images[0]['sha256']==digest==m[i]['source']['native']['artifact']['sha256'],'native/file/descriptor identity')
        block=next(b for b in data['values'][i]['result']['content'] if b['type']=='image')
        require(base64.b64decode(block['data'],validate=True)==blob,'returned raw image unchanged')
    require(m[1]['source']['sequence']==1 and m[5]['source']['sequence']==6,'original capture identity')
    require(m[1]['source']['capture_ns']<e[0]['ns']<e[1]['ns']<=m[5]['source']['capture_ns'],'source/effect time order')
    for i in range(1,8):
        require(r[i]==json.loads((ROOT/'case'/'exchange'/f'presentation-{i}.json').read_text()),'raw stdout/full result file identity')
        request=json.loads((ROOT/'case'/'exchange'/f'request-{i}.json').read_text())
        require(request['id']==i and r[i]['id']==i and r[i]['next_id']==i+1,'ordered command identities')
    for index,attempt in ((2,1),(6,3)):
        require(data['values'][index]==json.loads((ROOT/'case'/'host'/f'review-{attempt}.json').read_text()),'explicit original image review')
    require(data['values'][4]==json.loads((ROOT/'case'/'host'/'text-acknowledgment-2.json').read_text()),'original mint acknowledgment')
    require(not (ROOT/'case'/'commands').exists() and not (ROOT/'case'/'replies').exists(),'no caller command/reply file-spool directories')
    presented=next(x for x in h if x['kind']=='presentation_callbacks_completed' and x['attempt']==3)
    review=next(x for x in h if x['kind']=='review_recorded' and x['attempt']==3)
    input_send=next(x for x in sends if x['attempt']==3)
    return {'public_requests':4,'primary_commands':7,'raw_stream_records':9,'delivered_images':2,'primary_image_views':2,
      'native_captures':6,'input_programs':1,'save_effects':1,'app_acknowledgments':1,
      'app_ack_delay_ms':(e[1]['ns']-e[0]['ns'])/1e6,
      'saved_capture_after_ack_ms':(m[5]['source']['capture_ns']-e[1]['ns'])/1e6,
      'input_request_to_file_presentation_ms':presented['host_monotonic_ms']-input_send['host_monotonic_ms'],
      'input_file_presentation_to_review_ms':review['host_monotonic_ms']-presented['host_monotonic_ms'],
      'host_first_send_to_close_ms':h[-1]['host_monotonic_ms']-sends[0]['host_monotonic_ms']}
if __name__=='__main__':
    data=load();metrics=audit(data);controls=[]
    for name in ('duplicate-save','unverified-close','missing-input-release','changed-image-hash','stream-terminal-control'):
        changed=copy.deepcopy(data)
        if name=='duplicate-save':changed['events'].insert(1,copy.deepcopy(changed['events'][0]))
        elif name=='unverified-close':changed['meta'][7]['release']['verified']=False
        elif name=='missing-input-release':changed['meta'][5]['result']['execution']['releases']=[]
        elif name=='changed-image-hash':changed['replies'][5]['images'][0]['sha256']='0'*64
        else:changed['raw']+=b'\x1b[0m'
        try:audit(changed)
        except ValueError as error:controls.append({'name':name,'rejected':True,'reason':str(error)})
        else:raise ValueError('counterexample accepted')
    manifest=json.loads((ROOT/'frozen-manifest.json').read_text());repo=ROOT.parents[2]
    require(manifest['sha256']==hashlib.sha256((ROOT/'frozen-runtime.pyz').read_bytes()).hexdigest(),'archive identity')
    for name in ('primary_stdio.mjs','primary_exchange.mjs','primary_caller.mjs','relay_client.mjs','relay_host.mjs','README.md','FEEDBACK.md'):
        expected=subprocess.check_output(['git','-C',str(repo),'show',manifest['source_revision']+':runtime/host_v1/'+name])
        require((ROOT/'frozen-host'/name).read_bytes()==expected,'committed source export')
    for name in ('PLAN.md','keeper.py','fixture.py'):
        expected=subprocess.check_output(['git','-C',str(repo),'show','db13a84d5d138f7d76eca00212f4c2e21dff0cf3:runtime/results/primary-stdio-live-01/'+name])
        require((ROOT/name).read_bytes()==expected,'prelaunch scaffold freeze')
    print(json.dumps({'status':'PASS_GUARDED_PRIMARY_STDIO','source':manifest['source_revision'],
      'metrics':metrics,'counterexamples':controls,'scope':'One authored primary GUI case, not general model speed/token/authority proof'},indent=2))
