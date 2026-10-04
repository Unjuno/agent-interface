import json
import os
import select
import sys
import time

case=sys.argv[1]
ready=b'{"event":"ready","fixture":"E02"}\n'
payloads={'healthy':ready,'json_fault':b'{"event":\n','ready_then_fault':ready,
          'array':b'[1]\n','utf8_fault':b'\xff\n','eof_live':b''}
with open(sys.argv[2],'x') as receipt:
    def record(kind,payload,written,start,end):
        receipt.write(json.dumps(dict(kind=kind,pid=os.getpid(),ppid=os.getppid(),
            hex=payload.hex(),written=written,start_ns=start,return_ns=end,monotonic_ns=time.monotonic_ns()))+'\n')
        receipt.flush()
    def emit(payload):
        start=time.monotonic_ns()
        n=os.write(1,payload)
        record('write',payload,n,start,time.monotonic_ns())
    if case=='eof_live':
        start=time.monotonic_ns()
        sys.stdout.close()
        os.close(1)
        record('stdout-close',b'',0,start,time.monotonic_ns())
    else: emit(payloads[case])
    if case=='ready_then_fault':
        if not select.select([sys.stdin],[],[],5)[0]: sys.exit(2)
        if sys.stdin.buffer.readline()!=b'CONTINUE\n': sys.exit(3)
        emit(b'{"event":\n')
    if not select.select([sys.stdin],[],[],5)[0]: sys.exit(2)
    sys.stdin.buffer.read()
