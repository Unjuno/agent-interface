#!/usr/bin/env python3
import time
from experiment import wait_effect
class Q:
 def get(self,timeout):time.sleep(.004);return {'session_id':'s','request_id':'r','role':'TASK_SEMANTIC_EFFECT'}
d=time.perf_counter_ns()+2_000_000;r,w=wait_effect(Q(),d,'s','r');assert r is None and w>=d;print('PASS_LATE_WAKE_REJECTED',(w-d)/1e6)
