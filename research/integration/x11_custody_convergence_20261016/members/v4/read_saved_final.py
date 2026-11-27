"""Data-only qualification of retained source images and terminal actor records."""
import ast, copy, hashlib, json, pathlib, re
P=pathlib.Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def require(condition,message):
    if not condition:raise ValueError(message)
def rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf8').splitlines() if line.startswith('{')]
labels=['baseline-first','candidate-construction-first','candidate-normal','candidate-O','wrong-index','final-normal','final-O']
data={}
for label in labels:
    root=P/label
    receipt=json.loads((root/'RESULT.json').read_text(encoding='utf8'))
    require(not receipt['timeout'] and receipt['pins_unchanged'],'terminal '+label)
    for name,pin in receipt['streams'].items():
        raw=(root/name).read_bytes()
        require(len(raw)==pin['bytes'] and sha(raw)==pin['sha256'],'stream join '+label)
    for path,pin in receipt['pins'].items():
        file=pathlib.Path(path)
        if label=='candidate-construction-first' and file.is_relative_to(P/'sources/candidate'):
            file=P/'sources/candidate_indent_first'/file.relative_to(P/'sources/candidate')
        require(sha(file.read_bytes())==pin,'source join '+label+' '+str(file))
    data[label]={'receipt':receipt,'rows':rows(root/'stdout.txt'),'stderr':(root/'stderr.txt').read_text(encoding='utf8')}

backend_path='runtime/backends/x11_v1/backend.py'
test_path='runtime/backends/x11_v1/test_sidebutton_ledger.py'
manifest=json.loads((P/'SOURCE_MANIFEST_FINAL.json').read_text(encoding='utf8'))
for arm,images in manifest.items():
    for path,pin in images.items():
        raw=(P/'sources'/arm/path).read_bytes()
        require(len(raw)==pin['bytes'] and sha(raw)==pin['sha256'],'manifest join')
delta=[p for p in manifest['candidate'] if manifest['candidate'][p]!=manifest['baseline'][p]]
require(set(delta)=={backend_path,'.github/workflows/runtime-x11-v1.yml','runtime/integration_checks/native.py'},'baseline source delta')
require([p for p in manifest['wrong_index'] if manifest['wrong_index'][p]!=manifest['candidate'][p]]==[backend_path],'source negative delta')
right=(P/'sources/candidate'/backend_path).read_bytes()
wrong=(P/'sources/wrong_index'/backend_path).read_bytes()
require(right.replace(b'state[number-1]',b'state[number]')==wrong,'one-token source negative')

def expected_names(targets):
    result=[]
    for target in targets:
        file=P/'sources/candidate'/(target.replace('.','/')+'.py')
        tree=ast.parse(file.read_text(encoding='utf8'))
        for cls in tree.body:
            if isinstance(cls,ast.ClassDef):
                result += [target+'.'+cls.name+'.'+n.name for n in cls.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
    return sorted(result)

def inspect_green(d):
    terminal=d['rows'][-1]
    require(d['receipt']['exit']==0 and terminal['methods']==57,'green method count')
    require(not any(terminal[k] for k in ('failures','errors','skips','forbidden','native_display_calls')),'green terminal')
    names=expected_names(terminal['targets'])
    require(sorted(terminal['method_names'])==names and len(names)==57,'AST method identities')
    for name in names:
        module,cls,method=name.rsplit('.',2)
        require(method+' ('+module+'.'+cls+'.'+method+') ... ok' in d['stderr'],'stderr method '+name)
    selection=terminal['selection']
    require(len(selection['workflow'])==9 and len(selection['native_harness'])==22 and len(selection['native_protocol'])==33,'selector census')
    endpoints=[r for r in d['rows'] if 'case' in r or 'mixed_case' in r]
    require(len(endpoints)==176,'endpoint census')
    side=[r for r in endpoints if 'quarantine' in r]
    require(len(side)==35,'side census')
    index={(r['case'],r['stage']):r for r in side}
    require(len(index)==35,'unique side endpoints')
    for row in side:
        require(row['emissions']==sum('send' in e for e in row['events']),'side emission oracle')
    for name,number in [('x1',8),('x2',9)]:
        for stage in ('stubborn','failed_recover'):
            r=index[name,stage]
            require(r['buttons']==[number] and r['owned']==[name] and r['quarantine'] is True,'retained side custody')
        r=index[name,'stubborn']
        require(r['reply']['status']=='release_unverified' and r['emissions']==3,'stubborn outcome')
        refused=index[name,'refused']
        require(refused['reply']['error']=='INPUT_RECOVERY_REQUIRED' and refused['events']==r['events'] and refused['emissions']==3,'refusal emits')
        require(index[name,'failed_recover']['reply']['status']=='recovery_failed' and index[name,'failed_recover']['emissions']==4,'finite failed recovery')
        r=index[name,'recover']
        require(r['reply']['status']=='input_recovered' and r['reply']['replay_allowed'] is False and r['reply']['task_success'] is None and r['emissions']==5 and not (r['buttons'] or r['owned'] or r['quarantine']),'recovery without replay')
        r=index[name,'fresh']
        require(r['reply']['status']=='completed' and r['emissions']==8 and not(r['buttons'] or r['owned'] or r['quarantine']),'fresh dispatch')
    for fault in ('missing_extension','throw','empty','short','missing_class','disabled'):
        unknown=index[fault,'unknown'];refused=index[fault,'refused'];recovered=index[fault,'recover']
        require(unknown['reply']['status']=='execution_failed' and unknown['owned']==['x2'] and unknown['buttons']==[9] and unknown['quarantine'] is True,'unknown custody')
        require(refused['reply']['error']=='INPUT_RECOVERY_REQUIRED' and refused['emissions']==unknown['emissions'] and refused['events']==unknown['events'],'unknown refusal')
        require(recovered['reply']['status']=='input_recovered' and not(recovered['buttons'] or recovered['owned'] or recovered['quarantine']),'unknown recovery')
    require(index['second_master','down']['reply']['status']=='release_unverified' and index['second_master','down']['owned']==['x2'],'second-master conservative read')
    require(index['duplicate_master','unknown']['reply']['status']=='execution_failed' and index['duplicate_master','unknown']['owned']==['x1'],'duplicate inventory')
    decoder=[r for r in d['rows'] if 'decoder_button' in r]
    require(len(decoder)==2 and all(r['correct_index']==r['decoder_button']-1 and r['correct_value'] and not r['wrong_value'] for r in decoder),'decoder bits')
    wire=[r for r in d['rows'] if 'wire_button' in r]
    require(len(wire)==2 and all(type(r['enabled']) is int and r['enabled']==1 and r['classes']==1 for r in wire),'wire shapes')
    api=[r for r in d['rows'] if 'api_wrapper' in r]
    require(api==[{'api_wrapper':'query_version','actual_positional_arguments':0,'major':2,'minor':0}],'API shape')
    return {'methods':57,'endpoints':176,'side_endpoints':35,'decoder':2,'wire':2,'api':1}

checks={label:inspect_green(data[label]) for label in ('candidate-normal','candidate-O','final-normal','final-O')}
require(data['candidate-normal']['rows'][:-1]==data['candidate-O']['rows'][:-1],'normal/O semantic equality')
require(data['final-normal']['rows'][:-1]==data['final-O']['rows'][:-1], 'final normal/O equality')
require(data['final-normal']['rows'][:-1]==data['candidate-normal']['rows'][:-1], 'EOF normalization endpoint equality')
first=data['baseline-first']
require(first['receipt']['exit']==1 and first['rows'][-1]['methods']==9 and first['rows'][-1]['failures']==10 and first['rows'][-1]['errors']==0,'baseline terminal')
for r in first['rows']:
    if r.get('stage') in ('unknown','down','stubborn') and r.get('case')!='left':
        require(r['reply']['status']=='completed' and not(r['owned'] or r['quarantine']),'baseline false clearing')
construction=data['candidate-construction-first']
require(construction['receipt']['exit']==1 and not construction['rows'] and 'IndentationError' in construction['stderr'],'first construction failure retained')
negative=data['wrong-index']
require(negative['receipt']['exit']==1 and negative['rows'][-1]['methods']==9 and negative['rows'][-1]['failures']==3 and negative['rows'][-1]['errors']==0,'source negative terminal')
old=rows(P.parent/'x11-unified-custody-01a0ff2c/candidate-workflow-normal-LF/stdout.txt')
new=data['candidate-normal']['rows']
require([r for r in old if 'case' in r or 'mixed_case' in r]==[r for r in new if ('case' in r or 'mixed_case' in r) and 'quarantine' not in r],'all 141 prior endpoint rows unchanged')
require(sorted(old[-1]['actual_method_names'])==sorted(n for n in new[-1]['method_names'] if '.test_sidebutton_ledger.' not in n),'48 prior method identities unchanged')
controls={}
for name in ('omit_endpoint','clear_owned','allow_replay'):
    copydata=copy.deepcopy(data['candidate-normal'])
    if name=='omit_endpoint':
        copydata['rows'].pop(next(i for i,r in enumerate(copydata['rows']) if 'quarantine' in r))
    elif name=='clear_owned':
        next(r for r in copydata['rows'] if r.get('case')=='x1' and r.get('stage')=='stubborn')['owned']=[]
    else:
        next(r for r in copydata['rows'] if r.get('case')=='x1' and r.get('stage')=='recover')['reply']['replay_allowed']=True
    (P/(name+'.json')).write_bytes((json.dumps(copydata,sort_keys=True)+'\n').encode())
    try:inspect_green(copydata)
    except ValueError as e:controls[name]=str(e)
    else:raise ValueError('accepted tampered control '+name)
result={'checks':checks,'source_negative_failures':3,'baseline_failures':10,'first_construction_failure':'retained indentation error, no tests executed','prior_141_endpoints_and_48_methods_unchanged':True,'normal_O_semantic_rows_equal':True,'controls_rejected':controls,'source_delta_existing':delta,'new_test_module':test_path,'actor_replays':0,'scope':'actual full imported backend and session, real Python-Xlib wrapper/decoder, inert transport; native ClientPointer/topology/physical release unqualified; adoption/application HOLD maintained'}
(P/'READER_RESULT_FINAL.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
print(json.dumps(result))
