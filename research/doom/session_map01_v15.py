"""MAP01 v15: measurement-only composition around unchanged session v12.

Selects owner-thread release receipts v3 and an isolated same-main-thread scorer using
terminal-locked progress clock v2. Controller policy, command semantics and v12
controller-visible event delivery remain unchanged.
"""
from __future__ import annotations
import hashlib,json,sys,time
from pathlib import Path
from map01_scorer_stdio_adapter_v1 import MainThreadScorerStdin,ScorerFileSink
from independent_progress_clock_v2 import ProgressSample
HERE=Path(__file__).resolve().parent;RESEARCH=HERE.parent

def _option(name,default=None):
    args=sys.argv[1:]
    if name not in args:
        if default is not None:return default
        raise ValueError(f'required option missing: {name}')
    i=args.index(name)
    if i+1>=len(args):raise ValueError(f'option requires value: {name}')
    return args[i+1]
def _sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def _base_session_argv(argv, *, process_identity):
    result=[arg for arg in argv if arg!='--measurement-session']
    if process_identity:
        result=[arg for arg in result if arg not in ('--target-process-identity','--target-window-lifecycle',
            '--owned-input-service','--post-load-clock-gate')]
    return result
def _merge_sources(out, *, process_identity=False, window_lifecycle=False,owned_input_service=False):
    path=Path(out)/'sources.json'
    if not path.exists():return False
    data=json.loads(path.read_text(encoding='utf-8'))
    additions=[HERE/'session_map01_v15.py',HERE/'map01_scorer_stdio_adapter_v1.py',HERE/'main_thread_scorer_polling_v1.py',HERE/'independent_progress_clock_v2.py',HERE/'doom_owner_thread_release_batch_backend_v1.py',HERE/'doom_typed_release_backend_v2.py',RESEARCH/'live_control/executor_v13.py',RESEARCH/'live_control/executor_v12.py',RESEARCH/'live_control/input_transition_owner_v4.py',RESEARCH/'live_control/input_transition_owner_v3.py',RESEARCH/'live_control/input_owner_v12.py',RESEARCH/'live_control/input_owner_v11.py']
    additions.append(HERE/'input_owner_generation_protocol_v1.py')
    additions.append(RESEARCH/'live_control/input_owner_rpc_v2.py')
    if owned_input_service:
        additions.extend([HERE/'session_owned_owner_backend.py',RESEARCH/'live_control/input_owner_service_adapter.py',
            RESEARCH/'live_control/input_owner_cancel_v4.py',
            RESEARCH/'live_control/input_owner_process_v3.py',RESEARCH/'live_control/session_v9.py',
            HERE/'doom_typed_release_backend_v1.py'])
    for source in additions:data[str(source.relative_to(RESEARCH))]=_sha(source)
    if process_identity:
        identity_files = (HERE/'doom_process_identity_backend_v1.py',
                       RESEARCH/'live_control/target_process_identity_v1.py',
                       RESEARCH/'live_control/lease_cause_v1.py',
                       RESEARCH/'live_control/lease_cause_v2.py',
                       RESEARCH/'live_control/lease_release_v1.py')
        for source in identity_files:
            data[str(source.relative_to(RESEARCH))]=_sha(source)
        files = {source.relative_to(RESEARCH.parent).as_posix(): _sha(source)
                 for source in (*additions, *identity_files)}
        for relative in ('runtime/guarded_x11_v1/process_identity.py', 'runtime/guarded_x11_v1/target_queries.py'):
            files[relative]=_sha(RESEARCH.parent/relative)
        (Path(out)/'target-process-identity-sources.json').write_text(json.dumps(
            {'schema':'map01-process-identity-sources-v1','path_root':'repository','files':files,
             'window_lifecycle':window_lifecycle,'owned_input_service':owned_input_service},
            indent=2,sort_keys=True)+'\n',encoding='utf-8')
    path.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n',encoding='utf-8');return True

def _coherent_progress_sample(game,game_variable,timeout_seconds,clock_ns=time.perf_counter_ns,attempts=3):
    """Read scorer state only when all fields are bracketed by one episode tic."""
    if type(attempts) is not int or attempts<1:raise ValueError('attempts must be positive integer')
    for _ in range(attempts):
        tic_before=game.get_episode_time();finished=game.is_episode_finished();dead=game.is_player_dead()
        if type(finished) is not bool or type(dead) is not bool:
            raise ValueError('terminal state is not a boolean')
        raw_kills=game.get_game_variable(game_variable.KILLCOUNT);raw_deaths=game.get_game_variable(game_variable.DEATHCOUNT)
        if any(type(value) not in (int,float) or value<0 or value%1!=0 for value in (raw_kills,raw_deaths)):
            raise ValueError('game counter is invalid')
        kills=int(raw_kills);deaths=int(raw_deaths);ticrate=game.get_ticrate()
        if type(tic_before) is not int or tic_before<0 or type(ticrate) is not int or ticrate<=0:
            raise ValueError('engine clock is invalid')
        timeout_method=getattr(game,'is_episode_timeout_reached',None)
        if callable(timeout_method):
            timeout_reached=timeout_method()
            if type(timeout_reached) is not bool:
                raise ValueError('timeout state is not a boolean')
        else:
            if finished and not dead:
                raise ValueError('terminal timeout is unknown without native evidence')
            timeout_reached=None if finished else tic_before>=timeout_seconds*ticrate
        tic_after=game.get_episode_time()
        if type(tic_after) is not int or tic_after<0:
            raise ValueError('engine clock is invalid')
        if tic_before==tic_after:
            return ProgressSample(clock_ns(),kills,deaths,finished,dead,bool(finished and not dead and not timeout_reached))
    raise RuntimeError('independent scorer could not obtain one-tic coherent sample')

