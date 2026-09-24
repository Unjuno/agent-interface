"""Independent raw-only verifier. Imports no actor, adapter, extractor, or runner."""
import base64, hashlib, json, sys
from pathlib import Path
CONDITIONS=('STABLE','MOVE_RIGHT','MOVE_LEFT','MISSING_REFERENCE','FOREIGN_REFERENCE','SURFACE_REPLACED')
POLICIES=('CURRENT_GEOMETRY','REFERENCE_GEOMETRY')
ALLOC='cue-frame-geometry-4316-20260924-f4c9'
FLAGS=('grants_authority','task_input','extends_lease','verifies_effect')

def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
def rgb(b):
    out=bytearray(len(b)//4*3);out[0::3]=b[2::4];out[1::3]=b[1::4];out[2::3]=b[0::4];return bytes(out)
def crop(b,width,roi):
    x,y,w,h=roi
    return bytes(b[(row*width+col)*3+ch] for row in range(y,y+h) for col in range(x,x+w) for ch in (0,1,2))
def empty(status):return dict(status=status,local_roi=None,origin_used=None,extraction=None,**{k:False for k in FLAGS})

def audit(source,phase='pilot',evidence=None):
    source=Path(source);evidence=source if evidence is None else Path(evidence);base=evidence/phase
    errors=[];checks=0;rows=[]
    def ck(ok,label):
        nonlocal checks
        checks+=1
        if not ok:errors.append(label)
    n=12 if phase=='pilot' else 6
    ck({p.name for p in base.glob('c*') if p.is_dir()}=={f'c{i:02}' for i in range(n)},'case_set')
    if phase=='pilot':
        try:
            f=read(source/'FREEZE.json')
            for name,h in f['files'].items():ck(sha((source/name).read_bytes())==h,'freeze:'+name)
            ck(f['allocation']==ALLOC and f['pilot_cases']==12 and f['public_preregistration'] is False,'freeze:contract')
        except Exception as e:ck(False,'freeze_unreadable:'+type(e).__name__)
    for i in range(n):
        label=f'c{i:02}';d=base/label
        try:
            r=read(d/'case.json');cond=CONDITIONS[i%6]
            ck(r['index']==i and r['condition']==cond and r['phase']==phase and r['allocation']==ALLOC and r['session']==f'{ALLOC}/{phase}/{label}',label+':identity')
            ck(r['complete'] is True and r['display_cleanup'] is True,label+':completion')
            for name,h in r['source_hashes'].items():ck(sha((source/name).read_bytes())==h,label+':source:'+name)
            ck(set(r['source_hashes'])=={'run.py','actor.py','adapter.py','cue_4316.py'},label+':source_set')
            ck(r['xauth']['returncode']==0,label+':xauth')
            ck(r['abi']['order']=='LSBFirst' and r['abi']['depth']==24 and r['abi']['root_visual']['red']==0xff0000 and r['abi']['root_visual']['green']==0xff00 and r['abi']['root_visual']['blue']==0xff,label+':ABI')
            procs=r['processes'];ck(set(procs)=={'server','actor',*POLICIES},label+':process_set')
            ck(len({p['pid'] for p in procs.values()})==4 and all(type(p['pid']) is int and p['pid']>0 for p in procs.values()),label+':process_ids')
            for p in ('actor',*POLICIES):ck(procs[p]['returncode']==0,label+':exit:'+p)
            ck(procs['server']['returncode'] in (0,-15) and procs['server']['termination']=='SIGTERM',label+':server_exit')
            ck('-nolisten' in procs['server']['argv'] and 'tcp' in procs['server']['argv'] and '-auth' in procs['server']['argv'],label+':display_flags')
            for p in POLICIES:ck(procs[p]['display_present'] is False and (d/(p+'.stderr')).read_bytes()==b'',label+':policy_isolation:'+p)
            ck((d/'actor.stderr').read_bytes()==b'' and r['actor_extra_stdout_b64']=='',label+':actor_streams')
            app=[json.loads(x) for x in (d/'app.jsonl').read_text().splitlines()]
            ck(app[0]['kind']=='BEGIN' and app[-1]['kind']=='END' and app[-1]['input_count']==0 and not any(e['kind']=='INPUT' for e in app),label+':app_events')
            ck(all(app[j]['ns']<=app[j+1]['ns'] for j in range(len(app)-1)),label+':app_order')
            commands=[e['value'] for e in app if e['kind']=='COMMAND'];replies=[e['value'] for e in app if e['kind']=='REPLY']
            rpc=r['rpc'];sent=[json.loads(base64.b64decode(t['sent_b64'])) for t in rpc if t['sent_b64']]
            received=[json.loads(base64.b64decode(t['received_b64'])) for t in rpc]
            ck(sent==commands and received==replies,label+':wire_journal')
            move={'op':'MOVE','x':128 if cond=='MOVE_RIGHT' else 64,'y':64}
            third=move if cond in ('MOVE_RIGHT','MOVE_LEFT') else {'op':'RECREATE'} if cond=='SURFACE_REPLACED' else {'op':'SNAP'}
            ck(commands==[{'op':'DRAW','state':1},{'op':'DRAW','state':2},third,{'op':'SNAP'},{'op':'SNAP'},{'op':'CLOSE'}],label+':commands')
            creates=[e for e in app if e['kind']=='CREATE'];destroys=[e for e in app if e['kind']=='DESTROY']
            ck(len(creates)==(2 if cond=='SURFACE_REPLACED' else 1) and len(destroys)==(1 if cond=='SURFACE_REPLACED' else 0),label+':lifecycle')
            ck(r['before']==r['after'] and r['before']['app']==replies[4] and r['after']['app']==replies[5],label+':no_state_effect')
            inp=r['after']['input'];ck(inp['keymap']==[0]*32 and inp['buttons']==0 and inp['focus']==r['after']['app']['surface'],label+':neutral')
            captures=r['captures'];ck(len(captures)==4,label+':captures')
            images=[];roots=[]
            for j,c in enumerate(captures):
                raw=(d/c['raw_file']).read_bytes();rootraw=(d/c['root_file']).read_bytes();im=rgb(raw);rt=rgb(rootraw)
                ck(len(raw)==32768 and len(rootraw)==245760,label+f':image_size:{j}')
                ck(sha(raw)==c['raw_sha256'] and sha(im)==c['rgb_sha256'] and sha(rootraw)==c['root_raw_sha256'] and sha(rt)==c['root_rgb_sha256'],label+f':image_hash:{j}')
                origin=[96,64] if j<2 or cond not in ('MOVE_RIGHT','MOVE_LEFT') else [128 if cond=='MOVE_RIGHT' else 64,64]
                generation=2 if cond=='SURFACE_REPLACED' and j>=2 else 1
                ck(c['sequence']==j+1 and c['origin']==origin and c['generation']==generation and c['session']==r['session'] and c['intent']==7 and c['root_size']==[320,192],label+f':capture_meta:{j}')
                ck(c['surface']==creates[generation-1]['surface'],label+f':capture_surface:{j}')
                ck(0<c['capture_start_ns']<=c['capture_end_ns'] and (j==0 or captures[j-1]['capture_end_ns']<c['capture_start_ns']),label+f':capture_time:{j}')
                ck(crop(rt,320,[*c['origin'],128,64])==im,label+f':root_window_correspondence:{j}')
                images.append(im);roots.append(rt)
            ck(images[2]==images[3] and roots[2]==roots[3],label+':no_pixel_effect')
            ck(images[0]!=images[1],label+':two_temporal_states')
            ck(captures[1]['capture_end_ns']<next(e['ns'] for e in app if e['kind']=='COMMAND' and e['value']==third),label+':cue_before_change')
            cue=dict(cue_id=r['session']+'/cue',reference_id=captures[1]['frame_id'],reference_sha256=captures[1]['root_rgb_sha256'],
                     emitted_ns=captures[1]['capture_end_ns'],clock='MONOTONIC',screen_roi=[144,80,32,32],
                     session=r['session'],surface=captures[1]['surface'],generation=1,intent=7)
            refs=[captures[1].copy()]
            if cond=='MISSING_REFERENCE':refs=[]
            elif cond=='FOREIGN_REFERENCE':refs[0]['root_rgb_sha256']='0'*64
            req=read(d/'request.json');ck(req['cue']==cue and req['references']==refs and req['current']==captures[2],label+':request_anchor')
            frames=[dict(rgb_b64=base64.b64encode(images[j]).decode(),**captures[j]) for j in (0,1)]
            ck(req['frames']==frames and captures[2]['capture_end_ns']<req['now_ns'] and 0<=req['now_ns']-cue['emitted_ns']<=5_000_000_000,label+':request_history')
            for policy in POLICIES:
                p=procs[policy];ck(p['request_sha256']==sha((d/'request.json').read_bytes()) and p['start_ns']>req['now_ns'] and p['end_ns']>=p['start_ns'],label+':policy_request:'+policy)
                output=read(d/(policy+'.json'));ck(p['response_bytes']==(d/(policy+'.json')).stat().st_size,label+':response_size:'+policy)
                status={'MISSING_REFERENCE':'HOLD_REFERENCE','FOREIGN_REFERENCE':'REJECT_REFERENCE','SURFACE_REPLACED':'REJECT_SCOPE'}.get(cond,'ATTENTION_READY')
                expected=empty(status);wrong_pixels=0
                if status=='ATTENTION_READY':
                    o=captures[2]['origin'] if policy=='CURRENT_GEOMETRY' else captures[1]['origin']
                    local=[144-o[0],80-o[1],32,32]
                    items=[]
                    for j in (0,1):
                        b=crop(images[j],128,local)
                        items.append(dict(sequence=j+1,source_sha256=sha(images[j]),capture_end_ns=captures[j]['capture_end_ns'],roi=local,
                                          bytes=len(b),rgb_b64=base64.b64encode(b).decode(),sha256=sha(b)))
                        # Scoring anchor is the exact earlier ROOT screenshot region, not policy output.
                        truth=crop(roots[j],320,cue['screen_roi'])
                        wrong_pixels+=sum(b[k:k+3]!=truth[k:k+3] for k in range(0,len(b),3))
                    response=dict(status='ATTENTION_READY',images=items,rgb_bytes=6144,available_history=None,**{k:False for k in FLAGS})
                    expected.update(local_roi=local,origin_used=o,reference_id=cue['reference_id'],
                                    extraction=dict(responses=[response],**{k:False for k in FLAGS}))
                ck(output==expected,label+':exact_response:'+policy)
                ck(wrong_pixels==(2048 if status=='ATTENTION_READY' and policy=='CURRENT_GEOMETRY' and cond in ('MOVE_RIGHT','MOVE_LEFT') else 0),label+':scoped_pixel_gate:'+policy)
                rows.append(dict(case=label,condition=cond,policy=policy,status=status,wrong_pixels=wrong_pixels,
                                 rgb_bytes=6144 if status=='ATTENTION_READY' else 0,wire_bytes=p['response_bytes']))
        except Exception as e:ck(False,label+':unreadable:'+type(e).__name__)
    batches=[list(range(j,j+2)) for j in range(0,12,2)] if phase=='pilot' else [list(range(6))]
    for indices in batches:
        try:
            b=read(base/f'batch-{indices[0]:02}.json')
            ck(b['indices']==indices and b['completed']==indices and b['status']=='COMPLETE' and b['end_ns']>=b['start_ns'],'batch:'+str(indices[0]))
            if phase=='pilot':
                l=read(evidence/f'LAUNCH_{indices[0]:02}.json');ck(l['returncode']==0 and l['timeout'] is False,'launcher:'+str(indices[0]))
        except Exception as e:ck(False,'batch_unreadable:'+str(indices[0])+':'+type(e).__name__)
    summary={p:dict(observations=sum(x['policy']==p for x in rows),ready=sum(x['policy']==p and x['status']=='ATTENTION_READY' for x in rows),
                    wrong_crop_cases=sum(x['policy']==p and x['wrong_pixels']>0 for x in rows),wrong_pixels=sum(x['wrong_pixels'] for x in rows if x['policy']==p)) for p in POLICIES}
    return dict(status='PASS_LOCAL_FRAME_COORDINATE_BOUNDARY' if not errors else 'FAIL_OR_HOLD',phase=phase,
                planned_cases=n,checks=checks,errors=errors,summary=summary,rows=rows,gui_runs=0)

if __name__=='__main__':
    answer=audit(Path(sys.argv[1]),sys.argv[2] if len(sys.argv)>2 else 'pilot')
    print(json.dumps(answer,sort_keys=True,indent=2));sys.exit(bool(answer['errors']))
