from pathlib import Path
import os,sys,subprocess,time,json
from doom_controller_failure_cleanup_v1 import ControllerFailureCleanup
out=Path('/out')
child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],stdin=subprocess.PIPE,text=True)
fd=child.stdin.fileno();os.set_blocking(fd,False);filled=0
while True:
    try: filled+=os.write(fd,b'x'*4096)
    except BlockingIOError: break
os.set_blocking(fd,True)
class Planner:
    closed=False
    def close(self,timeout=1): self.closed=True
planner=Planner();original=ValueError('original controller fault');caught=None;rescued=False
started=time.monotonic()
try:
    try:
        with ControllerFailureCleanup(planner,out) as scope:
            scope.track(child);raise original
    except ValueError as error: caught=error
    result={'elapsed_s':time.monotonic()-started,'filled_pipe_bytes':filled,
            'child_poll_before_probe_cleanup':child.poll(),'planner_closed':planner.closed,
            'primary_identity_preserved':caught is original,'external_rescue_used':False}
    (out/'MEASUREMENT.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))
    assert child.poll() is not None and planner.closed and caught is original
    receipt=json.loads((out/'controller-failure.json').read_text())
    stages={s['stage']:s for s in receipt['stages']}
    assert stages['finish_send']['error_type']=='TimeoutError'
    assert stages['child_wait']['error_type']=='TimeoutExpired'
    assert stages['child_terminate']['status']=='returned'
    assert not receipt['input_release_verified']
finally:
    if child.poll() is None:
        rescued=True;child.kill();child.wait(timeout=3)
    (out/'PROBE_FINAL.json').write_text(json.dumps({'external_rescue_used':rescued,'child_poll':child.poll()}))