class _GameProxy:
    def __init__(self, inner, final_sample):
        self._inner = inner
        self._final_sample = final_sample
        self.initialized = False
        self.closing = False
        self.closed = False
        self._close_error = None

    def __getattr__(self, name):
        return getattr(self._inner, name)

    def init(self):
        result = self._inner.init()
        self.initialized = True
        return result

    def close(self):
        if self.closing:
            return None
        if self.closed:
            if self._close_error is not None:
                raise self._close_error
            return None

        # Preserve a controller error already unwinding through the session's
        # finally block if either scorer sampling or game cleanup also fails.
        active_error = sys.exception()
        self.closing = True
        sample_error = None
        game_close_error = None
        result = None
        if self.initialized:
            try:
                # sample_game() requires the proxy to remain initialized/open.
                self._final_sample()
            except BaseException as error:
                sample_error = error

        self.closed = True
        try:
            result = self._inner.close()
        except BaseException as error:
            game_close_error = error
            self._close_error = error
        finally:
            self.closing = False

        cleanup_errors = [error for error in (sample_error, game_close_error)
                          if error is not None]
        if cleanup_errors and active_error is not None:
            self._close_error = BaseExceptionGroup(
                "session and game-close cleanup failed",
                [active_error, *cleanup_errors],
            )
            raise self._close_error
        if len(cleanup_errors) == 1:
            self._close_error = cleanup_errors[0]
            raise self._close_error
        if len(cleanup_errors) > 1:
            self._close_error = BaseExceptionGroup(
                "final scorer sample and game close both failed", cleanup_errors)
            raise self._close_error
        return result

def validate_door_runtime_options(argv):
    reverse_flag='--door-task-reverse-arm'
    reverse_options=[item for item in argv if item.split('=',1)[0]==reverse_flag]
    for item in argv:
        name=item.split('=',1)[0]
        if name.startswith('--') and name!=reverse_flag and reverse_flag.startswith(name):
            raise ValueError('reverse option must be spelled in full')
    if reverse_options and (reverse_options != [reverse_flag] or argv.count('--door-task-arm')!=1 or argv.count('--door-task-traverse')!=1):
        raise ValueError('reverse option requires one explicit door/traverse mode')
    door_flags=[item for item in argv if item=='--door-task-arm' or item.startswith('--door-task-arm=')]
    if not door_flags:
        return
    required=('--target-process-identity','--owned-input-service',
              '--renewal-passive-observer','--post-load-clock-gate')
    if (door_flags!=['--door-task-arm'] or any(argv.count(flag)!=1 for flag in required)
            or '--target-window-lifecycle' in argv):
        raise ValueError('door trial requires owned process identity, observer and clock gate')


def validate_synthetic_runtime_options(argv):
    flags=('--synthetic-exit-pwad','--synthetic-exit-arm','--synthetic-exit-refresh')
    for item in argv:
        name=item.split('=',1)[0]
        if name.startswith('--') and name not in flags and any(flag.startswith(name) for flag in flags):
            raise ValueError('synthetic options must be spelled in full')
    synthetic=[item for item in argv if any(item.startswith(flag) for flag in flags)]
    if not synthetic:return
    required=('--target-process-identity','--owned-input-service','--renewal-passive-observer')
    if (synthetic not in (['--synthetic-exit-pwad','--synthetic-exit-arm'], ['--synthetic-exit-pwad','--synthetic-exit-arm','--synthetic-exit-refresh'])
            or any(argv.count(flag)!=1 for flag in required)
            or '--post-load-clock-gate' in argv or '--target-window-lifecycle' in argv
            or any(item.startswith('--door-task-') for item in argv)):
        raise ValueError('synthetic calibration requires owned target and observer without fixture modes')


