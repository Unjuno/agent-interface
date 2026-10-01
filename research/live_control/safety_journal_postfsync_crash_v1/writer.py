import argparse, json, os, signal, sys, time
from model import append_fsync, init_ledger, make_receipt, publish
ap=argparse.ArgumentParser(); ap.add_argument('--case'); ap.add_argument('--policy'); ap.add_argument('--journal'); ap.add_argument('--ledger'); ap.add_argument('--control-fd',type=int); a=ap.parse_args()
r=make_receipt(a.case); init_ledger(a.ledger); append_fsync(a.journal,r)
os.write(a.control_fd,(json.dumps({'event':'FSYNC_DONE','receipt_id':r['receipt_id']})+'\n').encode()); os.close(a.control_fd)
if a.policy=='post_fsync_sigkill':
    # Parent owns the kill; writer must not publish before it.
    signal.pause()
else:
    print(json.dumps({'writer_publish':publish(a.ledger,r)},sort_keys=True),flush=True)
