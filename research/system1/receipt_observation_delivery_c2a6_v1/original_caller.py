"""Compare whole-stream EOF acquisition with one bounded newline-delimited frame."""
from __future__ import annotations
import copy, importlib.util, json, os, signal, subprocess, sys, time
from pathlib import Path
from common import encode, save, until
from policy import describe

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('retained_4231_classifier',ROOT/'predecessor/run.py')
assert spec is not None and spec.loader is not None
previous=importlib.util.module_from_spec(spec); spec.loader.exec_module(previous)

def main() -> None:
    case=Path(sys.argv[1]).resolve()
    config=json.loads((case/'config.json').read_bytes())
    log=(case/'caller.events.jsonl').open('xb',buffering=0)
    seq=0
    def event(kind: str, **fields: object) -> None:
        nonlocal seq
        seq+=1
        log.write(encode({'seq':seq,'kind':kind,'pid':os.getpid(),'at_ns':time.monotonic_ns(),**fields}))
    def timeout(signum: int, frame: object) -> None:
        raise TimeoutError('owned caller bound of 3 seconds exceeded')
    signal.signal(signal.SIGALRM,timeout); signal.alarm(3)
    process=None
    with (case/'owner.stderr.bin').open('xb') as err:
        try:
            argv=[sys.executable,'-S','-B',str(ROOT/'source/owner.py'),str(case)]
            process=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err)
            assert process.stdin is not None and process.stdout is not None
            event('SPAWN',owner_pid=process.pid,argv=argv)
            ready_bytes=process.stdout.readline(65537)
            (case/'ready.bin').write_bytes(ready_bytes)
            ready=json.loads(ready_bytes)
            if ready.get('pid')!=process.pid or ready.get('kind')!='READY':
                raise ValueError('owner readiness mismatch')
            start=time.monotonic_ns()
            context={k:config[k] for k in ('case_id','session','request','clock_id')}
            context.update(start_ns=start,deadline_ns=start+120_000_000)
            request={'context':context,'schedule':config['timing']}
            raw=encode(request)
            (case/'caller.request.bin').write_bytes(raw)
            event('REQUEST_SEND',context=context)
            process.stdin.write(raw); process.stdin.flush(); process.stdin.close()
            until(start+config['timing']['reader_ms']*1_000_000)
            before=time.monotonic_ns(); event('READ_BEGIN',sample_ns=before,reader=config['reader'])
            # Both arms use the same BufferedReader, owner, framing and timing.
            data=(process.stdout.read() if config['reader']=='READ_TO_EOF'
                  else process.stdout.readline(65537))
            after=time.monotonic_ns(); event('READ_RETURN',sample_ns=after,byte_count=len(data))
            (case/'caller.frame.bin').write_bytes(data)
            receipt=None
            if len(data)<=65536 and data.endswith(b'\n') and data.count(b'\n')==1:
                try:
                    receipt=json.loads(data)
                except (ValueError,UnicodeError):
                    pass
            parsed=time.monotonic_ns(); event('PARSE_COMPLETE',sample_ns=parsed,valid=receipt is not None)
            journal=json.loads((case/'journal.json').read_bytes())
            complete=describe(context,receipt,journal,after,process.pid)
            withheld=describe(context,receipt,None,after,process.pid)
            foreign_receipt=copy.deepcopy(receipt); foreign_journal=copy.deepcopy(journal)
            if foreign_receipt is not None:
                foreign_receipt['context']['session']='foreign-session'
                foreign_journal['context']['session']='foreign-session'
            foreign=describe(context,foreign_receipt,foreign_journal,after,process.pid)
            # Execute only the unmodified predecessor's pure classifier, not its runner.
            legacy=None
            if receipt is not None:
                old_receipt={'session':context['session'],'request':context['request'],
                    'commit_ns':receipt['commit_ns'],'receipt_ns':receipt['receipt_ns'],
                    'status':receipt['status']}
                legacy=previous.classify('RECEIPT_ARRIVAL_DEADLINE',old_receipt,context['deadline_ns'],None)
            decision_ns=time.monotonic_ns(); event('DECISION',sample_ns=decision_ns,report=complete)
            # Finish process accounting AFTER the recorded decision, never as its prerequisite.
            tail=process.stdout.read()
            (case/'caller.tail.bin').write_bytes(tail)
            rc=process.wait(timeout=1)
            end=time.monotonic_ns(); event('OWNER_EXIT',owner_pid=process.pid,returncode=rc,sample_ns=end)
            result={'context':context,'caller_pid':os.getpid(),'owner_pid':process.pid,
                    'reader':config['reader'],'read_begin_ns':before,'read_return_ns':after,
                    'parsed_ns':parsed,'decision_ns':decision_ns,'owner_exit_observed_ns':end,
                    'owner_exit':rc,'legacy_sender_sample':legacy,
                    'report':complete,'withheld_journal_report':withheld,
                    'foreign_pair_report':foreign,'valid_frame':receipt is not None}
            save(case/'caller.json',result)
        except BaseException as exc:
            event('STOP',error=type(exc).__name__,message=str(exc))
            if process is not None and process.poll() is None:
                process.kill(); process.wait(timeout=1)
            raise
        finally:
            signal.alarm(0)
            log.close()

if __name__=='__main__':
    main()
