"""Synthetic metadata-only paired timing; not an end-to-end GUI benchmark."""
from collections import OrderedDict
import gc, json, os, pathlib, statistics, time, tracemalloc
from PIL import Image
from history_baseline import ObservationHistory
from segment import SegmentedAppendMap


class AppendOnlyObservationHistory:
    def __init__(self,capacity=2):
        self.capacity=capacity;self._records=SegmentedAppendMap();self._decoded=OrderedDict()
    def fork(self):
        other=AppendOnlyObservationHistory(self.capacity)
        other._records=self._records.fork();other._decoded=self._decoded.copy();return other
    def append(self,key,value):
        observation,image=value;native=observation['native'];artifact=native['artifact']
        if (image.mode!='RGB' or image.size!=(native['width'],native['height'])
                or artifact['source_raw_sha256']!=native['sha256']):
            raise ValueError('observation image identity mismatch')
        self._records.append(key,(observation,(artifact['path'],artifact['sha256'],image.size)))
        self._decoded[key]=image;self._decoded.move_to_end(key)
        while len(self._decoded)>self.capacity:self._decoded.popitem(last=False)


def main():
    out=pathlib.Path('/out');order=os.environ['SIZE_ORDER'];sizes=[0,1000,10000,100000]
    if order=='descending':sizes.reverse()
    elif order!='ascending':raise ValueError('unknown order')
    image=Image.new('RGB',(16,16));observation={'native':{'width':16,'height':16,'sha256':'raw','artifact':{'path':'unused','sha256':'encoded','source_raw_sha256':'raw'}}}
    value=(observation,image);identity=('unused','encoded',(16,16));results=[]
    for size in sizes:
        baseline=ObservationHistory();baseline._records={i:(observation,identity) for i in range(1,size+1)}
        candidate=AppendOnlyObservationHistory()
        for i in range(1,size+1):candidate._records.append(i,(observation,identity))
        assert len(baseline)==len(candidate._records)==size
        if size:
            assert baseline._records[1]==candidate._records[1]
            assert baseline._records[size]==candidate._records[size]
        samples={'dict_copy':[],'segmented':[]}
        for trial in range(41):
            for name in (('dict_copy','segmented') if trial%2==0 else ('segmented','dict_copy')):
                start=time.perf_counter_ns()
                if name=='dict_copy':
                    staged=baseline.fork();staged[size+1]=value
                else:
                    staged=candidate.fork();staged.append(size+1,value)
                del staged
                samples[name].append(time.perf_counter_ns()-start)
        peaks={}
        for name in ('dict_copy','segmented'):
            gc.collect();tracemalloc.start()
            if name=='dict_copy':staged=baseline.fork();staged[size+1]=value
            else:staged=candidate.fork();staged.append(size+1,value)
            _,peaks[name]=tracemalloc.get_traced_memory();tracemalloc.stop();del staged
        assert len(baseline)==len(candidate._records)==size
        results.append({'size':size,'samples_ns':samples,'median_ns':{k:statistics.median(v) for k,v in samples.items()},'peak_new_bytes':peaks})
    result={'status':'completed','size_order':order,'repetitions':41,'results':results}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
