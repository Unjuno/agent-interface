import copy,json,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).parent));from audit import verify
p=pathlib.Path(sys.argv[1]);d=json.loads(p.read_text());muts=[('stale',lambda x:x.__setitem__('stale_semantic_effects',1)),('guard',lambda x:x.__setitem__('hard_effects',1)),('mismatch',lambda x:x.__setitem__('state_mismatch',1)),('discriminator',lambda x:x.__setitem__('install_time_only_stale_semantic_effects',0)),('replay',lambda x:x.__setitem__('response_rebinds',1))];out=[]
for n,f in muts:
 x=copy.deepcopy(d);f(x);v=verify(x);out.append({'name':n,'rejected':not v['audit_pass'],'decision':v['decision']})
ok=all(y['rejected'] for y in out);print(json.dumps({'pass':ok,'controls':out},indent=2));raise SystemExit(0 if ok else 1)
