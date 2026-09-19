"""Private bounded observation stream; cursors neither consume nor authorize."""
import json,threading,time
from collections import deque
from stopped_scope_v2 import validate_scope,boundary
from request_boundary_v2 import request_boundary,SUPPORTED


class EventCursor:
    def __init__(self,capacity=256):
        if type(capacity)is not int or capacity<1:raise ValueError('positive capacity required')
        self.capacity=capacity;self.records=deque();self.sequence=0;self.closed=False
        self.condition=threading.Condition()

    def append(self,record):
        if not isinstance(record,dict) or not isinstance(record.get('event'),str):raise ValueError('event record required')
        encoded=json.dumps(record,allow_nan=False)
        with self.condition:
            if self.closed:raise ValueError('stream closed')
            self.sequence+=1;self.records.append((self.sequence,encoded))
            if len(self.records)>self.capacity:self.records.popleft()
            self.condition.notify_all()
            return self.sequence

    def close(self):
        with self.condition:self.closed=True;self.condition.notify_all()

    def read_until(self,after,events,timeout=5,max_records=64,action_id=None,request_id=None):
        if type(after)is not int or after<0:raise ValueError('nonnegative cursor required')
        if not isinstance(events,(list,tuple)) or not events or any(not isinstance(e,str) for e in events):raise ValueError('event boundary list required')
        if type(timeout) not in (int,float) or not 0<=timeout<=30:raise ValueError('timeout 0..30 required')
        if type(max_records)is not int or not 1<=max_records<=256:raise ValueError('max_records 1..256 required')
        validate_scope(action_id,events)
        if request_id is not None:
            if not isinstance(request_id,str) or not 1<=len(request_id)<=128:raise ValueError('bounded request_id required')
            if action_id is not None or any(e not in SUPPORTED for e in events):raise ValueError('unsupported request-scoped boundary')
        deadline=time.monotonic()+timeout
        with self.condition:
            while True:
                oldest=self.records[0][0] if self.records else self.sequence+1
                if after>self.sequence:raise ValueError('future cursor')
                if after<oldest-1:
                    return dict(status='gap',after=after,oldest=oldest,latest=self.sequence,records=[],cursor=after)
                batch=[];cursor=after;status=None
                for seq,encoded in self.records:
                    if seq<=after:continue
                    record=json.loads(encoded);batch.append(record);cursor=seq
                    if request_id is not None:
                        status=request_boundary(record,events,request_id)
                    else:status=boundary(record,events,action_id)
                    if status:break
                    if len(batch)>=max_records:status='batch_limit';break
                remaining=deadline-time.monotonic()
                if status or self.closed or remaining<=0:
                    return dict(status=status or ('closed' if self.closed else 'timeout'),records=batch,cursor=cursor,
                                returned_ns=time.perf_counter_ns(),authority='none',acknowledgement='not implied')
                self.condition.wait(remaining)
