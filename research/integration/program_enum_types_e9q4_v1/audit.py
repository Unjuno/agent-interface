"""Raw-only finite oracle. Imports no runtime, corpus builder, or runner."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
FRAMES = ['screen_physical_px', 'screen_logical', 'window_client']
BUTTONS = ['left','middle','right','x1','x2']
CAPS = {'key_chord':['input.keyboard'], 'text':['input.text'],
        'wait_update':['event.feedback','clock.monotonic'],
        'pointer_move':['input.pointer','display.geometry'],
        'pointer_button':['input.pointer','display.geometry'],
        'observe':['capture.frame','display.geometry'], 'key_state':['input.keyboard'],
        'release_all':['input.release_all']}
MESSAGES = {'pointer_move':'invalid pointer frame','observe':'invalid observe frame',
            'pointer_button':'invalid pointer button'}
CLI_IDS = [0,44,88,11,55,99,138,139]


def encode(x): return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
def sha(b): return hashlib.sha256(b).hexdigest()
def returned(x): return {'kind':'returned','value':x}
def raised(t,d,i): return {'kind':'raised','type':t,'detail':d,'operation_index':i}


def expectations(case, arm):
    p = case['program']; ops=p['ops']; expanded=[]; source=[]
    mode = ('bounded_text_gap' if any('gap_ms' in x for x in ops) else
            'bounded_key_repeat' if any('repeat' in x for x in ops) else None)
    for i, op in enumerate(ops):
        q={k:v for k,v in op.items() if k not in ('repeat','gap_ms')}
        if 'gap_ms' in op:
            for j,ch in enumerate(op['text']):
                if j: expanded.append({'op':'wait_update','timeout_ms':op['gap_ms']});source.append(i)
                expanded.append(dict(q,text=ch));source.append(i)
        else:
            for _ in range(op.get('repeat',1)): expanded.append(q.copy());source.append(i)
    result=None; index=None; message=None; kind=None
    if len(expanded)>128:
        message='ops length out of range';kind='ContractError'
    elif case['control']=='earlier_error':
        message='key F8 released while not held';kind='ContractError';index=0
    else:
        for i,op in enumerate(expanded):
            name=op['op']
            if name not in MESSAGES: continue
            v=op.get('button' if name=='pointer_button' else 'frame')
            allowed=BUTTONS if name=='pointer_button' else FRAMES
            if type(v) is str and v in allowed: continue
            if arm=='baseline' and type(v) in (list,dict):
                kind='TypeError';message="unhashable type: '"+type(v).__name__+"'"
            else:
                kind='ContractError';message=MESSAGES[name];index=i
            break
    neutral={'schema':'agent-interface/static-program-validation-v1',
             'side_effect_authority':False,'runtime_admission':'not_evaluated',
             'backend_checked':False,'task_success':None}
    if kind:
        validation=raised(kind,message,index)
        admission=(deepcopy(validation) if kind=='TypeError' else
                   returned({'accepted':False,'error':'INVALID_PROGRAM','required_capabilities':[]}))
        report=dict(neutral,status='invalid',static_valid=False,error='INVALID_PROGRAM',
                    detail_source='program_validation',compilation=mode,
                    detail=('program contains an invalid field type' if kind=='TypeError' else
                            'key released while not held' if case['control']=='earlier_error' else message))
        if index is not None:
            report.update(expanded_operation_index=index,source_operation_index=source[index])
    else:
        required=sorted({cap for op in expanded for cap in CAPS[op['op']]})
        validation=returned(True)
        err={'expired':'LEASE_EXPIRED','stale_observation':'STALE_OBSERVATION',
             'stale_binding':'STALE_BINDING','unsupported':'UNSUPPORTED_CAPABILITY',
             'permission':'PERMISSION_DENIED','coordinate':'COORDINATE_UNSUPPORTED'}.get(case['control'])
        admission=returned({'accepted':err is None,'error':err,'required_capabilities':required})
        report=dict(neutral,status='valid',static_valid=True,source_operation_count=len(ops),
                    expanded_operation_count=len(expanded),required_capabilities=required,compilation=mode)
    e=deepcopy(p);e['ops']=expanded
    return validation,admission,returned(report),e


def audit(raw, freeze):
    errors=[];checks=0
    def check(ok, label):
        nonlocal checks
        checks+=1
        if not ok:errors.append(label)
    try:
        check(raw['schema']=='enum-types-measurement-e9q4-v1','schema')
        check(raw.get('complete') is True,'terminal')
        construction=raw['mode']=='construction'
        ids=[0,4,11,44,48,55,88,92,99] if construction else list(range(140))
        cases=raw['cases']
        check([x['id'] for x in cases]==ids,'case denominator/order')
        if not construction:
            check(sha((encode(cases)+'\n').encode())==freeze['corpus_sha256'],'corpus identity')
            check(raw['sources']==freeze['runtime_sha256'],'runtime identity')
            check(raw['freeze_sha256']==sha((HERE/'FREEZE.json').read_bytes()),'freeze identity')
        check(raw['display_removed'] is True,'display status')
        check(set(raw['workers'])=={'baseline','candidate'},'arm denominator')
        count={'baseline_type_errors':0,'candidate_type_errors':0,'candidate_valid':0,'candidate_invalid':0}
        outcomes={}
        pids=[]
        for arm in ('baseline','candidate'):
            w=raw['workers'][arm];pids.append(w['pid'])
            check(type(w['exit']) is int and w['exit']==0,'worker exit '+arm)
            check(w['stderr']=='','worker stderr '+arm)
            check(sha(w['stdout'].encode())==w['stdout_sha256'],'worker stdout identity '+arm)
            check(sha(w['stderr'].encode())==w['stderr_sha256'],'worker stderr identity '+arm)
            check(type(w['start_ns']) is int and type(w['end_ns']) is int and w['end_ns']>=w['start_ns'],'worker time '+arm)
            check(w['argv'][1:3]==['-S','-B'] and w['argv'][3].endswith('/worker.py'),'worker command '+arm)
            document=json.loads(w['stdout']);rows=document['rows']
            check([r['id'] for r in rows]==ids,'row denominator '+arm)
            check(document['imported_runtime_modules']==['runtime','runtime.core_v1','runtime.core_v1.contract',
                   'runtime.core_v1.platform_probe','runtime.core_v1.sequence'],'import closure '+arm)
            outcomes[arm]={r['id']:r for r in rows}
            for case,row in zip(cases,rows):
                label=arm+':'+str(case['id'])
                v,a,s,e=expectations(case,arm)
                for key,val in [('validation',v),('admission',a),('inspection',s),('expanded_program',e)]:
                    check(encode(row[key])==encode(val),label+':'+key)
                check(row['input_sha256']==sha(encode(case['program']).encode()),label+':input')
                for field in ('input_unchanged','expanded_unchanged','manifest_unchanged'):
                    check(row[field] is True,label+':'+field)
                args={'now_ns':1,'current_observation_seq':1,'current_binding_revision':1}
                if case['control']=='expired':args['now_ns']=101
                if case['control']=='stale_observation':args['current_observation_seq']=2
                if case['control']=='stale_binding':args['current_binding_revision']=2
                check(row['admission_arguments']==args,label+':admission arguments')
                m=row['manifest']
                check(m['backend_id']=='enum-check' and m['platform']=={'os':'linux','backend':'no-device'},label+':manifest identity')
                check(m['coordinate_frames']==(['screen_physical_px'] if case['control']=='coordinate' else sorted(FRAMES)),label+':frames')
                states={k:r['state'] for k,r in m['capabilities'].items()}
                check(len(states)==14 and all(vv==('permission_required' if case['control']=='permission' and k=='input.pointer' else
                      'unsupported' if case['control']=='unsupported' and k=='input.pointer' else 'supported') for k,vv in states.items()),label+':capabilities')
                if row['validation'].get('type')=='TypeError':count[arm+'_type_errors']+=1
                if arm=='candidate':count['candidate_'+('valid' if s['value']['static_valid'] else 'invalid')]+=1
        selected=[0,11] if construction else sorted(CLI_IDS)
        check([(x['arm'],x['id']) for x in raw['cli']]==[(arm,i) for arm in ('baseline','candidate') for i in selected],'cli denominator')
        for row in raw['cli']:
            pids.append(row['pid']);label='cli:'+row['arm']+':'+str(row['id'])
            case=next(x for x in cases if x['id']==row['id'])
            report=expectations(case,row['arm'])[2]['value'].copy()
            check(row['input_bytes']==encode(case['program'])+'\n',label+':input bytes')
            report['input_sha256']=sha(row['input_bytes'].encode())
            check(json.loads(row['stdout'])==report,label+':response')
            check(type(row['exit']) is int and row['exit']==(0 if report['static_valid'] else 1),label+':exit')
            check(row['stderr']=='' and row['input_unchanged'] is True,label+':stderr/nonmutation')
            check(sha(row['stdout'].encode())==row['stdout_sha256'],label+':stdout identity')
            check(row['argv'][1:3]==['-S','-B'] and row['argv'][3].endswith('/validate_program.py') and row['argv'][4]=='--program',label+':command')
        check(len(set(pids))==len(pids) and all(type(pid) is int and pid>0 for pid in pids),'fresh process identities')
        for case in cases:
            a=outcomes['baseline'][case['id']];b=outcomes['candidate'][case['id']]
            if a['validation'].get('type')!='TypeError':check(encode(a)==encode(b),'unchanged behavior '+str(case['id']))
        if not construction:
            check(count=={'baseline_type_errors':36,'candidate_type_errors':0,'candidate_valid':39,'candidate_invalid':101},'fixed totals')
    except (KeyError,TypeError,ValueError,StopIteration) as e:
        errors.append('EVIDENCE_SHAPE:'+type(e).__name__)
        count={}
    return {'status':('PASS_CONSTRUCTION_ONLY' if raw.get('mode')=='construction' else 'PASS_PROGRAM_ENUM_TYPE_COMPATIBILITY') if not errors else 'HOLD_OR_FAIL_EVIDENCE',
            'checks':checks,'errors':errors,'counts':count}


def controls(raw,freeze):
    results=[]
    def change_worker(doc, fn):
        w=doc['workers']['candidate'];body=json.loads(w['stdout']);fn(body['rows']);w['stdout']=encode(body)+'\n';w['stdout_sha256']=sha(w['stdout'].encode())
    changes=[('missing_case',lambda d:d['cases'].pop()),
             ('duplicate_row',lambda d:change_worker(d,lambda r:r.append(deepcopy(r[0])))),
             ('wrong_source_index',lambda d:change_worker(d,lambda r:r[0]['inspection']['value'].__setitem__('source_operation_index',9))),
             ('boolean_index',lambda d:change_worker(d,lambda r:r[0]['validation'].__setitem__('operation_index',False))),
             ('false_admission',lambda d:change_worker(d,lambda r:r[0]['admission']['value'].__setitem__('accepted',True))),
             ('wrong_detail',lambda d:change_worker(d,lambda r:r[0]['inspection']['value'].__setitem__('detail','wrong'))),
             ('claimed_authority',lambda d:change_worker(d,lambda r:r[0]['inspection']['value'].__setitem__('side_effect_authority',True))),
             ('source_identity',lambda d:d['sources']['candidate'].__setitem__('runtime/core_v1/contract.py','0'*64)),
             ('lost_exit',lambda d:d['workers']['candidate'].__setitem__('exit',None)),
             ('cli_false_exit',lambda d:d['cli'][0].__setitem__('exit',0))]
    for name,fn in changes:
        d=deepcopy(raw);before=sha(encode(d).encode());fn(d);after=sha(encode(d).encode())
        report=audit(d,freeze);results.append({'name':name,'effective':before!=after,'rejected':bool(report['errors']),
                                              'mutated_sha256':after,'errors':report['errors']})
    return results


if __name__=='__main__':
    raw=json.loads(Path(sys.argv[1]).read_text());freeze=json.loads((HERE/'FREEZE.json').read_text()) if (HERE/'FREEZE.json').exists() else {}
    report=audit(raw,freeze)
    if '--controls' in sys.argv:
        report['controls']=controls(raw,freeze)
        if not all(x['effective'] and x['rejected'] for x in report['controls']):
            report['errors'].append('INEFFECTIVE_CONTROL');report['status']='HOLD_OR_FAIL_EVIDENCE'
    print(json.dumps(report,indent=2,sort_keys=True))
    raise SystemExit(0 if not report['errors'] else 1)
