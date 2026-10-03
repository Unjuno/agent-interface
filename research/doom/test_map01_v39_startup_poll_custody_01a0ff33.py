"""Ordinary inert startup poll/primary custody regression; no native or model launch."""
import ast, pathlib, types, subprocess, json, copy, unittest
p=pathlib.Path(__file__).resolve().parent
SOURCE=p/'map01_overlap_controller_v39.py'

heads = {'already-exited': 'P P', 'first-poll-fault': 'P W P P', 'final-poll-fault': 'P P', 'all-polls-fault': 'P W P T W P K W P', 'recovery-after-timeout': 'P W P T W P P', 'all-polls-and-stop-fault': 'P W P T P K P', 'join-fault': 'P P'}
poll_error = "session poll: RuntimeError('own status unavailable')"
errmap = {'first-poll-fault': [poll_error], 'final-poll-fault': [poll_error, 'owned session retirement unconfirmed'], 'all-polls-fault': [poll_error] * 4 + ['owned session retirement unconfirmed'], 'recovery-after-timeout': [poll_error], 'all-polls-and-stop-fault': [poll_error, "wait: OSError('own wait failure')", poll_error, "terminate: OSError('own terminate failure')", poll_error, "kill: OSError('own kill failure')", poll_error, 'owned session retirement unconfirmed'], 'join-fault': ["stdout reader join: RuntimeError('own stdout join failure')", 'stdout reader retirement unconfirmed']}

def poll_trial(source, name):
    module = ast.parse(source)
    chosen = [n for n in module.body if isinstance(n, ast.FunctionDef) and n.name in ['_startup_exception_text', '_close_failed_startup']]
    assert len(chosen) == 2
    calls = []
    errors = []

    def event(label, **extra):
        calls.append(dict(event=label, **extra))

    class Pipe:

        def __init__(self, name):
            self.name = name
            self.closed = False

        def close(self):
            event(self.name + '.close')
            self.closed = True

    class Worker:

        def __init__(self, name):
            self.name = name

        def start(self):
            event(self.name + '.start')

        def join(self, timeout):
            event(self.name + '.join', timeout=timeout)
            if name == 'join-fault' and self.name == 'stdout-reader':
                raise RuntimeError('own stdout join failure')

        def is_alive(self):
            event(self.name + '.is_alive')
            return False

    class Process:

        def __init__(self):
            self.stdin = Pipe('stdin')
            self.stdout = Pipe('stdout')
            self.stderr = Pipe('stderr')
            self.polls = 0
            self.waits = 0

        def poll(self):
            self.polls += 1
            event('process.poll', ordinal=self.polls)
            bad = name == 'first-poll-fault' and self.polls == 1 or (name == 'final-poll-fault' and self.polls == 2) or name in ['all-polls-fault', 'all-polls-and-stop-fault'] or (name == 'recovery-after-timeout' and self.polls == 2)
            if bad:
                raise RuntimeError('own status unavailable')
            return None if name == 'recovery-after-timeout' and self.polls == 1 else 0

        def wait(self, timeout):
            self.waits += 1
            event('process.wait', timeout=timeout, ordinal=self.waits)
            if name == 'all-polls-and-stop-fault':
                raise OSError('own wait failure')
            if name == 'recovery-after-timeout' and self.waits == 1:
                raise subprocess.TimeoutExpired('inert', timeout)
            return 0

        def terminate(self):
            event('process.terminate')
            if name == 'all-polls-and-stop-fault':
                raise OSError('own terminate failure')

        def kill(self):
            event('process.kill')
            if name == 'all-polls-and-stop-fault':
                raise OSError('own kill failure')

    class Planner:

        def close(self, timeout):
            event('planner.close', timeout=timeout)

    def thread(**kwargs):
        assert kwargs['daemon'] is True and callable(kwargs['target'])
        return Worker('stderr-reader')
    ns = dict(threading=types.SimpleNamespace(Thread=thread), subprocess=subprocess, atexit=types.SimpleNamespace(unregister=lambda fn: event('atexit.unregister')))
    exec(compile(ast.fix_missing_locations(ast.Module(body=chosen, type_ignores=[])), 'candidate' + '-selected-helper', 'exec'), ns)
    process = None if name == 'no-process' else Process()
    reader = None if process is None else Worker('stdout-reader')
    planner = Planner()
    receipt = None
    exception = None
    try:
        receipt = ns['_close_failed_startup'](process, reader, planner, p / 'NOT_CREATED')
    except BaseException as exc:
        exception = dict(type=type(exc).__name__, message=str(exc))
    return dict(arm='candidate', case=name, calls=calls, receipt=receipt, exception=exception, pipes=None if process is None else {key: getattr(process, key).closed for key in ['stdin', 'stdout', 'stderr']}, mock_thread_target_executions=0)

