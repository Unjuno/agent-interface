"""Additive reference over frozen peer executor; not public runtime adoption."""
import time
from executor_v12 import Executor as Previous

class Executor(Previous):
 def __init__(self,backend,emit):
  super().__init__(backend,emit)
  self.prestart_failure_receipts=[]
 def submit(self,identifier,steps,expected_sequence,valid_until_ns):
  try:return super().submit(identifier,steps,expected_sequence,valid_until_ns)
  except Exception as error:
   with self.lock:
    job=self.active
    if job is not None and job[0]==identifier and job[2].ident is None:
     # Worker never started: do not replay accepted or start positive input.
     job[1].set()
     self.closed=True
     self.prestart_failure_receipts.append({'id':identifier,'status':'delivery_unknown','worker_started':False,'recorded_ns':time.perf_counter_ns(),'error_type':type(error).__name__,'input_authority':False,'executor_closed':True})
     self.active=None
   raise
