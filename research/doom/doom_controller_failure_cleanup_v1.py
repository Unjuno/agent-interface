"""Best-effort owned cleanup preserving the controller's primary failure."""
import atexit,json,threading

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
                def finish():
                    child.stdin.write('{"op":"finish"}\n');child.stdin.flush()
                finish_sent,_,finish_thread=bounded('finish_send',finish,self.finish_timeout)
                if finish_sent and self.event_wait is not None:
                    attempt('post_control_score_wait',lambda:self.event_wait(
                        lambda row: type(row) is dict and
                        row.get('event')=='post_control_score',10))
                wait_timeout=(self.child_wait_timeout if finish_sent else
                              min(self.child_wait_timeout,self.finish_timeout))
                if not attempt('child_wait',lambda:child.wait(timeout=wait_timeout)):
                    attempt('child_terminate',child.terminate)
                    if not attempt('terminated_wait',lambda:child.wait(timeout=self.escalation_wait_timeout)):
                        attempt('child_kill',child.kill)
                        attempt('killed_wait',lambda:child.wait(timeout=self.escalation_wait_timeout))
                if finish_thread is not None:
                    attempt('finish_sender_join',lambda:finish_thread.join(timeout=1))
                    sender_alive=attempt('finish_sender_alive',finish_thread.is_alive)
                    if not sender_alive:
                        receipt['stages'].append({'stage':'finish_sender_retired',
                                                  'status':'unknown'})
                    elif receipt['stages'][-1]['result']:
                        receipt['stages'].append({'stage':'finish_sender_retired',
                                                  'status':'timed_out'})
                    else:
                        receipt['stages'].append({'stage':'finish_sender_retired',
                                                  'status':'returned'})
                if hasattr(child.stdin,'close'):
                    bounded('child_stdin_close',child.stdin.close,.5)
            if attempt('child_poll_after',child.poll):
                receipt['child_exit_code']=receipt['stages'][-1]['result']
        if attempt('planner_close',lambda:self.planner.close(timeout=1)):
            attempt('atexit_unregister',lambda:atexit.unregister(self.planner.close))
        receipt['stdout_reader_retired']=False
        if self.reader is not None:
            attempt('stdout_reader_join',lambda:self.reader.join(timeout=5))
            reader_alive=attempt('stdout_reader_alive',self.reader.is_alive)
            if reader_alive:
                receipt['stdout_reader_retired']=not receipt['stages'][-1]['result']
        receipt['stdout_reader_errors']=list(self.reader_errors)
        events=self.events if type(self.events) is list else []
        accepted_ids={row.get('id') for row in events if type(row) is dict and
                      row.get('event')=='accepted' and type(row.get('id')) is str}
        terminal_by_id={row.get('id'):row for row in events if type(row) is dict and
                        row.get('event')=='terminal' and type(row.get('id')) is str}
        event_set_complete=(receipt['stdout_reader_retired'] and
                            not receipt['stdout_reader_errors'])
        receipt['input_terminals_complete']=(event_set_complete and
                                              accepted_ids.issubset(terminal_by_id))
        receipt['input_releases_verified_empty']=(
            receipt['input_terminals_complete'] and all(
                type(terminal_by_id[identifier].get('release')) is dict and
                terminal_by_id[identifier]['release'].get('verified') is True and
                terminal_by_id[identifier]['release'].get('keys_down')==[] and
                terminal_by_id[identifier]['release'].get('buttons_down')==[]
            for identifier in accepted_ids))
        receipt['input_release_verified_empty']=receipt['input_releases_verified_empty']
        receipt['scorer_terminal_observed']=any(
            type(row) is dict and row.get('event')=='post_control_score' for row in events)
        score_path=None if self.runtime is None else self.runtime/'score.json'
        owner_path=None if self.runtime is None else self.runtime/'owner-events.json'
        receipt['score_file_present']=score_path is not None and score_path.is_file()
        receipt['owner_events_present']=owner_path is not None and owner_path.is_file()
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
