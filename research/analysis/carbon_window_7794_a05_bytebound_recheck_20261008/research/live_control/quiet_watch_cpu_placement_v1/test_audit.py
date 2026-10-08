#!/usr/bin/env python3
"""Synthetic tests only; no timing measurements, process launch or OS input."""
import copy, json, tempfile
from pathlib import Path
import audit, codec
ROOT=Path(__file__).resolve().parent

def fixture(p, f):
    r={'schema':'cpu_placement_v1','task':p['task'],'mode':'measure','source_sha256':f['sha256'],
       'environment':{'observer_cpu':0,'other_cpu':1,'initial_affinity':[0,1],
       'topology':{'0':{'core_id':'0','physical_package_id':'0'},'1':{'core_id':'1','physical_package_id':'0'}},
       'policy':0,'nice':0},'blocks':[]}
    for t,order in enumerate(p['orders']):
        for arm in order:
            i=len(r['blocks']); start=1000000000+i*1000000000
            late=4000000 if arm=='same' else 100000
            rows=[[start+p['start_delay_ns']+j*p['period_ns'],start+p['start_delay_ns']+j*p['period_ns']+late,late]
                  for j in range(p['samples_per_block'])]
            c=None
            if arm!='idle':
                dest=0 if arm=='same' else 1
                c={'requested_cpu':dest,'ready':{'affinity':[dest],'policy':0,'nice':0},
                   'affinity_before':[dest],'affinity_after':[dest],'alive_before':True,'alive_after':True,
                   'ticks_before':2,'ticks_after':50,'exit_code':-15}
            r['blocks'].append({'index':i,'triplet':t,'arm':arm,'parent_affinity_before':[0],
               'parent_affinity_after':[0],'start_ns':start,'end_ns':rows[-1][1]+100000,
               'thread_cpu_ns':2000000,'process_cpu_ns':2000000,'child':c,'samples':rows})
    return r

def main():
    p=json.loads((ROOT/'plan.json').read_text()); f=json.loads((ROOT/'freeze.json').read_text())
    r=fixture(p,f); positive=audit.inspect(r,p,f)
    assert positive['decision']=='CPU_PLACEMENT_EFFECT_SCOPED'
    rejected=[]
    def trial(name, change):
        x=copy.deepcopy(r); change(x)
        try: audit.inspect(x,p,f)
        except (ValueError,KeyError,TypeError): rejected.append(name)
        else: raise AssertionError('accepted mutation: '+name)
    trial('due_1ns', lambda x: x['blocks'][0]['samples'][1].__setitem__(0,x['blocks'][0]['samples'][1][0]+1))
    trial('wake_1ns',lambda x:x['blocks'][0]['samples'][1].__setitem__(1,x['blocks'][0]['samples'][1][1]+1))
    trial('late_1ns',lambda x:x['blocks'][0]['samples'][1].__setitem__(2,100001))
    trial('boolean_time',lambda x:x['blocks'][0]['samples'][1].__setitem__(2,True))
    trial('missing_sample',lambda x:x['blocks'][0]['samples'].pop())
    trial('overlapping_block',lambda x:x['blocks'][1].__setitem__('start_ns',x['blocks'][0]['start_ns']))
    trial('missing_block',lambda x:x['blocks'].pop())
    trial('arm_order',lambda x:x['blocks'][0].__setitem__('arm','other'))
    trial('parent_affinity',lambda x:x['blocks'][0].__setitem__('parent_affinity_after',[1]))
    trial('child_affinity',lambda x:x['blocks'][1]['child'].__setitem__('affinity_after',[1]))
    trial('dead_child',lambda x:x['blocks'][1]['child'].__setitem__('alive_after',False))
    trial('no_child_cpu',lambda x:x['blocks'][1]['child'].__setitem__('ticks_after',2))
    trial('child_cleanup',lambda x:x['blocks'][1]['child'].__setitem__('exit_code',0))
    trial('source',lambda x:x.__setitem__('source_sha256',{}))
    x=copy.deepcopy(r)
    for b in x['blocks']:
        for row in b['samples']: row[1]=row[0]+100000; row[2]=100000
    assert audit.inspect(x,p,f)['decision']=='HOLD_CPU_PLACEMENT'
    with tempfile.TemporaryDirectory() as d:
        raw=Path(d)/'raw.json'; raw.write_bytes(codec.enc(r))
        codec.pack(raw,Path(d)/'transport')
        assert codec.unpack(Path(d)/'transport')==raw.read_bytes()
        part=next((Path(d)/'transport').glob('raw.part*.b64')); part.write_bytes(b'x'+part.read_bytes()[1:])
        try: codec.unpack(Path(d)/'transport')
        except ValueError: rejected.append('transport_corruption')
        else: raise AssertionError('accepted transport corruption')
    print(json.dumps({'synthetic_pass':True,'rejected':rejected,'negative_count':len(rejected),
                      'hold_control':True,'lossless_roundtrip':True},indent=2))

if __name__=='__main__': main()
