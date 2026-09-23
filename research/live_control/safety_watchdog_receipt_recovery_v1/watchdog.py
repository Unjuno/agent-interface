import json, os, sys, time
from Xlib import X, display
from Xlib.ext import xtest
life_fd=int(sys.argv[1]); receipt_fd=int(sys.argv[2]); journal=sys.argv[3]; arm=sys.argv[4]
keycode=int(sys.argv[5]); ready_fd=int(sys.argv[6]); pid_fd=int(sys.argv[7])
d=display.Display()
owner_pid=int(os.read(pid_fd,64).decode())
os.write(ready_fd,b'WATCHDOG_READY\n')
# Lifetime EOF is the release admission signal; separately confirm PID is gone.
while os.read(life_fd,1) != b'': pass
for _ in range(100):
    try: os.kill(owner_pid,0); time.sleep(.0005)
    except ProcessLookupError: break
else: raise RuntimeError('owner pid still live after lifetime EOF')
death_confirm_ns=time.monotonic_ns()
q=d.query_keymap(); before=bool(q[keycode//8] & (1 << (keycode%8)))
release_request_ns=time.monotonic_ns(); xtest.fake_input(d,X.KeyRelease,keycode); d.sync()
q2=d.query_keymap(); after=bool(q2[keycode//8] & (1 << (keycode%8)))
verified_empty_ns=time.monotonic_ns()
receipt={
 'event':'WATCHDOG_CLEANUP','authority':'none','arm':arm,'owner_pid':owner_pid,'keycode':keycode,
 'owner_dead_confirmed_ns':death_confirm_ns,'release_request_ns':release_request_ns,
 'verified_empty_ns':verified_empty_ns,'key_down_before':before,'key_down_after':after
}
if arm=='watchdog_journal':
    receipt['journal_write_start_ns']=time.monotonic_ns()
    with open(journal,'a') as f:
        f.write(json.dumps(receipt,sort_keys=True)+'\n'); f.flush(); os.fsync(f.fileno())
    receipt['journal_write_done_ns']=time.monotonic_ns()
os.set_blocking(receipt_fd,False)
try:
    os.write(receipt_fd,(json.dumps(receipt,sort_keys=True)+'\n').encode()); pipe_write='ok'
except BlockingIOError:
    pipe_write='blocked'
# stdout is evaluator-only debug and is not an allowed recovery source.
print(json.dumps({'receipt':receipt,'pipe_write':pipe_write},sort_keys=True),flush=True)
