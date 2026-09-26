"""Cooperative disposable effect owner. No network or user files are accessed."""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path
from common import encode, save, digest, until, write_all

def main() -> None:
    folder=Path(sys.argv[1]).resolve()
    pid=os.getpid()
    with (folder/'owner.events.jsonl').open('xb', buffering=0) as log:
        seq=0
        def event(kind: str, **fields: object) -> None:
            nonlocal seq
            seq+=1
            log.write(encode({'seq':seq,'kind':kind,'pid':pid,'at_ns':time.monotonic_ns(),**fields}))
        ready={'kind':'READY','pid':pid,'clock':'CLOCK_MONOTONIC'}
        event('READY')
        write_all(1, encode(ready))
        raw=sys.stdin.buffer.readline(65537)
        (folder/'owner.request.bin').write_bytes(raw)
        request=json.loads(raw)
        context=request['context']
        schedule=request['schedule']
        start=context['start_ns']
        event('REQUEST',context=context)
        until(start + schedule['commit_ms']*1_000_000)
        commit_ns=None
        payload=None
        if schedule['commit']:
            payload=encode({'session':context['session'],'request':context['request'],'value':'private-effect'})
            event('WRITE_BEGIN')
            with (folder/'effect.bin').open('xb') as out:
                out.write(payload); out.flush(); os.fsync(out.fileno())
            commit_ns=time.monotonic_ns()
            event('COMMIT',commit_ns=commit_ns,payload_sha256=digest(payload))
        else:
            event('NO_COMMIT')
        journal={'context':context,'owner_pid':pid,'commit_ns':commit_ns,
                 'payload_sha256':digest(payload) if payload is not None else None,
                 'status':'COMMITTED' if payload is not None else 'NO_COMMIT'}
        with (folder/'journal.json').open('xb') as out:
            out.write(encode(journal)); out.flush(); os.fsync(out.fileno())
        event('JOURNAL_WRITTEN')
        until(start + schedule['send_ms']*1_000_000)
        send_sample=time.monotonic_ns()
        receipt={**journal,'receipt_ns':send_sample}
        complete=encode(receipt)
        transmitted=complete[:-8] if schedule['partial'] else complete
        (folder/'owner.frame.bin').write_bytes(transmitted)
        event('SEND_BEGIN',sender_sample_ns=send_sample,byte_count=len(transmitted))
        write_all(1,transmitted)
        event('SEND_RETURN',byte_count=len(transmitted))
        until(start + schedule['close_ms']*1_000_000)
        event('CLOSE_STDOUT')
        os.close(1)
        event('DONE')

if __name__=='__main__':
    main()
