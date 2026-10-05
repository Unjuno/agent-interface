"""Independent JSON/file reader: no runtime, peer, owner or collector imports/execution."""
import base64, copy, hashlib, json, pathlib, sys

ROOT=pathlib.Path(__file__).resolve().parent
def require(condition,message):
    if not condition:raise ValueError(message)
def integer(value):return type(value) is int
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(data):return hashlib.sha256(data).hexdigest()
def rows(path):return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines()]
def audit(output,raw):
    deck=read(ROOT/'DECK.json')
    require(len(raw)==8 and [r['case'] for r in raw]==deck,'exact ordered eight-row roster')
    gaps=[]
    for item in raw:
        case=item['case'];directory=output/case['id']
        baseline_error=case['arm']=='baseline' and case['boundary']=='input-error'
        peer_exit=17 if case['mode']=='exit17' and not baseline_error else 0
        expected_primary=1 if baseline_error else 2 if case['boundary']=='input-error' else 0
        require(item['collector_error'] is None,'collector failure')
        require(integer(item['primary_exit']) and item['primary_exit']==expected_primary,'primary actual typed exit')
        require(integer(item['peer_exit']) and item['peer_exit']==peer_exit,'peer actual typed exit')
        phase=item['phases']
        require([p['kind'] for p in phase]==['launch','peer_handle_open','accepted_before_boundary','boundary_before_permit','permit_written','both_processes_terminal'],'collector phase order')
        boundary=phase[3]
        require(type(boundary['observed']) is bool and boundary['observed']==(not baseline_error),'input boundary evidence')
        require(boundary['response_exists'] is False and boundary['effect_exists'] is False,'response/effect barrier')
        require(integer(boundary['wait']) and boundary['wait']==(0 if baseline_error else 258) and integer(boundary['exit_code']) and boundary['exit_code']==(0 if baseline_error else 259),'measured peer terminal/alive at fault barrier')
        require((integer(boundary['primary_exit']) and boundary['primary_exit']==1) if baseline_error else boundary['primary_exit'] is None,'owner settled before response permit')
        terminal=phase[-1]
        require(integer(terminal['wait']) and terminal['wait']==0 and integer(terminal['exit_code']) and terminal['exit_code']==peer_exit,'peer retained handle terminal')
        require(integer(item['primary_pid']) and integer(item['peer_pid']) and item['primary_pid']!=item['peer_pid'],'actual distinct owned processes')
        require(integer(phase[1]['pid']) and phase[1]['pid']==item['peer_pid'] and phase[1]['parent_pid']==item['primary_pid'],'child ownership chain')
        require(phase[2]['primary_exit'] is None and phase[2]['wait']==258,'accepted while both processes alive')
        require(type(item['elapsed_seconds']) in (int,float) and item['elapsed_seconds']<11,'collector case bound')

        # Verify persisted evidence independently of collector's reported statuses.
        manifest=read(directory/'FILES.json')
        actual={str(p.relative_to(directory)).replace('\\','/') for p in directory.rglob('*') if p.is_file() and p.name!='FILES.json'}
        require(actual==set(manifest),'complete case file roster')
        for path,entry in manifest.items():
            data=(directory/path).read_bytes()
            require(integer(entry['bytes']) and entry['bytes']==len(data) and entry['sha256']==sha(data),'case bytes '+path)
        request=read(directory/'accepted.json')
        expected_request=dict(id=1,tool='interface_guarded_input',arguments=dict(alias='synthetic-control',offset=[0,0],interaction='click',tail=[],detail='brief',observation_refs=True))
        require(request==expected_request and integer(request['id']),'exact accepted relay request')
        require(read(directory/'host/request-1.json')==request,'persisted original relay request')
        require(len(list((directory/'host').glob('request-*.json')))==1 and len(list((directory/'exchange').glob('request-*.json')))==1,'one operation, no replay')
        command=read(directory/'exchange/request-1.json')
        require(command==dict(id=1,method='input',args=['synthetic-control',[0,0],'click',[]]) and integer(command['id']),'exact consumed primary command')
        trace=rows(directory/'peer-events.jsonl')
        kinds=[r['kind'] for r in trace]
        if baseline_error:
            require(kinds==['started','accepted'] and not (directory/'synthetic-effect.json').exists() and not (directory/'response-intended.json').exists(),'original baseline terminal before permit/effect')
        else:
            effect=read(directory/'synthetic-effect.json')
            require(integer(effect['count']) and effect['count']==1 and effect['synthetic'] is True and effect['request_id']==1,'one explicitly synthetic effect')
            require(kinds[:4]==['started','accepted','permit_observed','synthetic_effect'] and len([k for k in kinds if k=='accepted'])==1,'peer acceptance/permit/effect order')
        require('unexpected_second_request' not in kinds and 'self_deadline' not in kinds,'no resend or self-deadline')
        stdout=rows(directory/'stdout.txt')
        statuses=[r['status'] for r in stdout]
        expected=['ready'] if baseline_error else ['ready','returned','terminal'] if case['boundary']=='eof' else ['ready','returned'] if case['mode']=='success' else ['ready','command_error']
        require(statuses==expected,'exact owner response rows')
        events=rows(directory/'host/host-events.jsonl')
        require([e['sequence'] for e in events]==list(range(1,len(events)+1)),'host event sequence')
        closed=[e for e in events if e['kind']=='transport_closed']
        if baseline_error:
            require(not closed and not (directory/'owner-result.json').exists() and not (directory/'host/exit.json').exists(),'baseline no owner close result')
            require("Unhandled 'error' event" in (directory/'stderr.txt').read_text(encoding='utf-8'),'baseline unhandled Interface failure')
            require(not (directory/'host/reply-1.json').exists() and not (directory/'exchange/presentation-1.json').exists(),'baseline response unobserved')
        else:
            owner=read(directory/'owner-result.json')
            require(integer(owner['input_error_listeners']) and owner['input_error_listeners']==0 and integer(owner['output_error_listeners']) and owner['output_error_listeners']==0,'owned listener release')
            require(owner['status']==('resolved' if case['boundary']=='eof' else 'rejected'),'owner settlement')
            if case['boundary']=='input-error':require(owner['same_error'] is True and owner['error']=='Error: owned-fixture-input-fault','same first input fault')
            require(len(closed)==1 and integer(closed[0]['code']) and closed[0]['code']==peer_exit and closed[0]['signal'] is None and events[-1]['kind']=='transport_closed','original transport actual close journal')
            if case['mode']=='wrong-id':
                require(not (directory/'host/exit.json').exists(),'predeclared rejected-journal exit receipt gap')
                saved=read(directory/'host/reply-1.json')
                require(saved==read(directory/'response-intended.json') and integer(saved['id']) and saved['id']==2,'wrong identity raw retained')
                require('identity/status mismatch' in stdout[1]['error'],'identity failure correlation')
                gaps.append(case['id'])
            else:
                require(read(directory/'host/exit.json')==dict(code=peer_exit,signal=None),'original relay actual exit receipt')
            if case['mode']=='success':
                reply=read(directory/'host/reply-1.json')
                require(reply==read(directory/'response-intended.json'),'exact original wire reply')
                original=read(directory/'exchange/original-reply-1.json')
                require(original==dict(reply,attempt=1),'exchange original reply identity')
                presentation=read(directory/'exchange/presentation-1.json')
                require(stdout[1]['result']==presentation and presentation['next_id']==2 and presentation['caller_state']['stopped'] is None,'completed fixture preserved without caller STOP')
                image=(directory/'exchange/image-1-1.png').read_bytes()
                require(image==base64.b64decode(reply['result']['content'][1]['data']) and presentation['images'][0]['sha256']==sha(image) and presentation['images'][0]['bytes']==len(image),'original image bytes/hash')
                reply_event=next(e for e in events if e['kind']=='reply_available')
                require(reply_event['reply_sha256']==sha((directory/'host/reply-1.json').read_bytes()),'original reply evidence hash')
                require(events[-2]['kind']=='presentation_callbacks_completed','presentation before transport close')
            else:
                require(stdout[1]['command_id']==1 and stdout[1]['command_method']=='input' and stdout[1]['replay_allowed'] is False and stdout[1]['state']['next_id']==2,'consumed command uncertainty, never replay')
                require(not (directory/'exchange/presentation-1.json').exists(),'no successful presentation on uncertainty')
        # Custody linkage is checked after independent behavioral assertions.
        require(read(directory/'receipt.json')==item,'raw/actual process receipt linkage')
    complete=read(output/'completion.json')
    require(integer(complete['rows']) and complete['rows']==8 and complete['elapsed_seconds']<100,'complete bounded deck')
    require(sum(p.stat().st_size for p in output.rglob('*') if p.is_file())<1048576,'output byte cap')
    return dict(rows=8,primary_exits=[r['primary_exit'] for r in raw],peer_exits=[r['peer_exit'] for r in raw],primary_question='FAIL_PREDECLARED_BASELINE_SURVIVAL',
      candidate_post_acceptance_cleanup='PASS_SCOPED_SAME_RETAINED_RAW',baseline_peer_termination_cause='UNKNOWN',synthetic_effect_counts=[0,1,0,1,0,1,1,1],exit_journal_gap_cases=gaps,
      scope='actual accepted host/child transport with injected input fault and synthetic downstream task/release; no physical or model evidence')

