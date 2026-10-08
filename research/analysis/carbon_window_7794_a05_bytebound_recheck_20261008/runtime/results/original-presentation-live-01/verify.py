import copy
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parent
def require(condition,message):
    if not condition:raise ValueError(message)
def load():
    case=ROOT/'case'
    return {'replies':{index:json.loads((case/'replies'/f'{index:03}.json').read_text()) for index in range(1,11)},
            'events':[json.loads(line) for line in (case/'events.jsonl').read_text().splitlines()],
            'host_events':[json.loads(line) for line in (case/'host/host-events.jsonl').read_text().splitlines()],
            'cleanup':json.loads((case/'cleanup.json').read_text()),
            'terminal':json.loads((case/'host-terminal.json').read_text()),
            'original_review':json.loads((case/'host/review-1.json').read_text()),
            'images':{index:(case/f'primary-{index:03}.png').read_bytes() for index in [1,5,7,8]},
            'captures':len(list((case/'calls').rglob('observation-*.json'))),
            'programs':len(list((case/'calls').rglob('program-guarded-*.json')))}
def audit(data):
    r=data['replies']; events=data['events']; host=data['host_events']
    require([event['event'] for event in events]==['save','app_ack'],'exact single app Save/ack')
    require(events[0]['token']=='t1001073' and events[1]['status']=='SAVED','task-bound effect')
    sends=[event for event in host if event['kind']=='send_requested']
    require([event['tool'] for event in sends]==['interface_guarded_observe','interface_guarded_mint',
            'interface_guarded_input','interface_guarded_observe','interface_close'],'exact public route/count')
    require(data['captures']==7 and data['programs']==1,'bounded native captures and one input program')
    require(all(reply['caller_state']['stopped'] is None for reply in r.values()),'no hidden primary STOP')
    require(data['cleanup']['host_exit']==0 and data['cleanup']['child_exit_codes']==[0,-15,0],
            'recorded terminal cleanup, controlled app termination retained')
    require(data['terminal']['exit']=={'code':0,'signal':None},'terminal original transport')
    require(r[10]['metadata']['status']=='closed' and r[10]['isError'] is False,'explicit close')
    for index in [1,5,8]:
        meta=r[index]['metadata']; blob=data['images'][index]
        require(hashlib.sha256(blob).hexdigest()==meta['source']['native']['artifact']['sha256'],
                'original primary/native PNG identity')
    require(data['images'][1]==data['images'][5]==data['images'][7],'original pixel bytes unchanged')
    require(data['images'][8]!=data['images'][1],'new visible state has distinct pixels')
    require(r[7]['metadata']=={'presentation_only':True,'source_attempt':1} and r[7]['attempt'] is None,
            'presentation is not a new attempt')
    represented=[json.loads(value) for value in r[7]['presented_text'] if isinstance(value,str)]
    require(represented==[r[1]['metadata']],'re-present entire original source metadata unchanged')
    require(data['original_review']==r[2]['metadata'],'original exclusive review unchanged')
    presentations=[event for event in host if event['kind']=='presentation_callbacks_completed' and event['attempt']==1]
    require(len(presentations)==2 and presentations[0]['reply_sha256']==presentations[1]['reply_sha256'],
            'two same-reply presentations')
    source1=r[1]['metadata']['source']; source6=r[5]['metadata']['source']; source7=r[8]['metadata']['source']
    require(source1['sequence']==1 and source6['sequence']==6 and source7['sequence']==7,'capture identities retained')
    require(source1['capture_ns']<events[0]['ns']<events[1]['ns']<int(r[7]['started_ns'])<source7['capture_ns'],
            'historical re-presentation after ack versus later acquisition')
    releases=r[5]['metadata']['result']['execution']['releases']
    require(releases and all(item['verified'] and item['keys_down']==[] and item['buttons_down']==[] for item in releases),
            'verified neutral input release')
    require(r[5]['metadata']['status']=='completed' and r[5]['isError'] is False,'completed input, not task inference')
    return {'public_requests':len(sends),'delivered_primary_images':4,'primary_image_views':5,
            'native_captures':data['captures'],'input_programs':data['programs'],'save_effects':1,'app_acknowledgments':1,
            'app_ack_delay_ms':(events[1]['ns']-events[0]['ns'])/1e6,
            're_presentation_after_ack_ms':(int(r[7]['started_ns'])-events[1]['ns'])/1e6,
            'fresh_saved_capture_after_ack_ms':(source7['capture_ns']-events[1]['ns'])/1e6,
            're_presentation_local_duration_ms':(int(r[7]['ended_ns'])-int(r[7]['started_ns']))/1e6,
            'host_first_send_to_close_ms':host[-1]['host_monotonic_ms']-sends[0]['host_monotonic_ms'],
            'original_png_sha256':hashlib.sha256(data['images'][1]).hexdigest(),
            'fresh_png_sha256':hashlib.sha256(data['images'][8]).hexdigest()}
data=load();metrics=audit(data)
mutations=[]
for name in ['duplicate-save','changed-represented-source','unverified-release']:
    altered=copy.deepcopy(data)
    if name=='duplicate-save':altered['events'].insert(1,copy.deepcopy(altered['events'][0]))
    elif name=='changed-represented-source':
        values=altered['replies'][7]['presented_text'];meta=json.loads(values[1]);meta['source']['capture_ns']+=1;values[1]=json.dumps(meta)
    else:altered['replies'][5]['metadata']['result']['execution']['releases'][0]['verified']=False
    try:audit(altered)
    except ValueError as error:mutations.append({'name':name,'rejected':True,'reason':str(error)})
    else:raise ValueError('counterexample accepted '+name)
manifest=json.loads((ROOT/'frozen-manifest.json').read_text())
for name in ['PLAN.md','keeper.py','fixture.py','host-keeper.mjs']:
    expected=subprocess.check_output(['git','-C',str(ROOT.parents[2]),'show',
        manifest['source_revision']+':runtime/results/original-presentation-live-01/'+name])
    require((ROOT/name).read_bytes()==expected,'frozen scaffold changed')
print(json.dumps({'status':'PASS_FUNCTIONAL_WITH_PRIMARY_PRESENTATION_DISCREPANCY','source':manifest['source_revision'],
    'archive_sha256':hashlib.sha256((ROOT/'frozen-runtime.pyz').read_bytes()).hexdigest(),
    'metrics':metrics,'counterexamples':mutations,
    'scope':'Finite functional original-source/cleanup/effect audit, not independent model comprehension or performance benefit'},indent=2))