def validate_candidate_runtime_options(argv):
    names = ('--candidate-setup-evidence', '--candidate-setup-evidence-sha256')
    if any(item.startswith('--candidate-setup-') and
           item.split('=', 1)[0] not in names for item in argv):
        raise ValueError('candidate proof options must use their full registered spelling')
    present = [name for name in names if any(item == name or item.startswith(name + '=') for item in argv)]
    if not present:
        return
    if (present != list(names)
            or any(sum(item == name or item.startswith(name + '=') for item in argv) != 1 for name in names)
            ):
        raise ValueError('candidate proof requires one evidence path and one pinned hash')
    required = ('--measurement-session', '--target-process-identity', '--owned-input-service',
                '--post-load-clock-gate', '--renewal-passive-observer')
    def option_value(name):
        matches = [index for index, item in enumerate(argv)
                   if item == name or item.startswith(name + '=')]
        if len(matches) != 1:
            return None
        index = matches[0]
        if argv[index] != name:
            return argv[index].split('=', 1)[1]
        return argv[index + 1] if index + 1 < len(argv) else None
    if (any(argv.count(flag) != 1 for flag in required)
            or '--target-window-lifecycle' in argv
            or option_value('--seed') != '990619'
            or option_value('--timeout-seconds') != '75'):
        raise ValueError('candidate task load requires measured owner, clock and pinned episode gates')


def main():
    validate_synthetic_runtime_options(sys.argv[1:])
    validate_door_runtime_options(sys.argv[1:])
    validate_candidate_runtime_options(sys.argv[1:])
    owned_input_service='--owned-input-service' in sys.argv[1:]
    process_identity='--target-process-identity' in sys.argv[1:]
    window_lifecycle = '--target-window-lifecycle' in sys.argv[1:]
    clock_gate_requested = "--post-load-clock-gate" in sys.argv[1:]
    if '--fresh-neutral-fixture-setup' in sys.argv[1:] and (clock_gate_requested or not owned_input_service or not process_identity or '--renewal-passive-observer' not in sys.argv[1:]):
        raise ValueError('fresh neutral setup requires process identity, owned service and observer without post-load gate')
    if clock_gate_requested and not owned_input_service:
        raise ValueError("post-load clock gate requires the owned input service")
    if owned_input_service and (not process_identity or window_lifecycle):
        raise ValueError('owned input service requires process identity without window lifecycle')
    if window_lifecycle and '--target-process-identity' not in sys.argv[1:]:
        raise ValueError('target window lifecycle requires target process identity')
    out=Path(_option('--out'));timeout_seconds=int(_option('--timeout-seconds','600'))
    if timeout_seconds<10:raise ValueError('timeout must leave scoring slack')
    post_load_gate = None
    if clock_gate_requested:
        from map01_post_load_gate_v1 import PostLoadGate
        post_load_gate = PostLoadGate(out, timeout_seconds)
    import session_map01_v12 as base
    from executor_v13 import Executor as ReleaseOrderedExecutor
    from doom_owner_thread_release_batch_backend_v1 import Backend as TelemetryBackend
    if process_identity:
        from doom_process_identity_backend_v1 import Backend as TelemetryBackend
        if window_lifecycle:
            from functools import partial
            TelemetryBackend = partial(TelemetryBackend, window_lifecycle=True)
    if owned_input_service:
        from session_owned_owner_backend import Backend as TelemetryBackend
    if "--renewal-passive-observer" in sys.argv[1:]:
        if not process_identity:
            raise ValueError("passive renewal requires target process identity")
        from functools import partial
        TelemetryBackend = partial(TelemetryBackend, renewal_passive_observer=True)
    holder={};sink=ScorerFileSink(out)
    def sample_game():
        game=holder.get('game')
        if game is None or not game.initialized or game.closed:raise RuntimeError('scorer sampled outside initialized game lifetime')
        return _coherent_progress_sample(game,base.vd.GameVariable,timeout_seconds)
    def final_sample():sink.direct(sample_game(),time.perf_counter_ns)
    original_ctor=base.vd.DoomGame;original_stdin=sys.stdin;polling=MainThreadScorerStdin(original_stdin,sample_game,sink,sample_hz=35.0)
    def ctor(*args,**kwargs):
        proxy=_GameProxy(original_ctor(*args,**kwargs),final_sample);holder['game']=proxy;return proxy
    base.vd.DoomGame=ctor;base.Backend=TelemetryBackend;base.Executor=ReleaseOrderedExecutor;base.sys.stdin=polling
    original_argv = sys.argv
    # The marker selects this wrapper in the parent caller and is consumed by
    # V15's candidate gate above; V12's legacy parser must not receive it.
    sys.argv = _base_session_argv(original_argv,process_identity=process_identity)
    try:
        if post_load_gate is None:
            base.main()
        else:
            base.main(post_load_gate=post_load_gate)
    finally:
        sys.argv = original_argv
        base.vd.DoomGame=original_ctor;base.sys.stdin=original_stdin
        from input_owner_rpc_v2 import _run_cleanups
        _run_cleanups(lambda:sink.finalize(polling.stats()),
            lambda:_merge_sources(out,process_identity=process_identity,window_lifecycle=window_lifecycle,owned_input_service=owned_input_service))
if __name__=='__main__':main()
