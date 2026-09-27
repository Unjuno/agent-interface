"""Private, bounded JSON-line producer/consumer workers; no external endpoints."""
from __future__ import annotations
import argparse
import json
import os
import sqlite3
import sys
import time
import contiguous_model as model
from gap_policy import GapPolicy


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--db', required=True)
    p.add_argument('--role', choices=['producer', 'consumer'], required=True)
    p.add_argument('--policy', required=True)
    args = p.parse_args()
    gate = GapPolicy(args.policy)
    con = sqlite3.connect(args.db, timeout=2)
    print(json.dumps({'ready': True, 'pid': os.getpid(), 'role': args.role}), flush=True)
    for line in sys.stdin:
        if len(line) > 8192:
            raise ValueError('request too long')
        req = json.loads(line)
        begin = time.monotonic_ns()
        op = req['op']
        result = {}
        if op == 'stop':
            result = {'status': 'STOPPED'}
        else:
            con.execute('BEGIN IMMEDIATE')
            try:
                if args.role == 'producer' and op == 'offer':
                    seq = req['seq']
                    if type(seq) is not int or seq not in (4, 5, 6, 7):
                        raise ValueError('outside synthetic event set')
                    result['status'] = model.producer_offer(
                        con, 2, seq, f'E{seq}', model.digest(f'p{seq}'), 'sequence_pos')
                elif args.role == 'consumer' and op == 'ack':
                    result['status'] = model.ack_through(con, 4, model.ack_digest(con, 4))
                elif args.role == 'consumer' and op == 'poll':
                    steps = []
                    for _ in range(3):
                        head = con.execute('SELECT seq,event_id,payload_sha FROM pending ORDER BY pos LIMIT 1').fetchone()
                        if head is None:
                            gate.clear()
                            steps.append({'status': 'NO_PENDING', 'observed_ns': time.monotonic_ns()})
                            break
                        status = model.pending_retry(con, *head)
                        observed = time.monotonic_ns()
                        step = {'status': status, 'head': list(head), 'observed_ns': observed}
                        if status == 'EVENT_PREDECESSOR_MISSING':
                            mx = con.execute('SELECT MAX(seq) FROM consumer').fetchone()[0]
                            step.update(gate.observe([mx + 1, head[0], head[1]], observed))
                            steps.append(step)
                            break
                        gate.clear()
                        steps.append(step)
                        if status != 'EVENT_ACCEPTED':
                            break
                    result = {'steps': steps}
                else:
                    raise ValueError('role/op mismatch')
                con.commit()
            except BaseException:
                con.rollback()
                raise
        result.update(request_id=req['request_id'], pid=os.getpid(),
                      begin_ns=begin, end_ns=time.monotonic_ns())
        print(json.dumps(result, separators=(',', ':')), flush=True)
        if op == 'stop':
            break
    con.close()

if __name__ == '__main__':
    main()