def expected_case(name):
    calls = []

    def add(event, **extra):
        calls.append(dict(event=event, **extra))
    exitcode = None if name in ['no-process', 'final-poll-fault', 'all-polls-fault', 'all-polls-and-stop-fault'] else 0
    if name != 'no-process':
        add('stderr-reader.start')
        add('stdin.close')
        polls = waits = 0
        for key in heads[name].split():
            if key == 'P':
                polls += 1
                add('process.poll', ordinal=polls)
            elif key == 'W':
                waits += 1
                add('process.wait', timeout=1, ordinal=waits)
            elif key == 'T':
                add('process.terminate')
            else:
                add('process.kill')
        add('stdout-reader.join', timeout=1)
        if name != 'join-fault':
            add('stdout-reader.is_alive')
        add('stderr-reader.join', timeout=1)
        add('stderr-reader.is_alive')
        if exitcode is not None:
            if name != 'join-fault':
                add('stdout.close')
            add('stderr.close')
    add('planner.close', timeout=1)
    add('atexit.unregister')
    receipt = dict(schema='map01-startup-cleanup-v1', session_exit_code=exitcode, reader_joined=name != 'join-fault', client_closed=True, input_release_verified=False, errors=errmap.get(name, []), escalations=['terminate', 'kill'] if name in ['all-polls-fault', 'all-polls-and-stop-fault'] else ['terminate'] if name == 'recovery-after-timeout' else [], stderr_complete=name == 'no-process', stderr_bytes=0, stderr_reader_joined=True)
    pipes = None if name == 'no-process' else dict(stdin=True, stdout=exitcode is not None and name != 'join-fault', stderr=exitcode is not None)
    return dict(arm='candidate', case=name, calls=calls, receipt=receipt, exception=None, pipes=pipes, mock_thread_target_executions=0)

def custody_trial(source, primary_kind, helper_kind, record_fault):
    tree=ast.parse(source)
    main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    handler=next(h for n in ast.walk(main) if isinstance(n,ast.Try) for h in n.handlers if h.name=='startup_error')
    functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['_startup_exception_text','_startup_exception_details','_note_startup_exception']]
    statement=ast.Try(body=[ast.Raise(exc=ast.Name(id='primary',ctx=ast.Load()))],handlers=[handler],orelse=[],finalbody=[])
    wrapper=ast.FunctionDef(name='selected_handler',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[statement],decorator_list=[])
    code=compile(ast.fix_missing_locations(ast.Module(body=functions+[wrapper],type_ignores=[])),'actual-candidate-handler','exec')
    class BadText(Exception):
     def __str__(self):raise RuntimeError('broken primary str')
     def __repr__(self):raise RuntimeError('broken primary repr')
    events=[];recorded=[]
    primary={'runtime':RuntimeError,'interrupt':KeyboardInterrupt,'bad-text':BadText}[primary_kind]('OWN_PRIMARY')
    secondary=None if helper_kind=='healthy' else (RuntimeError if helper_kind=='exception' else SystemExit)('OWN_CLEANUP_SECONDARY')
    healthy=dict(schema='map01-startup-cleanup-v1',session_exit_code=0,reader_joined=True,client_closed=True,input_release_verified=False,errors=[],escalations=[],stderr_complete=True,stderr_bytes=11,stderr_reader_joined=True)
    def helper(*args):
     assert args==('OWN_PROCESS','OWN_READER','OWN_PLANNER',out)
     events.append('helper.invoke')
     if secondary is not None:raise secondary
     return copy.deepcopy(healthy)
    class Output:
     def __truediv__(self,name):assert name=='startup-cleanup.json';events.append('record.path');return self
     def write_text(self,text):
      events.append('record.write');recorded.append(json.loads(text))
      if record_fault:raise OSError('OWN_RECORD_FAILED')
    out=Output()
    ns=dict(primary=primary,_close_failed_startup=helper,process='OWN_PROCESS',reader_thread='OWN_READER',planner_client='OWN_PLANNER',args=types.SimpleNamespace(out=out),all_events=[dict(event='OWN_STARTUP_EVENT')],json=json)
    exec(code,ns)
    caught=None
    try:ns['selected_handler']()
    except BaseException as exc:caught=exc
    row=dict(primary_kind=primary_kind,helper_kind=helper_kind,record_fault=record_fault,events=events,records=recorded,caught_is_primary=caught is primary,caught_is_secondary=caught is secondary,caught_type=type(caught).__name__,notes=list(getattr(primary,'__notes__',[])),primary_details=ns['_startup_exception_details'](primary))
    return row

