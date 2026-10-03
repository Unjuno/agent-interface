"""Saved-only mount-order adapter; no acquisition or predecessor writes."""
import copy
import json
from pathlib import Path

def guard_output(predecessor, output, source):
    predecessor,output,source=Path(predecessor).resolve(),Path(output).resolve(),Path(source).resolve()
    for protected in (predecessor,source):
        if output==protected or protected in output.parents:
            raise ValueError('output overlaps protected input/source tree')
    return predecessor,output

def mount_map(mounts, freeze):
    if type(mounts) is not list or len(mounts)!=2: raise ValueError('closed two-mount denominator')
    actual={}
    for m in mounts:
        if type(m) is not dict or m.get('Type')!='bind': raise ValueError('bind mount required')
        destination=m.get('Destination');source=m.get('Source');rw=m.get('RW')
        if type(destination) is not str or type(source) is not str or type(rw) is not bool:
            raise ValueError('exact mount field types')
        if destination in actual: raise ValueError('duplicate mount destination')
        actual[destination]=(source,rw)
    expected={'/src':(freeze['guest_source'],False),'/out':(freeze['guest_output'],True)}
    if actual!=expected: raise ValueError('closed source/output mount map')
    return actual

def unique(pairs):
    out={}
    for key,value in pairs:
        if key in out: raise ValueError('duplicate inspection JSON field')
        out[key]=value
    return out

def normalize_launch(receipt, freeze):
    state=json.loads(receipt['inspect_stdout'],object_pairs_hook=unique,
                     parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    mount_map(state['Mounts'],freeze)
    result=copy.deepcopy(receipt)
    state['Mounts']=sorted(state['Mounts'],key=lambda m: {'/src':0,'/out':1}[m['Destination']])
    result['inspect_stdout']=json.dumps(state,sort_keys=True,allow_nan=False)
    return result
