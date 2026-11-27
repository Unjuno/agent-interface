"""Metadata lookup cost for an append-only synthetic history."""
import json,os,pathlib,random,statistics,time
from segment import SegmentedAppendMap

def main():
    order=os.environ['SIZE_ORDER'];sizes=[1000,10000,100000]
    if order=='descending':sizes.reverse()
    elif order!='ascending':raise ValueError('bad order')
    rows=[]
    for size in sizes:
        baseline={i:i for i in range(1,size+1)};candidate=SegmentedAppendMap()
        for i in range(1,size+1):candidate.append(i,i)
        rng=random.Random(2142+size);random_keys=[rng.randrange(1,size+1) for _ in range(1024)]
        samples={name:[] for name in ('dict_recent','segment_recent','dict_random','segment_random')}
        for trial in range(41):
            names=list(samples)
            if trial%2:names.reverse()
            for name in names:
                mapping=baseline if name.startswith('dict') else candidate
                keys=[size]*1024 if name.endswith('recent') else random_keys
                start=time.perf_counter_ns();total=sum(mapping[k] for k in keys);elapsed=time.perf_counter_ns()-start
                assert total==sum(keys);samples[name].append(elapsed)
        rows.append({'size':size,'samples_ns_per_1024':samples,'median_ns_per_lookup':{k:statistics.median(v)/1024 for k,v in samples.items()}})
    result={'status':'completed','order':order,'repetitions':41,'rows':rows}
    pathlib.Path('/out/result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
