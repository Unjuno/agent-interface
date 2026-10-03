"""Bounded plain-data report retention; never grants execution authority."""
import hashlib,json,math,os
from pathlib import Path

SCHEMA='caller-report-retention-inthex-v1'
def encode(value, *, max_bytes=65536):
    if type(max_bytes) is not int or not 1<=max_bytes<=1048576:raise ValueError('bounded output limit')
    seen=set();nodes=0;budget=0
    def walk(v,depth):
        nonlocal nodes,budget
        nodes+=1
        if nodes>20000 or depth>32:raise ValueError('tree limit')
        if v is None:return ['null',None]
        if type(v) is bool:return ['bool',v]
        if type(v) is int:
            if v.bit_length()>32768:raise ValueError('integer limit')
            text=hex(v);budget+=len(text)
            if budget>max_bytes:raise ValueError('output limit')
            return ['int',text]
        if type(v) is float:
            if not math.isfinite(v):raise ValueError('finite float required')
            return ['float',repr(v)]
        if type(v) is str:
            budget+=len(v.encode('utf-8'))
            if budget>max_bytes:raise ValueError('output limit')
            return ['str',v]
        if type(v) not in (dict,list):raise ValueError('plain JSON tree required')
        if id(v) in seen:raise ValueError('cycle')
        seen.add(id(v))
        try:
            if type(v) is list:return ['list',[walk(x,depth+1) for x in v]]
            if any(type(k) is not str for k in v):raise ValueError('string keys required')
            for k in v:
                budget+=len(k.encode('utf-8'))
                if budget>max_bytes:raise ValueError('output limit')
            return ['dict',[[k,walk(x,depth+1)] for k,x in v.items()]]
        finally:seen.remove(id(v))
    tree=walk(value,0)
    b=json.dumps({'schema':SCHEMA,'tree':tree},ensure_ascii=True,separators=(',',':'),allow_nan=False).encode('utf-8')
    if len(b)>max_bytes:raise ValueError('output limit')
    return b

def decode(data, *, max_bytes=65536):
    if type(data) is not bytes or len(data)>max_bytes:raise ValueError('bounded bytes required')
    value=json.loads(data)
    if type(value) is not dict or set(value)!={'schema','tree'} or value['schema']!=SCHEMA:raise ValueError('exact envelope')
    nodes=0
    def walk(n,depth):
        nonlocal nodes
        nodes+=1
        if nodes>20000 or depth>32 or type(n) is not list or len(n)!=2:raise ValueError('bounded node')
        t,v=n
        if t=='null' and v is None:return None
        if t=='bool' and type(v) is bool:return v
        if t=='str' and type(v) is str:return v
        if t=='int' and type(v) is str and len(v)<=8196:
            x=int(v,16)
            if x.bit_length()<=32768 and hex(x)==v:return x
        if t=='float' and type(v) is str:
            x=float(v)
            if math.isfinite(x) and repr(x)==v:return x
        if t=='list' and type(v) is list:return [walk(x,depth+1) for x in v]
        if t=='dict' and type(v) is list:
            result={}
            for pair in v:
                if type(pair) is not list or len(pair)!=2 or type(pair[0]) is not str or pair[0] in result:raise ValueError('unique string key')
                result[pair[0]]=walk(pair[1],depth+1)
            return result
        raise ValueError('canonical typed value')
    restored=walk(value['tree'],0)
    if encode(restored,max_bytes=max_bytes)!=data:raise ValueError('canonical envelope bytes')
    return restored

def write_report(report, directory, *, max_bytes=65536):
    """Keep normal JSON bytes; fallback preserves all original plain values.

    Destination is caller-owned, absent report filenames. This is successful
    write/readback custody, not crash-atomicity or hostile filesystem isolation.
    """
    fallback=encode(report,max_bytes=max_bytes)
    try:
        data=(json.dumps(report,indent=2)+'\n').replace('\n',os.linesep).encode('utf-8')
        name='report.json';kind='ordinary_json';error=None
    except ValueError as e:
        data=fallback;name='report.lossless.json';kind='lossless_inthex';error={'type':type(e).__name__,'message':str(e)}
    if len(data)>max_bytes:raise ValueError('output limit')
    directory=Path(directory)
    if (directory/'report.json').exists() or (directory/'report.lossless.json').exists():raise FileExistsError('existing report retained')
    destination=directory/name
    with destination.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    if destination.read_bytes()!=data:raise IOError('report readback mismatch')
    return {'kind':kind,'name':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'original_json_error':error,'operation_invoked':False,'grants_input_authority':False}

def read_report(directory, receipt, *, max_bytes=65536):
    required={'kind','name','bytes','sha256','original_json_error','operation_invoked','grants_input_authority'}
    if type(receipt) is not dict or set(receipt)!=required or receipt['operation_invoked'] is not False or receipt['grants_input_authority'] is not False:raise ValueError('exact data-only receipt')
    names={'ordinary_json':'report.json','lossless_inthex':'report.lossless.json'}
    if receipt.get('kind') not in names or receipt.get('name')!=names[receipt['kind']]:raise ValueError('fixed report name')
    p=Path(directory)/receipt['name']
    if type(receipt['bytes']) is not int or not 0<receipt['bytes']<=max_bytes or p.stat().st_size!=receipt['bytes']:raise ValueError('bounded report')
    data=p.read_bytes()
    if hashlib.sha256(data).hexdigest()!=receipt['sha256']:raise ValueError('report hash')
    if receipt['kind']=='lossless_inthex':return decode(data,max_bytes=max_bytes)
    return json.loads(data)
