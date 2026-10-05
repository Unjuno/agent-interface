"""Frozen independent auditor: raw pixels, app events, model streams, receipts."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib
from review_audit import expected
ROOT=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def pixel_errors(xwd,png):
    try:
        h=struct.unpack('>25I',xwd[:100]);width,height=h[4:6];base=h[0]+12*h[19]
        if h[1:4]!=(7,2,24) or h[6]!=0 or h[7] not in (0,1) or h[11]!=32 or h[13:17]!=(4,0xff0000,0xff00,0xff) or len(xwd)!=base+h[12]*height:return ['xwd_layout']
        if png[:8]!=b'\x89PNG\r\n\x1a\n':return ['png_signature']
        at=8;compressed=b'';names=[];shape=None
        while at<len(png):
            n=struct.unpack('>I',png[at:at+4])[0];name=png[at+4:at+8];blob=png[at+8:at+8+n]
            crc=struct.unpack('>I',png[at+8+n:at+12+n])[0]
            if zlib.crc32(name+blob)&0xffffffff!=crc:return ['png_crc']
            names.append(name)
            if name==b'IHDR':shape=struct.unpack('>IIBBBBB',blob)
            elif name==b'IDAT':compressed+=blob
            elif name==b'IEND' and blob:return ['png_end']
            at+=12+n
        if names!=[b'IHDR',b'IDAT',b'IEND'] or at!=len(png) or shape!=(width,height,8,2,0,0,0):return ['png_layout']
        decoded=zlib.decompress(compressed)
        if len(decoded)!=(width*3+1)*height:return ['png_length']
        for y in range(height):
            if decoded[y*(width*3+1)]!=0:return ['png_filter']
            for x in range(width):
                offset=base+y*h[12]+x*4;four=xwd[offset:offset+4]
                rgb=four[2::-1] if h[7]==0 else four[1:4]
                start=y*(width*3+1)+1+x*3
                if decoded[start:start+3]!=rgb:return ['pixel_identity']
        return []
    except (ValueError,IndexError,struct.error,zlib.error):return ['malformed_pixels']
def model_value(rows):
    starts=[r['thread_id'] for r in rows if r.get('type')=='thread.started']
    ends=[r['usage'] for r in rows if r.get('type')=='turn.completed']
    answers=[r['item']['text'] for r in rows if r.get('type')=='item.completed' and r.get('item',{}).get('type')=='agent_message']
    if len(starts)!=1 or len(ends)!=1 or len(answers)!=1:raise ValueError('model completion')
    for row in rows:
        if row.get('type') in ('error','turn.failed') or row.get('type','').startswith('item.') and row.get('item',{}).get('type') not in ('agent_message','reasoning'):raise ValueError('model tool/error')
    usage=ends[0];answer=json.loads(answers[0])
    if set(usage)!={'input_tokens','cached_input_tokens','output_tokens'} or any(type(v) is not int or v<0 for v in usage.values()) or usage['cached_input_tokens']>usage['input_tokens']:raise ValueError('usage')
    if set(answer)!={'decision','observed_target','observed_decoy','prefix'} or any(type(v) is not str for v in answer.values()) or answer['decision'] not in ('NO_REPAIR','INSERT_PREFIX','REFUSE'):raise ValueError('schema')
    if answer['decision']=='INSERT_PREFIX' and len(answer['prefix'])!=1 or answer['decision']!='INSERT_PREFIX' and answer['prefix']!='':raise ValueError('prefix schema')
    return dict(answer=answer,usage=usage,call_id=starts[0])
def process_errors(directory,receipt,argv,prompt_sha=None):
    errors=[]
    attempt=json.loads((directory/'attempt.json').read_bytes())
    if receipt['argv']!=argv or attempt['argv']!=argv or attempt['started_utc']!=receipt['started_utc']:errors.append('process_argv_attempt')
    if receipt['output_sha256']!={name:sha(directory/name) for name in ('attempt.json','stdout.bin','stderr.bin')}:errors.append('process_streams')
    if prompt_sha is not None and (receipt['prompt_sha256']!=prompt_sha or attempt['prompt_sha256']!=prompt_sha):errors.append('process_prompt')
    start=datetime.fromisoformat(receipt['started_utc']);end=datetime.fromisoformat(receipt['finished_utc'])
    if start.tzinfo is None or end.tzinfo is None or end<start or type(receipt['wall_seconds']) not in (int,float) or receipt['wall_seconds']<=0 or abs((end-start).total_seconds()-receipt['wall_seconds'])>1:errors.append('process_clock')
    if type(receipt['exit_code']) is not int or receipt['exit_code']!=0 or receipt.get('timed_out',False) or receipt['launch_error'] is not None:errors.append('process_exit')
    return errors
def inspect(results,source=ROOT):
    errors=[];observations=[]
    try:
        results=Path(results);source=Path(source)
        frozen=sha(source/'FREEZE.json');freeze=json.loads((source/'FREEZE.json').read_bytes())
        hashes={name:sha(source/name) for name in freeze['sha256']}
        if hashes!=freeze['sha256']:errors.append('source_hash')
        required={'app.py','candidate.py','xwd_png.py','model_runner.py','model_contract.py','review_audit.py','audit.py','host_capture.py','fixture.json','prompt.txt','response.schema.json'}
        if not required<=set(hashes):errors.append('source_coverage')
        data=results/'review01-candidate-data';models=results/'review01-model-data'
        raw_path=data/'candidate_stdout.json';raw=json.loads(raw_path.read_bytes())
        fixture=json.loads((source/'fixture.json').read_bytes())
        if raw['fixture']!=fixture or raw['fixture_sha256']!=sha(source/'fixture.json') or raw['freeze_sha256']!=frozen or raw['source_sha256']!=hashes or raw['image_id']!=fixture['image_id'] or raw['error'] or raw['model_calls']!=0 or len(raw['rows'])!=4:errors.append('stimulus_identity')
        first_receipt=json.loads((results/'review01-candidate-launch/receipt.json').read_bytes())
        binding={'source_commit':first_receipt['binding']['source_commit'],'freeze_sha256':frozen,'source_sha256':hashes,'allocation':freeze['allocation']}
        if len(binding['source_commit'])!=40 or any(c not in '0123456789abcdef' for c in binding['source_commit']):errors.append('source_commit_shape')
        host_receipts={}
        for role in ('candidate','model'):
            directory=results/('review01-'+role+'-launch');receipt=json.loads((directory/'receipt.json').read_bytes());host_receipts[role]=receipt
            errors.extend(role+':'+e for e in process_errors(directory,receipt,freeze['commands'][role]))
            if receipt['binding']!=binding:errors.append(role+':source_binding')
        if datetime.fromisoformat(host_receipts['candidate']['finished_utc'])>datetime.fromisoformat(host_receipts['model']['started_utc']):errors.append('host_phase_order')
        model=json.loads((models/'model_result.json').read_bytes())
        if model['freeze_sha256']!=frozen or model['candidate_raw_sha256']!=sha(raw_path) or model['prompt_sha256']!=sha(source/'prompt.txt') or model['error'] or len(model['rows'])!=4:errors.append('model_identity_or_first_stop')
        pids=set();calls=set()
        for index,(row,case) in enumerate(zip(raw['rows'],fixture['cases'])):
            directory=data/f'row-{index:03d}';app=row['app'];ready=row['ready'];token=fixture['allocation']+f':row-{index:03d}'
            if row['case']!=case or row['token']!=token or row['app_pid']!=app['pid'] or app['token']!=token or ready['token']!=token or ready['pid']!=app['pid'] or type(app['pid']) is not int or app['pid']<=0 or app['pid'] in pids:errors.append('row_identity')
            pids.add(app['pid'])
            if json.loads((directory/'app_result.json').read_bytes())!=app or json.loads((directory/'app_stdout.bin').read_bytes())!=app or json.loads((directory/'ready.json').read_bytes())!=ready or row['app_exit']!=0 or row['app_stderr'] or (directory/'app_stderr.bin').read_bytes():errors.append('app_stream')
            target=case['emitted'] if case['recipient']=='target' else '';decoy=case['emitted'] if case['recipient']=='decoy' else ''
            if app['target']!=target or app['decoy']!=decoy or app['save_count']!=0 or row['post_review_input_count']!=0:errors.append('stimulus_effect')
            events=[e for e in app['events'] if e['kind']=='KeyPress'];requests=row['key_requests']
            if ''.join(e['char'] for e in events)!=case['emitted'] or any(e['widget']!=case['recipient'] for e in events) or ''.join(e['char'] for e in requests)!=case['emitted'] or len(events)!=len(requests):errors.append('keypress_identity')
            clock=[app['started_ns'],ready['ready_ns'],row['click']['started_ns'],row['click']['completed_ns']]
            for request in requests:clock.extend([request['started_ns'],request['completed_ns']])
            clock.extend([row['screen']['started_ns'],row['screen']['completed_ns'],app['ended_ns']])
            if any(type(t) is not int or t<=0 for t in clock) or clock!=sorted(clock) or any(not ready['ready_ns']<=e['ns']<=row['screen']['started_ns'] for e in events):errors.append('app_clock')
            g=ready[case['recipient']]
            if row['click']['x']!=g['x']+g['width']//2 or row['click']['y']!=g['y']+g['height']//2:errors.append('click_geometry')
            width,height=map(int,case['geometry'].split('+')[0].split('x'))
            if (ready['root']['width'],ready['root']['height'])!=(width,height):errors.append('geometry_dimensions')
            screen=row['screen']
            if screen['xwd_sha256']!=sha(directory/'screen.xwd') or screen['png_sha256']!=sha(directory/'screen.png') or screen['exit_code']!=0 or screen['argv']!=['xwd','-silent','-id',str(ready['root']['id'])] or screen['stderr_sha256']!=sha(directory/'xwd_stderr.bin') or (directory/'xwd_stderr.bin').read_bytes():errors.append('capture_binding')
            errors.extend(pixel_errors((directory/'screen.xwd').read_bytes(),(directory/'screen.png').read_bytes()))
            if index>=len(model['rows']):continue
            mr=model['rows'][index];md=models/f'row-{index:03d}';receipt=json.loads((md/'receipt.json').read_bytes())
            errors.extend(process_errors(md,receipt,freeze['model_commands'][index],sha(source/'prompt.txt')))
            if mr['process']!=receipt or mr['index']!=index or mr['image_sha256']!=screen['png_sha256'] or mr['error'] or mr['authority_granted'] is not False or mr['actions_emitted']!=0:errors.append('model_row_binding')
            events=[json.loads(line) for line in (md/'stdout.bin').read_bytes().decode('utf-8').splitlines() if line]
            parsed=model_value(events)
            if parsed!=mr['parsed'] or parsed['call_id'] in calls:errors.append('model_parsed_identity')
            calls.add(parsed['call_id'])
            if not datetime.fromisoformat(host_receipts['model']['started_utc'])<=datetime.fromisoformat(receipt['started_utc'])<=datetime.fromisoformat(receipt['finished_utc'])<=datetime.fromisoformat(host_receipts['model']['finished_utc']):errors.append('model_process_order')
            wanted=expected(case['wanted'],app['target'],app['decoy'])
            observations.append(dict(index=index,case=case['id'],expected=wanted,answer=parsed['answer'],exact=parsed['answer']==wanted,usage=parsed['usage'],wall_seconds=receipt['wall_seconds']))
        method='STOP_AUDIT' if errors else 'METHOD_PASS_FINITE_REVIEW_ONLY'
        hypothesis='UNQUALIFIED' if errors else ('H_PASS_FINITE_REVIEW_ONLY' if len(observations)==4 and all(r['exact'] for r in observations) else 'H_FAIL_FINITE_REVIEW_ONLY')
        return dict(status=method,hypothesis=hypothesis,errors=errors,observations=observations,scope='four controlled private GUI review stimuli; model is non-authoritative, no post-model action or recovery efficacy/causal speed claim')
    except (KeyError,TypeError,ValueError,OSError,IndexError,AttributeError) as exc:
        return dict(status='STOP_AUDIT',hypothesis='UNQUALIFIED',errors=errors+['malformed:'+type(exc).__name__],observations=observations)
if __name__=='__main__':
    result=inspect(sys.argv[1]);print(json.dumps(result,sort_keys=True));raise SystemExit(1 if result['errors'] else 0)
