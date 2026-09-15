"""Adapt retained main-thread scorer polling to the v12 stdin iterator contract."""
from __future__ import annotations
import json,statistics,threading
from pathlib import Path
from main_thread_scorer_polling_v1 import MainThreadScorerPolling
from independent_progress_clock_v2 import ProgressClock,ProgressSample,append_jsonl,summarize_events

class ScorerFileSink:
    """Persist scorer-only samples/events without a controller-visible callback."""
    def __init__(self,out:Path):
        self.out=Path(out);self.clock=ProgressClock();self.samples=[];self.events=[];self.owner_thread=threading.get_ident()
    def __call__(self,receipt):
        if threading.get_ident()!=self.owner_thread:raise RuntimeError('scorer sink left session main thread')
        sample=receipt.get('payload')
        if not isinstance(sample,ProgressSample):raise TypeError('scorer payload must be ProgressSample')
        events=self.clock.ingest(sample)
        row={k:v for k,v in receipt.items() if k!='payload'};row['payload']=sample.as_dict();row['controller_visible']=False
        self.out.mkdir(parents=True,exist_ok=True)
        with (self.out/'scorer-samples.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(row,sort_keys=True)+'\n')
        if events:append_jsonl(self.out/'scorer-events.jsonl',events);self.events.extend(events)
        self.samples.append(row)
    def direct(self,sample,clock_ns):
        now=clock_ns();self({'scheduled_ns':now,'sample_started_ns':now,'sample_finished_ns':now,'start_lateness_ns':0,'missed_periods_before':0,'payload':sample,'direct_final_sample':True})
    def finalize(self,stats):
        ns=[r['payload']['sample_ns'] for r in self.samples];intervals=[b-a for a,b in zip(ns,ns[1:])]
        summary={'schema':'map01-independent-scorer-integration-v3','controller_visible':False,'sample_count':len(self.samples),'event_count':len(self.events),'event_summary':summarize_events(self.events),'scheduler':stats,'sample_interval_ms':None,'zero_positive_events_allowed':True}
        if intervals:
            ordered=sorted(intervals);summary['sample_interval_ms']={'median':statistics.median(intervals)/1e6,'p95':ordered[min(len(ordered)-1,round(.95*(len(ordered)-1)))]/1e6,'max':max(intervals)/1e6}
        if self.out.exists() or self.samples:
            self.out.mkdir(parents=True,exist_ok=True);(self.out/'scorer-summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8')
        return summary

class MainThreadScorerStdin:
    """Text iterator using the retained polling scheduler's timing/I/O primitives."""
    def __init__(self,stream,sample_fn,sink,sample_hz=35.0,loop=None):
        self.stream=stream;self.fd=stream.fileno();self.sample_fn=sample_fn;self.sink=sink
        self.loop=loop or MainThreadScorerPolling(sample_hz=sample_hz)
        self.owner_thread=threading.get_ident();self.next_sample_ns=None;self.buffer=bytearray();self.samples=0;self.commands=0;self.missed=0;self.eof=False
    def __iter__(self):return self
    def _sample_due(self):
        now=self.loop.clock_ns()
        if self.next_sample_ns is None:self.next_sample_ns=now
        if now<self.next_sample_ns:return False
        elapsed=((now-self.next_sample_ns)//self.loop.period_ns)+1;skipped=max(0,elapsed-1);scheduled=self.next_sample_ns;self.next_sample_ns+=elapsed*self.loop.period_ns;self.missed+=skipped
        started=self.loop.clock_ns();payload=self.sample_fn();finished=self.loop.clock_ns()
        self.sink({'scheduled_ns':scheduled,'sample_started_ns':started,'sample_finished_ns':finished,'start_lateness_ns':max(0,started-scheduled),'missed_periods_before':skipped,'payload':payload})
        self.samples+=1;return True
    def __next__(self):
        if threading.get_ident()!=self.owner_thread:raise RuntimeError('scorer stdin left session main thread')
        while True:
            if self._sample_due():continue
            newline=self.buffer.find(b'\n')
            if newline>=0:
                raw=bytes(self.buffer[:newline]);del self.buffer[:newline+1]
                if not raw:continue
                self.commands+=1;return raw.decode('utf-8',errors='strict')
            now=self.loop.clock_ns();timeout=max(0,(self.next_sample_ns-now)/1e9)
            if not self.loop.wait_readable(self.fd,timeout):continue
            chunk=self.loop.read_fn(self.fd,65536)
            if chunk==b'':
                self.eof=True
                if self.buffer:raise ValueError('unterminated command at EOF')
                raise StopIteration
            self.buffer.extend(chunk)
            if len(self.buffer)>self.loop.max_buffer_bytes:raise ValueError('command buffer exceeded max_buffer_bytes')
    def stats(self):
        return {'owner_thread_id':self.owner_thread,'samples':self.samples,'commands':self.commands,'missed_sample_periods':self.missed,'eof':self.eof,'sample_hz':1e9/self.loop.period_ns}
