import ast, hashlib, itertools, json, time
from pathlib import Path
HERE=Path(__file__).resolve().parent
INPUTS=HERE/'inputs'
RESULTS=HERE/'results'
EXPECTED={'current_main_commit':'f185a9059d485a4f8d5a65e9e7f6782897f67eae','candidate_commit':'6195600931fa6de4ecf1a5012cb83b549addb5af','current_main_blob':'50c63fa83969ed518a91e39c08d1ee52064eb636','candidate_blob':'576d481a3503e8be4d8ceded8a6371b3fe8850fc'}
OMIT=object()
def parser_from(path):
    tree=ast.parse(path.read_text(encoding='utf-8-sig'))
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ControllerFailureCleanup')
    method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__exit__')
    start=next(i for i,n in enumerate(method.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='events' for t in n.targets))
    end=next(i for i,n in enumerate(method.body[start:],start) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Subscript) and isinstance(t.value,ast.Name) and t.value.id=='receipt' and isinstance(t.slice,ast.Constant) and t.slice.value=='input_release_verified_empty' for t in n.targets))
    statements=method.body[start:end+1]
    unparsed=ast.unparse(ast.Module(body=statements,type_ignores=[]))
    amb=['accepted_duplicate_ids','terminal_duplicate_ids']
    ret=[ast.Name(id='receipt',ctx=ast.Load())]+[ast.Name(id=x,ctx=ast.Load()) if x in unparsed else ast.Constant(value=None) for x in amb]
    fn=ast.FunctionDef(name='derive',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='self'),ast.arg(arg='receipt')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=statements+[ast.Return(value=ast.Tuple(elts=ret,ctx=ast.Load()))],decorator_list=[])
    ns={}; exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(path),'exec'),ns)
    return ns['derive']
class Context:
    stdout_reader_retired=True
    stdout_reader_errors=[]
    def __init__(self,events): self.events=events
def accepted(identifier,token):
    row={'event':'accepted','id':identifier}
    if token is not OMIT: row['intent_token']=token
    return row
def terminal(identifier,kind):
    row={'event':'terminal','id':identifier}
    if kind=='no_release': return row
    if kind=='malformed_release': row['release']=['bad']; return row
    verified=kind not in ('unverified_empty','occupied_key','occupied_button')
    rel={'verified':verified,'keys_down':[1] if kind=='occupied_key' else [],'buttons_down':[1] if kind=='occupied_button' else []}
    if kind in ('token_a','token_b'): rel['intent_token']='lease-a' if kind=='token_a' else 'lease-b'
    row['release']=rel
    return row
TOKENS=(OMIT,'lease-a','lease-b')
TERM_KINDS=('no_release','malformed_release','neutral','token_a','token_b','unverified_empty','occupied_key','occupied_button')
ATOMS=[accepted(i,t) for i in ('cmd-a','cmd-b') for t in TOKENS]+[terminal(i,k) for i in ('cmd-a','cmd-b') for k in TERM_KINDS]
def oracle(events):
    a=[r for r in events if type(r) is dict and r.get('event')=='accepted' and type(r.get('id')) is str]
    t=[r for r in events if type(r) is dict and r.get('event')=='terminal' and type(r.get('id')) is str]
    aid=[r['id'] for r in a]; tid=[r['id'] for r in t]
    ambiguous=(len(aid)!=len(set(aid)) or len(tid)!=len(set(tid)))
    complete=(not ambiguous and set(aid).issubset(set(tid)))
    empty=complete
    if empty:
        accepted_by={r['id']:r for r in a}; terminal_by={r['id']:r for r in t}
        for ident in set(aid):
            rel=terminal_by[ident].get('release')
            if type(rel) is not dict or rel.get('verified') is not True or rel.get('keys_down')!=[] or rel.get('buttons_down')!=[]:
                empty=False; break
            if 'intent_token' in rel:
                token=accepted_by[ident].get('intent_token')
                if type(token) is not str or not token or rel.get('intent_token')!=token:
                    empty=False; break
    return {'input_terminals_complete':complete,'input_releases_verified_empty':empty,'ambiguous':ambiguous}
def main():
    current=parser_from(INPUTS/'current_main.py'); candidate=parser_from(INPUTS/'pr8687_candidate.py')
    result={'status':'PASS_SCOPED','source':EXPECTED,'atom_count':len(ATOMS),'sequence_count':0,'candidate_mismatches':0,'current_main_false_positive':0,'current_main_false_negative':0,'candidate_order_sensitive_profiles':0,'main_order_sensitive_profiles':0,'candidate_duplicate_certifications':0,'first_current_false_positive':None,'first_current_order_sensitive_profile':None}
    started=time.perf_counter(); profiles={'main':{},'candidate':{}}
    for n in range(5):
        for indexes in itertools.product(range(len(ATOMS)),repeat=n):
            events=[ATOMS[i] for i in indexes]; expected=oracle(events)
            base={'stdout_reader_retired':True,'stdout_reader_errors':[],'input_terminals_complete':False,'input_releases_verified_empty':False}
            m,_a,_t=current(Context(events),dict(base)); c,_ca,_ct=candidate(Context(events),dict(base))
            ms=(m['input_terminals_complete'],m['input_releases_verified_empty']); cs=(c['input_terminals_complete'],c['input_releases_verified_empty']); es=(expected['input_terminals_complete'],expected['input_releases_verified_empty'])
            result['sequence_count']+=1
            if cs!=es: result['candidate_mismatches']+=1
            if ms[1] and not es[1]:
                result['current_main_false_positive']+=1
                if result['first_current_false_positive'] is None: result['first_current_false_positive']={'events':events,'main':list(ms),'candidate':list(cs),'oracle':list(es)}
            if es[1] and not ms[1]: result['current_main_false_negative']+=1
            if c.get('event_identity_ambiguous') is True and c['input_releases_verified_empty'] is True: result['candidate_duplicate_certifications']+=1
            key=tuple(sorted(indexes))
            profiles['main'].setdefault(key,set()).add(ms); profiles['candidate'].setdefault(key,set()).add(cs)
    result['main_order_sensitive_profiles']=sum(len(v)>1 for v in profiles['main'].values())
    result['candidate_order_sensitive_profiles']=sum(len(v)>1 for v in profiles['candidate'].values())
    for key,vals in profiles['main'].items():
        if len(vals)>1:
            result['first_current_order_sensitive_profile']={'atom_indexes':key,'events':[ATOMS[i] for i in key],'outputs':[list(x) for x in sorted(vals)]}; break
    result['elapsed_seconds']=round(time.perf_counter()-started,3)
    if (result['sequence_count']!=sum(len(ATOMS)**n for n in range(5)) or result['candidate_mismatches'] or result['candidate_order_sensitive_profiles'] or result['candidate_duplicate_certifications'] or not result['current_main_false_positive'] or not result['main_order_sensitive_profiles']): result['status']='FAIL_SCOPED'
    (RESULTS/'candidate.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(result,sort_keys=True))
    if result['status']!='PASS_SCOPED': raise SystemExit(1)
if __name__=='__main__': main()
