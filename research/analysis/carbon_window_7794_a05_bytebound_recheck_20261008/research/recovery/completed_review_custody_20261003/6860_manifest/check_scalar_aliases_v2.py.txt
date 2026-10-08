from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

root=Path(__file__).resolve().parent
evidence=root/'source-v2/runtime/results/manifest-enum-types-01a0ff33'
def load(name):
    spec=importlib.util.spec_from_file_location(name,evidence/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
v1=load('audit_matrix');v2=load('audit_matrix_v2')
raw=json.loads((evidence/'after.json').read_bytes())
fixtures=json.loads((evidence/'fixtures.json').read_bytes())
identity=json.loads((evidence/'SOURCE_MANIFEST.json').read_bytes())
def paths(value,path=()):
    if type(value)is dict:
        for k,v in value.items():yield from paths(v,path+(k,))
    elif type(value)is list:
        for i,v in enumerate(value):yield from paths(v,path+(i,))
    elif type(value)is bool:
        yield path,int(value);yield path,float(value)
    elif type(value)is int:
        yield path,float(value)
        if value in (0,1):yield path,bool(value)
    elif type(value)is float and value.is_integer():
        yield path,int(value)
observed=[]
for row_index,row in enumerate(raw['rows']):
    for label in ('manifest','validate','admit','readiness'):
        for path,value in paths(row[label]):
            mutated=deepcopy(raw);target=mutated['rows'][row_index][label]
            for part in path[:-1]:target=target[part]
            target[path[-1]]=value
            before=v1.verify(mutated,fixtures,False,identity['after_source_sha256'])
            after=v2.verify(mutated,fixtures,False,identity['after_source_sha256'])
            observed.append({'row':row['id'],'label':label,'path':list(path),'replacement_type':type(value).__name__,
                             'v1_rejected':bool(before),'v2_rejected':bool(after)})
result={'cases':len(observed),'v1_rejected':sum(x['v1_rejected'] for x in observed),
        'v2_rejected':sum(x['v2_rejected'] for x in observed),'rows':observed,
        'unexpected_v2_acceptance':[x for x in observed if not x['v2_rejected']]}
with (root/'scalar-aliases-v2.raw.json').open('x',encoding='utf-8',newline='\n')as f:
    json.dump(result,f,sort_keys=True);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
sys.exit(bool(result['unexpected_v2_acceptance']))
