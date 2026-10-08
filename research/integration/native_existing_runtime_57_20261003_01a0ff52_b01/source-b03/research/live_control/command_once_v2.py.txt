"""In-memory, session-local at-most-one write attempt, not exactly-once input."""
import json,threading
from bounded_pipe_writer_v2 import WriteRejected,WriteUncertain


class CommandOnce:
    def __init__(self,write,capacity=1024):
        self.write=write;self.capacity=capacity;self.records={};self.lock=threading.Lock()

    def send(self,request_id,command):
        if not isinstance(request_id,str) or not 1<=len(request_id)<=128:raise ValueError('bounded request ID required')
        if not isinstance(command,dict) or command.get('op') not in ('submit','clock','cancel','pointer_reply','finalization_status','finish'):raise ValueError('runtime command required')
        payload=json.dumps(command,sort_keys=True,separators=(',',':'),allow_nan=False)
        with self.lock:
            if request_id in self.records:
                prior=self.records[request_id]
                if prior['payload']!=payload:raise ValueError('request ID payload conflict')
                return dict(request_id=request_id,replayed=True,**{k:v for k,v in prior.items() if k!='payload'})
            if len(self.records)>=self.capacity:raise ValueError('request registry full; no eviction/retry')
            record=dict(payload=payload,state='write_uncertain');self.records[request_id]=record
            try:self.write(payload+'\n')
            except WriteRejected as exc:record.update(state='rejected_before_write',sent=0,error=str(exc))
            except WriteUncertain as exc:record.update(state='channel_unusable' if exc.reason=='previous failure' else 'write_uncertain',sent=exc.sent,total=exc.total,channel_poisoned=True,error=exc.reason)
            except Exception as exc:record['error']=type(exc).__name__
            else:record['state']='stdin_flushed'
            return dict(request_id=request_id,replayed=False,**{k:v for k,v in record.items() if k!='payload'})
