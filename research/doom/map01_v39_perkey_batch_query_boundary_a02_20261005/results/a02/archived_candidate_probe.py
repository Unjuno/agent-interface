import ast, hashlib, json, time
from pathlib import Path
HERE=Path(__file__).resolve().parent
SOURCE=HERE/'input_owner_v12.py'
source=SOURCE.read_text(encoding='utf-8')
tree=ast.parse(source)
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_classify_release')
ns={}
exec(compile(ast.Module(body=[fn],type_ignores=[]),str(SOURCE),'exec'),ns)
class FakeDevice:
    def __init__(self, physical, fail_inject_at=None):
        self.physical=set(physical); self.fail_inject_at=fail_inject_at; self.inject_count=0; self.ops=[]
    def query(self):
        bitmap=bytearray(32)
        for code in self.physical: bitmap[code//8]|=1<<(code%8)
        self.ops.append({'operation':'keymap-query','bitmap_down':sorted(self.physical)})
        return {'available':True,'down':frozenset(self.physical)}
    def up(self,code):
        self.inject_count+=1
        if self.inject_count==self.fail_inject_at:
            self.ops.append({'operation':'key-up-failed','keycode':code})
            return False
        self.ops.append({'operation':'key-up','keycode':code})
        self.physical.discard(code)
        return True
    def sync(self): self.ops.append({'operation':'sync'}); return True

def classify(owner_owned, pre, attempted, sync_ok, post):
    return ns['_classify_release'](owner_owned,pre,attempted,sync_ok,post)

def sequential():
    d=FakeDevice({65,74}); rows=[]
    for code in (65,74):
        pre=d.query(); attempted=True; injected=d.up(code); sync_ok=d.sync(); post=d.query()
        status,_=classify(True,code in pre['down'],attempted,sync_ok and injected,code in post['down'])
        rows.append({'keycode':code,'classification':status,'release_attempted':attempted,'injection_succeeded':injected,'sync_succeeded':sync_ok and injected,'pre_down':code in pre['down'],'post_down':code in post['down'],'grants_input_authority':False})
    return {'mode':'sequential_per_key','rows':rows,'ops':d.ops,'final_down':sorted(d.physical)}

def batched(fail_inject_at=None):
    d=FakeDevice({65,74},fail_inject_at); pre=d.query(); attempts={}; injected={}
    for code in (65,74): attempts[code]=True; injected[code]=d.up(code)
    sync_ok=d.sync(); post=d.query(); rows=[]
    for code in (65,74):
        key_sync=sync_ok and injected[code]
        if pre['available'] and post['available']:
            status,_=classify(True,code in pre['down'],attempts[code],key_sync,code in post['down'])
        else: status='PHYSICAL_SAMPLE_UNAVAILABLE'
        rows.append({'keycode':code,'classification':status,'release_attempted':attempts[code],'injection_succeeded':injected[code],'sync_succeeded':key_sync,'pre_down':code in pre['down'],'post_down':code in post['down'],'grants_input_authority':False})
    return {'mode':'batched_boundary_samples','rows':rows,'ops':d.ops,'final_down':sorted(d.physical)}

def between_queries(ops):
    ups=[i for i,x in enumerate(ops) if x['operation'] in ('key-up','key-up-failed')]
    return sum(x['operation']=='keymap-query' for x in ops[ups[0]+1:ups[1]])
result={'schema':'issue59-batch-boundary-a01-result-v1','source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'runs':[sequential(),batched(),batched(fail_inject_at=2)]}
for r in result['runs']:
    r['keymap_query_count']=sum(x['operation']=='keymap-query' for x in r['ops'])
    r['queries_between_up_injections']=between_queries(r['ops'])
(HERE/'RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'EXECUTED','results':[{k:r[k] for k in ('mode','keymap_query_count','queries_between_up_injections','final_down')}|{'classifications':[x['classification'] for x in r['rows']]} for r in result['runs']]}))
