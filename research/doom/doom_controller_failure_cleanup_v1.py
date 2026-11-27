"""Best-effort owned cleanup preserving the controller's primary failure."""
import atexit,hashlib,json,math,os,select,threading,time
from collections import Counter
from copy import deepcopy


class SessionControlBoundaryFailure(RuntimeError):
    """An observed refusal, never a release or task-effect certificate."""
    def __init__(self, event):
        self.event = deepcopy(event)
        super().__init__('session input retirement unresolved before control effect')


def reject_control_boundary_failure(row):
    # Even an incomplete failure payload stops. Keep it for diagnosis rather
    # than treating a missing obligation field as evidence of neutral input.
    if type(row) is dict and row.get('event') == 'control_boundary_failed':
        raise SessionControlBoundaryFailure(row)


def reject_stdout_reader_failure(row):
    if type(row) is dict and row.get('event') == 'controller_stdout_reader_failed':
        error_type=row.get('error_type')
        suffix='' if type(error_type) is not str else ': '+error_type
        raise RuntimeError('controller stdout capture failed'+suffix)


def reject_duplicate_json_members(pairs):
    """Reject duplicate object names when used as json.loads object_pairs_hook."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON member: {key!r}")
        result[key] = value
    return result


def _reject_nonfinite_json(value):
    raise ValueError("non-finite JSON number: " + value)


def _finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        _reject_nonfinite_json(value)
    return number


def load_controller_event(line):
    return json.loads(line, object_pairs_hook=reject_duplicate_json_members,
                      parse_constant=_reject_nonfinite_json, parse_float=_finite_float)


def capture_raw_stdout_events(stream, path, capture, consume):
    """Retain exact child stdout bytes before parsing each JSONL event."""
    final_path=os.fspath(path)
    temporary_path=final_path+'.partial'
    digest=hashlib.sha256()
    line_count=byte_count=0
    capture.update({'path':temporary_path,'status':'recording','line_count':0,
                    'byte_count':0,'sha256':None})
    try:
        with open(temporary_path,'wb') as output:
            for raw_line in stream:
                if type(raw_line) is not bytes:
                    raise TypeError('raw child stdout must yield bytes')
                output.write(raw_line)
                output.flush()
                digest.update(raw_line)
                line_count+=1
                byte_count+=len(raw_line)
                capture.update({'line_count':line_count,'byte_count':byte_count})
                consume(raw_line)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary_path,final_path)
        capture.update({'path':final_path,'status':'complete',
                        'sha256':digest.hexdigest()})
    except BaseException as error:
        capture.update({'path':temporary_path,'status':'incomplete',
                        'sha256':digest.hexdigest(),
                        'error_type':type(error).__name__})
        raise
    return capture


INPUT_RELEASE_EVENTS = {"input_admission", "input_released", "input_release_transition"}


def _empty_release(record):
    return (type(record) is dict and record.get("verified") is True and
            record.get("keys_down") == [] and record.get("buttons_down") == [] and
            record.get("keys_unknown") == [] and record.get("key_state_errors") == [])


def operation_release_verified(identifier, events, *, require_intent=False):
    release_scope = INPUT_RELEASE_EVENTS | {"accepted", "terminal"}
    rows = [row for row in events if type(row) is dict and row.get("id") == identifier
            and type(row.get("event")) is str and row["event"] in release_scope]
    kinds = [row["event"] for row in rows]
    # The serialized event stream preserves publication order, including any
    # contradictory input evidence read after the program's terminal.
    if (kinds.count("accepted") != 1 or kinds.count("terminal") != 1 or
            kinds[0] != "accepted" or kinds[-1] != "terminal"):
        return False
    accepted, terminal = rows[0], rows[-1]
    release = terminal.get("release")
    if not _empty_release(release):
        return False
    token = accepted.get("intent_token")
    token_verified = type(token) is str and bool(token)
    if ("intent_token" in accepted or require_intent) and not token_verified:
        return False
    release_token = release.get("intent_token")
    if release_token is not None and (not token_verified or release_token != token):
        return False

    admissions = [row for row in rows if row.get("event") == "input_admission"]
    transitions = [row for row in rows if row.get("event") == "input_release_transition"]
    releases = [row for row in rows if row.get("event") == "input_released"]
    if any(row.get("intent_token") != token or not token_verified for row in admissions):
        return False
    if any("intent_token" in row and (not token_verified or row["intent_token"] != token)
           for row in transitions):
        return False
    if len(releases) > 1:
        return False
    matching_release = False
    if releases:
        # Release-only cleanup transitions may follow the owner release, but
        # no further input may be admitted under that same accepted intent.
        if "input_admission" in kinds[kinds.index("input_released") + 1:]:
            return False
        row = releases[0]
        owner = row.get("owner_release")
        matching_release = (token_verified and row.get("intent_token") == token and
                            _empty_release(owner) and owner.get("intent_token") == token)
        if not matching_release:
            return False
    if terminal.get("status") == "cancelled" and (admissions or transitions or releases):
        return matching_release
    if "intent_token" in release and release_token is None and (admissions or transitions or releases):
        return False
    return not require_intent or release_token == token or matching_release


def owner_event_verified(row):
    if type(row) is not dict:
        return False
    event=row.get('event')
    if event=='owner_release':
        return row.get('verified') is True
    if event!='owner_explicit_keyup':
        return False
    attempts=row.get('server_keyup_attempts')
    attempt_count=row.get('server_keyup_attempt_count')
    owner_started=row.get('owner_keyrelease_started_ns')
    owner_returned=row.get('owner_sync_returned_ns')
    sampled=row.get('owner_keymap_sampled_ns')
    attempts_valid=(
        type(attempts) is list and type(attempt_count) is int
        and len(attempts)==attempt_count and 1<=attempt_count<=3
        and type(attempts[0]) is dict and type(attempts[-1]) is dict
        and attempts[0].get('keyrelease_started_ns')==owner_started
        and attempts[-1].get('sync_returned_ns')==owner_returned
        and attempts[-1].get('keymap_sampled_ns')==sampled
        and all(
            type(attempt) is dict and attempt.get('attempt')==index
            and type(attempt.get('keyrelease_started_ns')) is int
            and type(attempt.get('sync_returned_ns')) is int
            and type(attempt.get('keymap_sampled_ns')) is int
            and attempt['keyrelease_started_ns']<=attempt['sync_returned_ns']
            <=attempt['keymap_sampled_ns']
            and type(attempt.get('server_key_down_before')) is bool
            and type(attempt.get('server_key_down_after')) is bool
            for index,attempt in enumerate(attempts,1))
        and all(
            prior['keymap_sampled_ns']<=current['keyrelease_started_ns']
            and prior['server_key_down_after'] is current['server_key_down_before']
            for prior,current in zip(attempts,attempts[1:]))
        and attempts[-1].get('server_key_down_after') is False)
    key_order=row.get('release_batch_key_order')
    return bool(
        row.get('operation')=='up'
        and type(row.get('owner_id')) is str and bool(row.get('owner_id'))
        and type(row.get('key')) is str and bool(row.get('key'))
        and type(row.get('keycode')) is int and row.get('keycode')>0
        and type(row.get('intent_token')) is str and bool(row.get('intent_token'))
        and type(row.get('valid_until_ns')) is int
        and row.get('server_sync_completed') is True
        and row.get('server_keyup_verified') is True
        and row.get('server_key_down_after_keyup') is False
        and row.get('key_state_source')=='x11_query_keymap'
        and type(owner_started) is int and type(owner_returned) is int
        and type(sampled) is int and owner_started<=owner_returned<=sampled
        and row.get('physical_verification_authoritative') is False
        and type(row.get('cancel_requested_after_sync')) is bool
        and type(row.get('release_batch_initial_up_count')) is int
        and type(key_order) is list and bool(key_order)
        and row.get('release_batch_initial_up_count')==len(key_order)
        and all(type(key) is str and bool(key) for key in key_order)
        and row.get('key') in key_order and attempts_valid)


MAX_CHILD_STDERR_BYTES=1_048_576
MAX_PRIMARY_ERROR_MESSAGE_CHARS=4096

def primary_error_message(error):
    """Retain a bounded primary exception message without risking cleanup."""
    try:
        message=str(error)
    except BaseException:
        message=f'<unprintable {type(error).__name__}>'
    return message[:MAX_PRIMARY_ERROR_MESSAGE_CHARS], len(message)>MAX_PRIMARY_ERROR_MESSAGE_CHARS

def capture_child_stderr(stream,path,max_bytes=MAX_CHILD_STDERR_BYTES):
    """Drain one owned child stderr pipe with a byte cap and retain its prefix."""
    if type(max_bytes) is not int or max_bytes<0:
        raise ValueError('stderr capture byte limit must be a nonnegative integer')
    reader=getattr(stream,'buffer',stream)
    read_chunk=getattr(reader,'read1',None)
    if not callable(read_chunk):read_chunk=reader.read
    observed=retained=0
    with open(path,'wb') as output:
        while True:
            chunk=read_chunk(65536)
            if not chunk:break
            if type(chunk) is str:chunk=chunk.encode('utf-8')
            if type(chunk) is not bytes:
                raise TypeError('child stderr reader must return text or bytes')
            observed+=len(chunk)
            keep=chunk[:max(0,max_bytes-retained)]
            if keep:
                output.write(keep);output.flush();retained+=len(keep)
    return {'status':'complete','path':str(path),'bytes_observed':observed,
            'bytes_retained':retained,'truncated':retained<observed,
            'scope':'owned child stderr pipe'}

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
        self.decisions=None;self.source_refreshes=None
        self.raw_stdout_capture=None
    def track(self, process):
        self.process=process
    def set_stage(self, name):
        self.failed_stage=name
    def observe_output(self, events, reader, event_wait, runtime, reader_errors=None):
        self.events=events;self.reader=reader;self.event_wait=event_wait
        self.runtime=runtime
        self.reader_errors=[] if reader_errors is None else reader_errors
    def observe_progress(self, decisions, source_refreshes):
        self.decisions=decisions;self.source_refreshes=source_refreshes
    def observe_raw_stdout(self, capture):
        self.raw_stdout_capture=capture
    def __enter__(self): return self
    def __exit__(self, kind, error, traceback):
        if error is None: return False
        message,message_truncated=primary_error_message(error)
        receipt={'format':'controller-failure-cleanup-v2', 'primary_error_type':kind.__name__,
                 'primary_error_message':message,
                 'primary_error_message_truncated':message_truncated,
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
            stderr=getattr(child,'stderr',None)
            if stderr is not None:
                stderr_path=self.out/'stderr.txt'
                captured,metadata,_worker=bounded(
                    'child_stderr_capture',
                    lambda:capture_child_stderr(stderr,stderr_path),1)
                receipt['stderr_capture']=(metadata if captured else {
                    'status':'incomplete', 'path':str(stderr_path),
                    'scope':'owned child stderr pipe; partial file may be present'})
                if captured and hasattr(stderr,'close'):
                    attempt('child_stderr_close',stderr.close)
            else:
                receipt['stderr_capture']={'status':'unavailable',
                                           'scope':'owned child stderr pipe'}
        bounded('planner_close',lambda:self.planner.close(timeout=1),1)
        attempt('atexit_unregister',lambda:atexit.unregister(self.planner.close))
        receipt['stdout_reader_retired']=False
        if self.reader is not None:
            attempt('stdout_reader_join',lambda:self.reader.join(timeout=5))
            reader_alive=attempt('stdout_reader_alive',self.reader.is_alive)
            if reader_alive:
                receipt['stdout_reader_retired']=not receipt['stages'][-1]['result']
        receipt['stdout_reader_errors']=list(self.reader_errors)
        if self.raw_stdout_capture is not None:
            receipt['raw_stdout_capture']=deepcopy(self.raw_stdout_capture)
        if self.decisions is not None and self.source_refreshes is not None:
            def write_failure_progress():
                events=self.events if type(self.events) is list else []
                payload={
                    'format':'map01-controller-failure-progress-v1',
                    'failed_stage':self.failed_stage,
                    'decision_count':len(self.decisions),
                    'decisions':deepcopy(self.decisions),
                    'source_refreshes':deepcopy(self.source_refreshes),
                    'controller_events':deepcopy(events),
                    'controller_event_capture_scope':(
                        'parent-parsed stdout event objects after controller timing annotations; '
                        'exact child stdout bytes and SHA-256 are in raw_stdout_capture'),
                    'raw_stdout_capture':deepcopy(self.raw_stdout_capture),
                    'event_capture_status':(
                        'complete' if receipt['stdout_reader_retired'] and
                        not receipt['stdout_reader_errors'] else 'incomplete'),
                    'stdout_reader_errors':list(self.reader_errors),
                }
                serialized=(json.dumps(payload,indent=2,allow_nan=False)+'\n').encode('utf-8')
                temporary=self.out/'controller-failure-progress.json.tmp'
                final=self.out/'controller-failure-progress.json'
                with open(temporary,'wb') as output:
                    output.write(serialized)
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(temporary,final)
                return {'path':str(final),'sha256':hashlib.sha256(serialized).hexdigest(),
                        'decision_count':len(self.decisions),
                        'event_count':len(events),
                        'event_capture_status':payload['event_capture_status']}
            progress_written=attempt('failure_progress_write',write_failure_progress)
            if progress_written:
                receipt['diagnostic_progress']=receipt['stages'][-1]['result']
        event_collection_valid=type(self.events) is list
        events=self.events if event_collection_valid else []
        receipt['control_boundary_failures']=[deepcopy(row) for row in events
            if type(row) is dict and row.get('event')=='control_boundary_failed']
        receipt['control_boundary_failed']=bool(receipt['control_boundary_failures'])
        if receipt['control_boundary_failed']:
            receipt['task_effect']='unknown'
        invalid_event_records=sum(
            type(row) is not dict or
            type(row.get('event')) is not str or not row.get('event')
            for row in events)
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
        input_rows=[row for row in events if type(row) is dict and
                    type(row.get('event')) is str and row['event'] in INPUT_RELEASE_EVENTS]
        invalid_input_ids=sum(not (type(row.get('id')) is str and row.get('id'))
                              for row in input_rows)
        orphan_input_ids=sorted({row['id'] for row in input_rows
                                 if type(row.get('id')) is str and row['id']
                                 and row['id'] not in accepted_ids})
        identities_unambiguous=(event_collection_valid and invalid_event_records==0 and
                                not duplicate_accepted_ids and not duplicate_terminal_ids and
                                invalid_accepted_ids==0 and invalid_terminal_ids==0 and
                                invalid_input_ids==0 and not orphan_input_ids and
                                accepted_ids==terminal_ids)
        receipt['orphan_input_event_ids']=orphan_input_ids
        receipt['invalid_input_event_id_count']=invalid_input_ids
        receipt['duplicate_accepted_ids']=duplicate_accepted_ids
        receipt['duplicate_terminal_ids']=duplicate_terminal_ids
        receipt['invalid_event_record_count']=invalid_event_records
        receipt['invalid_accepted_event_id_count']=invalid_accepted_ids
        receipt['invalid_terminal_event_id_count']=invalid_terminal_ids
        receipt['input_event_identities_unambiguous']=identities_unambiguous
        renewal=getattr(error, 'cover_renewal_receipt', None)
        renewal_terminal_bound=renewal_scope_verified=renewal is None
        if type(renewal) is dict:
            receipt['cover_renewal']=deepcopy(renewal)
            receipt['task_effect']='unknown'
            identifier=renewal.get('id')
            token=renewal.get('verified_release_intent_token')
            renewal_terminal_bound=(type(identifier) is str and
                                     identifier in accepted_ids and identifier in terminal_ids)
            renewal_scope_verified=(renewal_terminal_bound and
                renewal.get('input_recovery_required') is False and
                renewal.get('verified_empty_release') is True and
                type(token) is str and bool(token) and any(
                    row.get('id')==identifier and row.get('intent_token')==token for row in accepted_rows) and
                operation_release_verified(identifier, events, require_intent=True))
        event_set_complete=(receipt['stdout_reader_retired'] and
                            not receipt['stdout_reader_errors'])
        receipt['input_terminals_complete']=(event_set_complete and
                                              identities_unambiguous and renewal_terminal_bound)
        receipt['input_releases_verified_empty']=(
            receipt['input_terminals_complete'] and
            not receipt['control_boundary_failed'] and renewal_scope_verified and
            all(operation_release_verified(identifier, events) for identifier in accepted_ids))
        receipt['input_release_verified_empty']=receipt['input_releases_verified_empty']
        if renewal is not None:
            receipt['input_recovery_required']=not receipt['input_releases_verified_empty']
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
                    type(owner_rows[-1]) is dict and
                    owner_rows[-1].get('event')=='owner_release' and
                    owner_rows[-1].get('reason')=='close' and
                    all(owner_event_verified(row) for row in owner_rows))
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
        cycle_hold = getattr(error, 'cycle_budget_receipt', None)
        if type(cycle_hold) is dict:
            receipt['cover_cycle_hold'] = deepcopy(cycle_hold)
        attempt('failure_receipt_write',lambda:(self.out/'controller-failure.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n'))
        return False
