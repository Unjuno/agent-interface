"""Audit retained first pair; no runtime rerun or altered candidate."""
from pathlib import Path
import json,hashlib,copy
from PIL import Image
base=Path(__file__).resolve().parent
def read(path): return json.loads(path.read_text())
def check(ok,reason):
    if not ok: raise ValueError(reason)
def effects(events):
    check(len(events)==2 and events[0]['event']=='save' and events[0]['token']=='t1001072' and events[1]['event']=='app_ack' and events[1]['status']=='SAVED' and events[0]['ns']<events[1]['ns'],'exact once app effect')
reports=[];programs=[];initial=[]
for name,requests,images,final_index,review_index in [('01-immediate',5,3,6,7),('02-cue-wait',4,2,4,5)]:
    case=base/name
    check(read(case/'cleanup.json')['child_exit_codes']==[0,-15,0] and read(case/'cleanup.json')['host_exit']==0,'terminal owned processes')
    rows=[read(p) for p in sorted((case/'replies').glob('*.json'))]
    check(all(row['caller_state']['stopped'] is None for row in rows),'no caller stop')
    events=[json.loads(line) for line in (case/'events.jsonl').read_text().splitlines()];effects(events)
    host_requests=[read(p) for p in sorted((case/'host').glob('request-*.json'))]
    expected=['interface_guarded_observe','interface_guarded_mint','interface_guarded_input']+(['interface_guarded_observe'] if name=='01-immediate' else [])+['interface_close']
    check([r['tool'] for r in host_requests]==expected,'exact public request shape')
    check(len(host_requests)==requests,'request count')
    input_row=rows[3];final=rows[final_index-1]
    check(input_row['metadata']['result']['status']=='completed' and input_row['isError'] is False,'completed input')
    source=final['metadata']['source'];ack=events[1]['ns']
    check(source['capture_ns']>ack,'Saved capture after acknowledgment')
    check(all(r['verified'] is True and r['keys_down']==[] and r['buttons_down']==[] for r in input_row['metadata']['result']['execution']['releases']),'verified neutral release')
    if name=='02-cue-wait':
        check(input_row['metadata']['feedback']['status']=='matched' and input_row['metadata']['feedback']['title']=='SAVED-1001072','cue matched')
        check(host_requests[2]['arguments']['feedback']['timeout_ms']==5000,'frozen cue budget')
    else:
        check('feedback' not in host_requests[2]['arguments'],'baseline no cue')
        check(input_row['metadata']['source']['capture_ns']<ack,'immediate capture before acknowledgment')
    pictures=[r for r in rows if r['image_path']]
    check(len(pictures)==images,'primary image count')
    for row in pictures:
        art=row['metadata']['source']['native']['artifact'];picture=Path(row['image_path']).read_bytes()
        check(picture==Path(art['path']).read_bytes() and hashlib.sha256(picture).hexdigest()==art['sha256'],'original native PNG')
    for row in rows:
        if row['attempt'] is None: continue
        raw=read(case/'host'/('reply-'+str(row['attempt'])+'.json'))['result']
        check(json.loads(next(b['text'] for b in raw['content'] if b['type']=='text'))==row['metadata'],'original host metadata')
    session=next((case/'calls').glob('guarded-session-*'))
    files=list(session.glob('program-guarded-*.json'));check(len(files)==1,'one native program')
    programs.append(read(files[0]));initial.append(Path(rows[0]['image_path']).read_bytes())
    count=len(list(session.glob('observation-*.json')));check(count==(7 if name=='01-immediate' else 6),'capture count')
    image=Image.open(Path(input_row['image_path'])).convert('RGB')
    all_black=all(bounds==(0,0) for bounds in image.getextrema())
    reports.append(dict(arm=name,public_requests=requests,primary_images=images,captures=count,input_programs=1,save_events=1,ack_events=1,input_reply_ms=(int(input_row['ended_ns'])-int(input_row['started_ns']))/1e6,app_ack_delay_ms=(ack-events[0]['ns'])/1e6,first_saved_capture_after_ack_ms=(source['capture_ns']-ack)/1e6,first_saved_reply_after_ack_ms=(int(final['ended_ns'])-ack)/1e6,first_saved_review_record_after_ack_ms=(int(rows[review_index-1]['ended_ns'])-ack)/1e6,first_input_image_all_black=all_black))
check(initial[0]==initial[1],'identical initial PNGs')
for key in ['schema','source','terminal','ops']:check(programs[0][key]==programs[1][key],'same native program shape '+key)
controls=[]
for name in ['duplicate_save','wrong_token','missing_ack']:
    ee=copy.deepcopy(events)
    if name=='duplicate_save':ee.append(copy.deepcopy(ee[0]))
    elif name=='wrong_token':ee[0]['token']='wrong'
    else:ee.pop()
    try:effects(ee)
    except ValueError:controls.append(name)
    else:raise ValueError('effect mutation accepted '+name)
report=dict(status='FUNCTIONAL_PAIR_WITH_PRIMARY_FRAME_REVIEW_ERROR',decision='HOLD_GENERAL_EFFICIENCY',source_revision='5933e45ebe713e9e51682fb13069b8e8f7f979ee',archive_sha256='75f51372d5ccf5a161cbce1a355a594095dc8de3be3185ca983c0368d7a7bcb7',rows=reports,equal_initial_pngs=True,equal_native_ops=True,mutations_rejected=controls,model_tokens=None,billing=None,limitations=['one pair, fixed baseline-first order','primary scaffolding and inspection/tool timing included in later awareness boundaries','review record is attribution, not provider semantic-processing timestamp','baseline primary initially described black frame, but immutable native PNG has nonblack pixels and re-view shows READY; retain perception/presentation error, not native capture failure','app title convention only; exact effect validated by independent events','same current primary model; no provider revision attestation or token-cost comparison'])
(base/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