def expected(arm, primary_kind, helper_kind, record_fault):
    primary_type = {'runtime': 'RuntimeError', 'interrupt': 'KeyboardInterrupt', 'bad-text': 'BadText'}[primary_kind]
    details = dict(type=primary_type, message='<exception text unavailable>' if primary_kind == 'bad-text' else 'OWN_PRIMARY')
    helper_bad = helper_kind != 'healthy'
    handled = arm == 'candidate' or not helper_bad
    secondary_type = 'RuntimeError' if helper_kind == 'exception' else 'SystemExit'
    notes = []
    if handled:
        if helper_bad:
            payload = dict(schema='map01-startup-cleanup-v1', session_exit_code=None, reader_joined=False, client_closed=False, input_release_verified=False, errors=['startup cleanup helper failed: ' + secondary_type + "('OWN_CLEANUP_SECONDARY')"], escalations=[], stderr_complete=False, stderr_bytes=None, stderr_reader_joined=False, cleanup_error=dict(type=secondary_type, message='OWN_CLEANUP_SECONDARY'))
        else:
            payload = dict(schema='map01-startup-cleanup-v1', session_exit_code=0, reader_joined=True, client_closed=True, input_release_verified=False, errors=[], escalations=[], stderr_complete=True, stderr_bytes=11, stderr_reader_joined=True)
        payload.update(startup_error=details, startup_events=[dict(event='OWN_STARTUP_EVENT')])
        if record_fault:
            notes.append("startup cleanup record failed: OSError('OWN_RECORD_FAILED')")
        if helper_bad:
            notes.append('startup cleanup incomplete; see startup-cleanup.json')
    return dict(primary_kind=primary_kind, helper_kind=helper_kind, record_fault=record_fault, events=['helper.invoke', 'record.path', 'record.write'] if handled else ['helper.invoke'], records=[payload] if handled else [], caught_is_primary=handled, caught_is_secondary=not handled, caught_type=primary_type if handled else secondary_type, notes=notes, primary_details=details)

class StartupPollAndCustodyTests(unittest.TestCase):
    def test_poll_failures_preserve_later_cleanup_and_unknown_status(self):
        source=SOURCE.read_bytes()
        for case in ['no-process','already-exited','first-poll-fault','final-poll-fault','all-polls-fault','recovery-after-timeout','all-polls-and-stop-fault','join-fault']:
            with self.subTest(case=case):
                self.assertEqual(poll_trial(source,case),expected_case(case))
    def test_original_startup_exception_survives_entire_helper_and_record_faults(self):
        source=SOURCE.read_bytes()
        for primary in ['runtime','interrupt','bad-text']:
            for helper in ['healthy','exception','baseexception']:
                for record in [False,True]:
                    with self.subTest(primary=primary,helper=helper,record=record):
                        self.assertEqual(custody_trial(source,primary,helper,record),expected('candidate',primary,helper,record))
if __name__=='__main__':unittest.main()
