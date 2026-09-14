"""Pointer-capable backend plus bounded no-input dynamic observation."""
import copy
import time
from session_v9 import Backend as Previous, suite
from executor_v3 import Cancelled


class Backend(Previous):
    def validate(self,steps):
        if not isinstance(steps,list):raise ValueError("steps must be a list")
        rewritten=[];coast_ms=0
        for step in steps:
            if isinstance(step,dict) and step.get("op")=="coast":
                duration=step.get("duration_ms");sample=step.get("sample_ms")
                if type(duration) is not int or not 1<=duration<=5000:
                    raise ValueError("coast duration_ms must be 1-5000")
                if type(sample) is not int or not 50<=sample<=1000:
                    raise ValueError("coast sample_ms must be 50-1000")
                coast_ms+=duration;rewritten.append({"op":"observe"})
            else:rewritten.append(copy.deepcopy(step))
        super().validate(rewritten)
        timed=coast_ms
        for step in steps:
            if not isinstance(step,dict):continue
            op=step.get("op")
            if op=="hold":timed+=step.get("duration_ms",0)
            elif op in ("wait_title","settle"):timed+=step.get("timeout_ms",0)
            elif op=="pointer_drag":timed+=step.get("duration_ms",0)
            elif op=="pointer_click":timed+=step.get("duration_ms",40)
        if timed>10000:raise ValueError("combined wait budget exceeds 10 seconds")

    def execute(self,step,cancel,identifier,index):
        if step["op"]!="coast":return super().execute(step,cancel,identifier,index)
        started=time.perf_counter_ns();deadline=started+step["duration_ms"]*1_000_000;samples=0
        while True:
            if cancel.is_set():raise Cancelled()
            self.snapshot(identifier,index);samples+=1
            remaining=deadline-time.perf_counter_ns()
            if remaining<=0:break
            if cancel.wait(min(step["sample_ms"]/1000,remaining/1e9)):raise Cancelled()
        self.emit({"event":"coast_result","id":identifier,"step":index,"samples":samples,
          "elapsed_ms":(time.perf_counter_ns()-started)/1e6,"input_admissions":0,
          "sequence":self.sequence,"semantic_completion":"unknown"})
