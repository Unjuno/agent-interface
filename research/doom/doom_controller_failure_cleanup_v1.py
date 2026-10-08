"""Best-effort owned cleanup preserving the controller's primary failure."""
import atexit,json,os,select,threading,time
from collections import Counter


def reject_duplicate_json_members(pairs):
    """Reject duplicate object names when used as json.loads object_pairs_hook."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON member: {key!r}")
        result[key] = value
    return result


def send_failure_finish(stream, timeout=0.25):
    """Attempt finish on an owned POSIX pipe without an unbounded flush.

    This failure-only path cannot certify protocol delivery or input release.
    Unsupported descriptors fail rather than falling back to a blocking write.
    The caller must have exclusive ownership of the stream during teardown.
    """
    if os.name != 'posix':
        raise NotImplementedError('bounded failure finish requires POSIX pipe')
    fd=stream.fileno()
    blocking=os.get_blocking(fd)
    deadline=time.monotonic()+timeout
    data=b'{"op":"finish"}\n'
    os.set_blocking(fd,False)
    try:
        while data:
            remaining=deadline-time.monotonic()
            if remaining <= 0: raise TimeoutError('failure finish pipe deadline')
            if not select.select([], [fd], [], remaining)[1]:
                raise TimeoutError('failure finish pipe deadline')
            try: written=os.write(fd,data)
            except BlockingIOError: continue
            if written <= 0: raise BrokenPipeError('failure finish made no progress')
            data=data[written:]
    finally:
        os.set_blocking(fd,blocking)


class ControllerFailureCleanup:
    def __init__(self, planner, out, finish_timeout=0.5,
                 child_wait_timeout=5, escalation_wait_timeout=1):
        self.planner=planner;self.out=out;self.process=None
        self.finish_timeout=finish_timeout
        self.child_wait_timeout=child_wait_timeout
        self.escalation_wait_timeout=escalation_wait_timeout
        self.failed_stage='controller_setup'
        self.events=None;self.reader=None;self.event_wait=None;self.runtime=None
        self.reader_errors=[]
    def track(self, process):
        self.process=process
    def set_stage(self, name):
        self.failed_stage=name
    def observe_output(self, events, reader, event_wait, runtime, reader_errors=None):
        self.events=events;self.reader=reader;self.event_wait=event_wait
        self.runtime=runtime
        self.reader_errors=[] if reader_errors is None else reader_errors
    def __enter__(self): return self
    def __exit__(self, kind, error, traceback):
        if error is None: return False
        receipt={'format':'controller-failure-cleanup-v1', 'primary_error_type':kind.__name__,
                 'failed_stage':self.failed_stage,'stages':[], 'input_release_verified':False,
                 'input_releases_verified_empty':False,
                 'scope':'owned child process only; no physical release or scorer certificate'}
        def attempt(name, operation):
            try:
                result=operation()
                receipt['stages'].append({'stage':name,'status':'returned','result':result})
                return True
            except BaseException as secondary:
                receipt['stages'].append({'stage':name,'status':'failed','error_type':type(secondary).__name__})
                try: error.add_note(name+' cleanup failed: '+type(secondary).__name__)
                except BaseException: pass
                return False
        def bounded(name, operation, timeout):
            result=[];finished=threading.Event()
            def invoke():
                try:result.append((True,operation()))
                except BaseException as secondary:result.append((False,secondary))
                finally:finished.set()
            worker=threading.Thread(target=invoke,daemon=True,name='controller-cleanup-'+name)
            if not attempt(name+'_worker_start',worker.start):return False,None,None
            if not finished.wait(timeout):
                receipt['stages'].append({'stage':name,'status':'timed_out',
                                          'timeout_seconds':timeout})
                try:error.add_note(name+' cleanup timed out')
                except BaseException:pass
                return False,None,worker
            worker.join(timeout=.1)
            succeeded,value=result[0]
            if succeeded:
                receipt['stages'].append({'stage':name,'status':'returned','result':value})
                return True,value,worker
            receipt['stages'].append({'stage':name,'status':'failed',
                                      'error_type':type(value).__name__})
            try:error.add_note(name+' cleanup failed: '+type(value).__name__)
            except BaseException:pass
            return False,None,worker
        child=self.process
        if child is not None:
            polled=attempt('child_poll_before',child.poll)
            if not polled or receipt['stages'][-1]['result'] is None:
                finish_sent=attempt('finish_send',lambda:send_failure_finish(
                    child.stdin,timeout=self.finish_timeout))
                if finish_sent and self.event_wait is not None:
                    attempt('post_control_score_wait',lambda:self.event_wait(
                        lambda row: type(row) is dict and
                        row.get('event')=='post_control_score',10))
                if finish_sent:
                    if not attempt('child_wait',lambda:child.wait(timeout=self.child_wait_timeout)):
                        attempt('child_terminate',child.terminate)
                        if not attempt('terminated_wait',lambda:child.wait(timeout=self.escalation_wait_timeout)):
                            attempt('child_kill',child.kill)
                            attempt('killed_wait',lambda:child.wait(timeout=self.escalation_wait_timeout))
                else:
                    receipt['stages'].append({'stage':'child_wait','status':'skipped',
                                              'reason':'finish_send_failed'})
                    poll_ok=attempt('child_poll_after_finish_failure',child.poll)
                    if not poll_ok or receipt['stages'][-1]['result'] is None:
                        attempt('child_terminate',child.terminate)
                        if not attempt('terminated_wait',lambda:child.wait(timeout=self.escalation_wait_timeout)):
                            attempt('child_kill',child.kill)
                            attempt('killed_wait',lambda:child.wait(timeout=self.escalation_wait_timeout))
                if hasattr(child.stdin,'close'):
                    bounded('child_stdin_close',child.stdin.close,.5)
            if attempt('child_poll_after',child.poll):
                receipt['child_exit_code']=receipt['stages'][-1]['result']
        bounded('planner_close',lambda:self.planner.close(timeout=1),1)
        attempt('atexit_unregister',lambda:atexit.unregister(self.planner.close))
        receipt['stdout_reader_retired']=False
        if self.reader is not None:
            attempt('stdout_reader_join',lambda:self.reader.join(timeout=5))
            reader_alive=attempt('stdout_reader_alive',self.reader.is_alive)
            if reader_alive:
                receipt['stdout_reader_retired']=not receipt['stages'][-1]['result']
        receipt['stdout_reader_errors']=list(self.reader_errors)
        event_collection_valid=type(self.events) is list
        events=self.events if event_collection_valid else []
        invalid_event_records=sum(type(row) is not dict for row in events)
        if not event_collection_valid:
            invalid_event_records=1
        accepted_rows=[row for row in events if type(row) is dict and
                       row.get('event')=='accepted']
        terminal_rows=[row for row in events if type(row) is dict and
                       row.get('event')=='terminal']
        accepted_id_counts=Counter(row.get('id') for row in accepted_rows
                                   if type(row.get('id')) is str and row.get('id'))
        terminal_id_counts=Counter(row.get('id') for row in terminal_rows
                                   if type(row.get('id')) is str and row.get('id'))
        duplicate_accepted_ids=sorted(identifier for identifier,count in
                                      accepted_id_counts.items() if count>1)
        duplicate_terminal_ids=sorted(identifier for identifier,count in
                                      terminal_id_counts.items() if count>1)
        invalid_accepted_ids=sum(not (type(row.get('id')) is str and row.get('id'))
                                 for row in accepted_rows)
        invalid_terminal_ids=sum(not (type(row.get('id')) is str and row.get('id'))
                                 for row in terminal_rows)
        accepted_ids=set(accepted_id_counts)
        terminal_ids=set(terminal_id_counts)
        accepted_by_id={row.get('id'):row for row in events if type(row) is dict and
                        row.get('event')=='accepted' and type(row.get('id')) is str}
        terminal_by_id={row.get('id'):row for row in events if type(row) is dict and
                        row.get('event')=='terminal' and type(row.get('id')) is str}
        identities_unambiguous=(event_collection_valid and invalid_event_records==0 and
                                not duplicate_accepted_ids and
                                not duplicate_terminal_ids and
                                invalid_accepted_ids==0 and invalid_terminal_ids==0 and
                                accepted_ids==terminal_ids)
        receipt['duplicate_accepted_ids']=duplicate_accepted_ids
        receipt['duplicate_terminal_ids']=duplicate_terminal_ids
        receipt['invalid_event_record_count']=invalid_event_records
        receipt['invalid_accepted_event_id_count']=invalid_accepted_ids
        receipt['invalid_terminal_event_id_count']=invalid_terminal_ids
        receipt['input_event_identities_unambiguous']=identities_unambiguous
        admissions_by_id={identifier:[row for row in events if type(row) is dict and
                                      row.get('event')=='input_admission' and
                                      row.get('id')==identifier]
                          for identifier in accepted_ids}
        released_by_id={identifier:[row for row in events if type(row) is dict and
                                    row.get('event')=='input_released' and
                                    row.get('id')==identifier]
                        for identifier in accepted_ids}
        transitions_by_id={identifier:[row for row in events if type(row) is dict and
                                       row.get('event')=='input_release_transition' and
                                       row.get('id')==identifier]
                           for identifier in accepted_ids}
        def empty_release(record):
            return (type(record) is dict and record.get('verified') is True and
                    record.get('keys_down')==[] and record.get('buttons_down')==[] and
                    record.get('keys_unknown')==[] and record.get('key_state_errors')==[])
        def matching_input_release(identifier, token):
            for row in released_by_id[identifier]:
                owner=row.get('owner_release')
                if (row.get('intent_token')==token and type(owner) is dict and
                        owner.get('intent_token')==token and empty_release(owner)):
                    return True
            return False
        def release_is_verified(identifier):
            terminal=terminal_by_id[identifier]
            release=terminal.get('release')
            if not empty_release(release):
                return False
            accepted_token=accepted_by_id[identifier].get('intent_token')
            if ('intent_token' in release and
                    release.get('intent_token') not in (None, accepted_token)):
                return False
            admissions=admissions_by_id[identifier]
            transitions=transitions_by_id[identifier]
            released=released_by_id[identifier]
            has_active_input=bool(admissions or transitions or released)
            if admissions and (type(accepted_token) is not str or not accepted_token or
                               any(row.get('intent_token')!=accepted_token
                                   for row in admissions)):
                return False
            if terminal.get('status')=='cancelled' and has_active_input:
                return (type(accepted_token) is str and bool(accepted_token) and
                        matching_input_release(identifier, accepted_token))
            if 'intent_token' in release and release.get('intent_token') is None and has_active_input:
                return False
            if 'intent_token' in release and release.get('intent_token') is not None:
                return (type(accepted_token) is str and bool(accepted_token) and
                        release.get('intent_token')==accepted_token)
            return True
        event_set_complete=(receipt['stdout_reader_retired'] and
                            not receipt['stdout_reader_errors'])
        receipt['input_terminals_complete']=(event_set_complete and
                                              identities_unambiguous)
        receipt['input_releases_verified_empty']=(
            receipt['input_terminals_complete'] and
            all(release_is_verified(identifier) for identifier in accepted_ids))
        receipt['input_release_verified_empty']=receipt['input_releases_verified_empty']
        receipt['scorer_terminal_observed']=any(
            type(row) is dict and row.get('event')=='post_control_score' for row in events)
        score_path=None if self.runtime is None else self.runtime/'score.json'
        owner_path=None if self.runtime is None else self.runtime/'owner-events.json'
        receipt['score_file_present']=False
        if score_path is not None and attempt('score_file_presence',score_path.is_file):
            receipt['score_file_present']=receipt['stages'][-1]['result'] is True
        receipt['owner_events_present']=False
        if owner_path is not None and attempt('owner_events_presence',owner_path.is_file):
            receipt['owner_events_present']=receipt['stages'][-1]['result'] is True
        receipt['owner_events_closed']=False
        if receipt['owner_events_present']:
            try:
                owner_rows=json.loads(owner_path.read_text(encoding='utf-8'))
                receipt['owner_events_closed']=(
                    type(owner_rows) is list and bool(owner_rows) and
                    owner_rows[-1].get('reason')=='close' and
                    all(type(row) is dict and row.get('verified') is True
                        for row in owner_rows))
            except BaseException as secondary:
                receipt['stages'].append({'stage':'owner_events_read','status':'failed',
                                          'error_type':type(secondary).__name__})
                try: error.add_note('owner_events_read cleanup failed: '+type(secondary).__name__)
                except BaseException: pass
        child_exit=receipt.get('child_exit_code') is not None
        planner_closed=any(row.get('stage')=='planner_close' and row.get('status')=='returned'
                           for row in receipt['stages'])
        receipt['cleanup_complete']=all((
            child_exit,planner_closed,receipt['stdout_reader_retired'],
            not receipt['stdout_reader_errors'],receipt['input_terminals_complete'],
            receipt['input_releases_verified_empty'],receipt['scorer_terminal_observed'],
            receipt['score_file_present'],receipt['owner_events_closed'],
            all(row.get('status')=='returned' for row in receipt['stages'])))
        attempt('failure_receipt_write',lambda:(self.out/'controller-failure.json').write_text(json.dumps(receipt,indent=2)+'\n'))
        return False
