"""Private input-free finite probe; writes fresh reviewer evidence, not retained data."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.machinery
import importlib.util
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
PROGRAM={'schema':'agent-interface/program-v1','program_id':'non-author-finite-review',
         'source':{'observation_seq':1,'binding_revision':1},
         'authority':{'lease_id':'no-device','expires_at_ns':100},
         'terminal':{'release_all_required':True},'ops':[{'op':'release_all'}]}
def load(path):
    loader=importlib.machinery.SourceFileLoader('private_review_core',str(path))
    spec=importlib.util.spec_from_loader(loader.name,loader)
    c=importlib.util.module_from_spec(spec)
    sys.modules[loader.name]=c
    loader.exec_module(c)
    return c
def main(source,stage,output):
    started=datetime.now(timezone.utc).isoformat()
    c=load(source)
    rows=[]
    for i,(os,state,frames) in enumerate(product(OS,STATES,FRAMES)):
        m={'schema':'agent-interface/backend-v1','backend_id':'finite-review',
           'platform':{'os':deepcopy(os),'backend':'no-device'},
           'capabilities':{'input.release_all':{'state':deepcopy(state)}},
           'coordinate_frames':deepcopy(frames),'clock':{'unit':'ns','monotonic':True},'permissions':[]}
        before=json.dumps(m,sort_keys=True)
        row={'id':i,'manifest':deepcopy(m)}
        for label,call in [('validate',lambda:c.validate_backend_manifest(m)),
                           ('admit',lambda:c.admit_program(deepcopy(PROGRAM),m,now_ns=1,current_observation_seq=1,current_binding_revision=1)),
                           ('readiness',lambda:c.office_readiness(m))]:
            try:
                value=call()
                row[label]=({'valid':True} if label=='validate' else
                            {'accepted':value.accepted,'error':value.error,'required':list(value.required_capabilities)}
                            if label=='admit' else value)
            except Exception as e:
                row[label]={'exception':type(e).__name__}
        row['unchanged']=json.dumps(m,sort_keys=True)==before
        rows.append(row)
    raw={'schema':'review6860-finite-json-v1','stage':stage,'program':PROGRAM,
         'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
         'started_utc':started,'ended_utc':datetime.now(timezone.utc).isoformat(),
         'row_count':len(rows),'rows':rows,'native_backend_opened':False}
    with output.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(raw,f,sort_keys=True,allow_nan=False)
        f.write('\n')
    print(json.dumps({'stage':stage,'rows':len(rows),'sha256':hashlib.sha256(output.read_bytes()).hexdigest()}))
if __name__=='__main__':
    main(Path(sys.argv[1]),sys.argv[2],Path(sys.argv[3]))
