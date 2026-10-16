"""Self-contained exact JSON-value sharing for repeated large objects; not summarization."""
import copy
import json
from collections import Counter
from report_pages_v2 import digest,MAX_SOURCE


def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)


def unique_pairs(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('duplicate JSON key')
        result[key]=value
    return result


def build(data):
    if not isinstance(data,bytes) or len(data)>MAX_SOURCE:raise ValueError('bounded source bytes required')
    value=json.loads(data,object_pairs_hook=unique_pairs)
    canonical(value)  # Reject non-finite values before constructing any representation.
    counts=Counter()
    def count(node):
        if isinstance(node,(dict,list)):
            key=canonical(node)
            if len(key.encode())>=256:counts[key]+=1
            for child in node.values() if isinstance(node,dict) else node:count(child)
    count(value)
    definitions={};ids={};references=[]
    def encode(node,path):
        if isinstance(node,(dict,list)):
            key=canonical(node)
            if counts[key]>1:
                if key not in ids:
                    identifier='r'+str(len(ids)+1);ids[key]=identifier
                    definitions[identifier]=copy.deepcopy(node)
                identifier=ids[key];references.append(dict(path=path,id=identifier))
                return {'shared_value':identifier}
            if isinstance(node,dict):return {k:encode(v,path+[k]) for k,v in node.items()}
            return [encode(v,path+[i]) for i,v in enumerate(node)]
        return node
    document=encode(value,[])
    return dict(format='shared-result-v1',source_sha256=digest(data),definitions=definitions,document=document,references=references,
        scope='All original JSON values retained; definitions are complete literals. Only listed paths are references. No task/authority inference.')


def decode(packed):
    if packed.get('format')!='shared-result-v1':raise ValueError('format required')
    result=copy.deepcopy(packed['document']);definitions=packed['definitions'];paths=[]
    for ref in packed['references']:
        path=ref['path'];identifier=ref['id']
        if not isinstance(path,list) or any(type(k) not in (str,int) for k in path):raise ValueError('invalid reference path')
        if identifier not in definitions:raise ValueError('missing definition')
        if any(path[:len(p)]==p or p[:len(path)]==path for p in paths):raise ValueError('overlapping references')
        paths.append(path)
        node=result
        for key in path[:-1]:
            if isinstance(node,list) and (type(key)is not int or key<0):raise ValueError('invalid list index')
            if isinstance(node,dict) and type(key)is not str:raise ValueError('invalid object key')
            node=node[key]
        if path:
            key=path[-1]
            if isinstance(node,list) and (type(key)is not int or key<0):raise ValueError('invalid list index')
            if isinstance(node,dict) and type(key)is not str:raise ValueError('invalid object key')
            if node[key]!={'shared_value':identifier}:raise ValueError('reference marker mismatch')
            node[key]=copy.deepcopy(definitions[identifier])
        else:
            if result!={'shared_value':identifier}:raise ValueError('root reference mismatch')
            result=copy.deepcopy(definitions[identifier])
    return result
