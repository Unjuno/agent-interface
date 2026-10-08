"""Reviewer raw-only oracle; imports no runtime, producer, or author auditor."""
from copy import deepcopy
import hashlib
from itertools import product
import json
from pathlib import Path
import sys

OS=['linux','windows','macos',None,False,True,0,1.5,'other',[],{}]
STATES=['supported','unsupported','unknown','permission_required',None,False,0,1.5,'',[],{}]
FRAMES=[['screen_physical_px'],['screen_logical'],['window_client'],
        ['window_client','screen_logical','screen_physical_px'],[],None,'screen_physical_px',
        ['screen_physical_px','screen_physical_px'],['screen_physical_px',{}],['unknown'],
        [[]],False,0,[None],['screen_physical_px',1]]
FLOOR=['capture.frame','clock.monotonic','display.geometry','event.feedback',
       'input.keyboard','input.pointer','input.release_all','input.scroll','input.text','window.focus']
PROGRAM={'schema':'agent-interface/program-v1','program_id':'non-author-finite-review',
         'source':{'observation_seq':1,'binding_revision':1},
         'authority':{'lease_id':'no-device','expires_at_ns':100},
         'terminal':{'release_all_required':True},'ops':[{'op':'release_all'}]}
def cases():
    for os,state,frames in product(OS,STATES,FRAMES):
        yield {'schema':'agent-interface/backend-v1','backend_id':'finite-review',
               'platform':{'os':os,'backend':'no-device'},
               'capabilities':{'input.release_all':{'state':state}},
               'coordinate_frames':frames,'clock':{'unit':'ns','monotonic':True},'permissions':[]}
def reference(m,baseline):
    os=m['platform']['os']; state=m['capabilities']['input.release_all']['state']; frames=m['coordinate_frames']
    os_ok=type(os)is str and os in ('linux','windows','macos')
    state_ok=type(state)is str and state in ('supported','unsupported','unknown','permission_required')
    frame_ok=(type(frames)is list and bool(frames) and all(type(x)is str and x in
              ('screen_physical_px','screen_logical','window_client') for x in frames)
              and len(frames)==len(set(frames)))
    hashing_error=(type(os)in(list,dict) or (os_ok and type(state)in(list,dict))
                   or (os_ok and state_ok and type(frames)is list and bool(frames)
                       and any(type(x)in(list,dict) for x in frames)))
    if baseline and hashing_error:
        return {k:{'exception':'TypeError'} for k in ('validate','admit','readiness')}
    if not(os_ok and state_ok and frame_ok):
        return {'validate':{'exception':'ContractError'},
                'admit':{'accepted':False,'error':'INVALID_PROGRAM','required':[]},
                'readiness':{'exception':'ContractError'}}
    err=(None if state=='supported' else 'PERMISSION_DENIED' if state=='permission_required' else 'UNSUPPORTED_CAPABILITY')
    states={key:state if key=='input.release_all' else 'unknown' for key in FLOOR}
    return {'validate':{'valid':True},'admit':{'accepted':err is None,'error':err,'required':['input.release_all']},
            'readiness':{'ready':False,'blocking_capabilities':[k for k in FLOOR if states[k]!='supported'],'states':states}}
def json_same(a,b):
    if type(a)is not type(b):return False
    if type(a)is dict:return a.keys()==b.keys() and all(json_same(a[k],b[k]) for k in a)
    if type(a)is list:return len(a)==len(b) and all(json_same(x,y) for x,y in zip(a,b))
    return a==b
def verify(raw,stage,sha):
    errors=[]; expected=list(cases())
    if raw.get('schema')!='review6860-finite-json-v1' or raw.get('stage')!=stage:
        errors.append('schema_or_stage')
    if raw.get('source_sha256')!=sha:
        errors.append('source')
    if raw.get('native_backend_opened')is not False:
        errors.append('native_backend_declaration')
    if not json_same(raw.get('program'),PROGRAM):
        errors.append('program')
    if type(raw.get('row_count'))is not int or raw['row_count']!=len(expected):
        errors.append('denominator')
    rows=raw.get('rows')
    if type(rows)is not list or len(rows)!=len(expected):
        return errors+['rows']
    for i,(row,m) in enumerate(zip(rows,expected)):
        if type(row.get('id'))is not int or row['id']!=i or not json_same(row.get('manifest'),m):
            errors.append('identity:'+str(i))
        if row.get('unchanged')is not True:
            errors.append('mutation:'+str(i))
        for k,want in reference(m,stage=='baseline').items():
            got=row.get(k)
            if not json_same(got,want):
                errors.append(k+':'+str(i))
            elif 'accepted'in want and type(got['accepted'])is not bool:
                errors.append('accepted_type:'+str(i))
            elif 'valid'in want and type(got['valid'])is not bool:
                errors.append('valid_type:'+str(i))
            elif 'ready'in want and type(got['ready'])is not bool:
                errors.append('ready_type:'+str(i))
    return errors
def main(raw_path,sha,output):
    raw=json.loads(raw_path.read_bytes()); stage=raw['stage']; errors=verify(raw,stage,sha)
    controls={}
    for kind in ('omission','duplicate','accepted_invalid','integer_accepted','source','native','input_mutation','escaped_type_error','manifest_clock_integer','manifest_os_float_alias','program_terminal_integer'):
        changed=deepcopy(raw)
        if kind=='omission': changed['rows'].pop()
        elif kind=='duplicate': changed['rows'][-1]=deepcopy(changed['rows'][0])
        elif kind=='accepted_invalid': changed['rows'][4]['admit']={'accepted':True,'error':None,'required':[]}
        elif kind=='integer_accepted': changed['rows'][0]['admit']['accepted']=1
        elif kind=='source': changed['source_sha256']='0'*64
        elif kind=='native': changed['native_backend_opened']=True
        elif kind=='input_mutation': changed['rows'][0]['unchanged']=False
        elif kind=='manifest_clock_integer': changed['rows'][0]['manifest']['clock']['monotonic']=1
        elif kind=='manifest_os_float_alias': changed['rows'][990]['manifest']['platform']['os']=0.0
        elif kind=='program_terminal_integer': changed['program']['terminal']['release_all_required']=1
        else: changed['rows'][0]['validate']={'exception':'TypeError'}
        rejected=verify(changed,stage,sha)
        controls[kind]={'rejected':bool(rejected),'sample_errors':rejected[:3]}
        if not rejected: errors.append('undetected:'+kind)
    summary={'stage':stage,'rows':len(raw['rows']),'api_calls':3*len(raw['rows']),
             'errors':errors,'corruption_controls':controls,
             'type_error_rows':sum(row['validate']=={'exception':'TypeError'} for row in raw['rows']),
             'raw_sha256':hashlib.sha256(raw_path.read_bytes()).hexdigest(),
             'source_sha256':sha,'status':'PASS_FINITE_JSON_BOUNDARY' if not errors else 'FAIL'}
    with output.open('x',encoding='utf-8',newline='\n')as f:
        json.dump(summary,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps(summary))
    return bool(errors)
if __name__=='__main__':
    sys.exit(main(Path(sys.argv[1]),sys.argv[2],Path(sys.argv[3])))
