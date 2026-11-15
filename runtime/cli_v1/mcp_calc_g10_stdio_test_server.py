"""Production CLI/stdio entrypoint with a process-owned Fake X G10 fixture."""
import sys
import time
import json
from pathlib import Path
from types import SimpleNamespace
from runtime.cli_v1.test_mcp_owned_process import _CALC_TEST_PROCESS_GENERATION


class FakeG10Launch:
    def launch(self, _artifact):
        return {'status':'launched','pid':4400,'start_ticks':123456,
            'input_dispatched':False,'task_success':None,'replay_allowed':False}

    def retain_initial_process_group_custody(self, owner):
        owner._calc_process_group_custody={'fixture':'g10-stdio-parent-custody'}
        return {'status':'retained','custody':dict(owner._calc_process_group_custody),
            'input_dispatched':False,'task_success':None,'replay_allowed':False}

    def discover_owned_window(self, _owner, **_kwargs):
        return {'status':'candidate_found','candidate':{
            'xid':20,'process_pid':4321,'process_start_ticks':98765,
            'process_generation':_CALC_TEST_PROCESS_GENERATION,
            'window_incarnation':'c'*64,'mapped':True},
            'input_dispatched':False,'task_success':None,'replay_allowed':False}

    def review_and_bind_owned_window(self, _owner, window_id, **_kwargs):
        binding={'xid':window_id,'pid':4321,'start_ticks':98765,
            'process_generation':_CALC_TEST_PROCESS_GENERATION,
            'window_generation':'c'*64}
        fresh={'xid':window_id,'process_pid':4321,'process_start_ticks':98765,
            'process_generation':_CALC_TEST_PROCESS_GENERATION,
            'window_incarnation':'c'*64,'mapped':True,
            'focused_before':True,'focused_after':True}
        return {'status':'reviewed','candidate':{'xid':window_id},
            'fresh_metadata':fresh,'binding':binding,'input_dispatched':False,
            'task_success':None,'replay_allowed':False}

    def wait_for_verified_exit(self, *, timeout_s):
        import time
        return {'schema':'agent-interface/calc-target-exit-receipt-v2',
            'status':'exited','verified':True,
            'process_generation':_CALC_TEST_PROCESS_GENERATION,
            'xid':20,'pid':4321,'start_ticks':98765,'exit_code':0,
            'observed_monotonic_ns':time.monotonic_ns(),
            'custody':'libreoffice-oosplash-direct-child-v1',
            'launcher_pid':4400,'launcher_start_ticks':123456,
            'launcher_executable':'/usr/lib/libreoffice/program/oosplash',
            'launcher_package_version':'4:7.4.7-1+deb12u14',
            'launcher_exit_code':0,
            'replacement_observed':False}

    def cleanup_owned_process_group(self, custody):
        return {'status':'terminated','verified_empty':True,
            'clean_exit_verified':False,'custody':custody}

    def close(self):
        return None


def main():
    from runtime.cli_v1 import mcp_server
    from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
    from runtime.cli_v1.test_mcp_owned_process import _fake_owner_factory
    from runtime.cli_v1 import owned_guarded_session

    output=Path(sys.argv[sys.argv.index('--output-directory')+1])
    output.mkdir(parents=True,exist_ok=True)
    for marker in ('calc-profile-mode','g10-stub-compiled',
                   'fake-target-exit-receipt'):
        (output/marker).write_text('enabled',encoding='ascii')
    original_get=OwnedGuardedSessionOwner.get
    def timed_owner_get(owner):
        started=time.monotonic_ns()
        outcome='open'
        try:
            return original_get(owner)
        except BaseException as error:
            outcome=type(error).__name__
            raise
        finally:
            ended=time.monotonic_ns()
            (output/'owner-get-timing.json').write_text(json.dumps({
                'started_monotonic_ns':started,
                'ended_monotonic_ns':ended,
                'elapsed_ns':ended-started,
                'outcome':outcome}),encoding='utf-8')
    OwnedGuardedSessionOwner.get=timed_owner_get
    real_create_server=mcp_server.create_server

    def fake_backed_create_server(targets, output_directory, **options):
        return real_create_server(targets,output_directory,
            _guarded_owner_factory=_fake_owner_factory,
            _calc_launch_factory=lambda _artifact:FakeG10Launch(),**options)

    mcp_server.os=SimpleNamespace(name='posix')
    mcp_server._x11_root_window_id=lambda _display:20
    mcp_server.create_server=fake_backed_create_server
    # The stdio fixture has an extra Windows-spawned parent process. Keep its
    # transport/custody assertions separate from the production 5 s startup
    # budget, which is covered by the direct owner tests.
    owned_guarded_session._STARTUP_TIMEOUT_S=20.0
    mcp_server.main()


if __name__=='__main__':
    main()
