from pathlib import Path
import os,subprocess,sys,threading,time,json
from doom_controller_failure_cleanup_v1 import ControllerFailureCleanup

out=Path('/out')
child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'],stdin=subprocess.PIPE,text=True)
original_wait=child.wait
wait_calls=[]
def recorded_wait(*args,**kwargs):
    wait_calls.append({'started_ns':time.perf_counter_ns(),'timeout':kwargs.get('timeout')})
    return original_wait(*args,**kwargs)
child.wait=recorded_wait
fd=child.stdin.fileno();os.set_blocking(fd,False);filled=0
while True:
    try: filled+=os.write(fd,b'x'*4096)
    except BlockingIOError: break
os.set_blocking(fd,True)
class Planner:
    closed=False
    def close(self,timeout=1): self.closed=True
planner=Planner();started=threading.Event();result={}
def cleanup():
    try:
        with ControllerFailureCleanup(planner,out) as scope:
            scope.track(child);started.set();raise ValueError('original controller fault')
    except BaseException as error:
        result.update(error_type=type(error).__name__,error=str(error))
thread=threading.Thread(target=cleanup,daemon=True);thread.start();assert started.wait(1)
time.sleep(.5)
before={'filled_pipe_bytes':filled,'cleanup_thread_alive':thread.is_alive(),'child_poll':child.poll(),
        'wait_calls':list(wait_calls),'planner_closed':planner.closed,'helper_result':dict(result),
        'actor':'measurement before separately owned probe kill','observation_interval_s':.5}
(out/'BEFORE_EXTERNAL_RELEASE.json').write_text(json.dumps(before,indent=2))
try:
    child.kill();exit_code=original_wait(timeout=3);thread.join(timeout=3)
finally:
    if child.poll() is None: child.kill();original_wait(timeout=3)
after={'actor':'probe killed direct child to release blocked finish','child_exit':exit_code,
       'cleanup_thread_alive':thread.is_alive(),'planner_closed':planner.closed,'result':result,'wait_calls':wait_calls}
(out/'AFTER_EXTERNAL_RELEASE.json').write_text(json.dumps(after,indent=2))
print(json.dumps({'before':before,'after':after}))
assert before['cleanup_thread_alive'] and before['wait_calls']==[] and before['planner_closed'] is False
assert before['helper_result']=={} and before['child_poll'] is None
assert after['cleanup_thread_alive'] is False and after['planner_closed'] is True
assert after['result']['error_type']=='ValueError'