def main():
    output=ROOT/sys.argv[1]
    freeze=read(ROOT/'FREEZE.json')
    for path,expected in freeze['files'].items():require(sha((ROOT/path).read_bytes())==expected,'frozen file '+path)
    reaudit=read(ROOT/'REAUDIT_FREEZE.json')
    require(sha((ROOT/'audit_v2.py').read_bytes())==reaudit['auditor_sha256'],'new raw-only auditor source')
    require(sha((output/'raw.jsonl').read_bytes())==reaudit['raw_sha256'],'unchanged original raw')
    raw=rows(output/'raw.jsonl')
    result=audit(output,raw)
    mutations=[]
    variants=[]
    variants.append(('missing-row',raw[:-1]))
    variants.append(('duplicate-row',raw+[raw[0]]))
    v=copy.deepcopy(raw);v[0],v[1]=v[1],v[0];variants.append(('reordered',v))
    v=copy.deepcopy(raw);v[0]['primary_exit']=True;variants.append(('bool-exit',v))
    v=copy.deepcopy(raw);v[3]['peer_exit']=0;variants.append(('wrong-peer-exit',v))
    v=copy.deepcopy(raw);v[1]['phases'][3]['effect_exists']=True;variants.append(('effect-before-permit',v))
    v=copy.deepcopy(raw);v[1]['phases'][3]['primary_exit']=2;variants.append(('owner-before-promise',v))
    v=copy.deepcopy(raw);v[1]['phases'][-1]['wait']=258;variants.append(('peer-not-terminal',v))
    controls=output.parent/'audit-controls-v2';controls.mkdir()
    for name,data in variants:
        with (controls/(name+'.jsonl')).open('x',encoding='utf-8',newline='\n') as f:
            for item in data:f.write(json.dumps(item,separators=(',',':'))+'\n')
        try:audit(output,data)
        except (ValueError,KeyError,TypeError) as error:mutations.append(dict(name=name,refused=True,error=str(error)))
        else:raise ValueError('audit control accepted '+name)
    result['controls']=mutations
    result['raw_sha256']=sha((output/'raw.jsonl').read_bytes())
    result['auditor_imports']='Python stdlib only; no producer/runtime imports'
    with (output.parent/'AUDIT_V2.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))
if __name__=='__main__':main()
