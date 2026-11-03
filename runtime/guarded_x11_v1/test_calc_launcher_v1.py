"""Parent-held Calc launch custody tests; subprocess is an inert fake."""
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from runtime.guarded_x11_v1.calc_launcher_v1 import CalcLaunchSupervisor
from runtime.guarded_x11_v1.calc_task_artifact_v1 import CalcTaskArtifact
from runtime.guarded_x11_v1.process_identity import process_generation_from_identity


PID, START_TICKS, XID = 4321, 998877, 2200
GENERATION = process_generation_from_identity(XID, PID, START_TICKS)
GUI_PID, GUI_START_TICKS, GUI_XID = 8765, 112233, 2300
GUI_GENERATION = process_generation_from_identity(
    GUI_XID, GUI_PID, GUI_START_TICKS)


class _Process:
    pid = PID

    def __init__(self, returncode=0, timeout=False):
        self.returncode = returncode
        self.timeout = timeout
        self.wait_calls = []
        self.reaped = False

    def poll(self):
        return self.returncode if self.reaped else None

    def wait(self, timeout):
        self.wait_calls.append(timeout)
        if self.timeout:
            raise subprocess.TimeoutExpired('calc', timeout)
        self.reaped = True
        return self.returncode


class _Factory:
    def __init__(self, *, returncode=0, timeout=False):
        self.process = _Process(returncode=returncode, timeout=timeout)
        self.calls = []

    def __call__(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        return self.process


class CalcLaunchSupervisorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.executable = Path(sys.executable).resolve()
        self.factory = _Factory()
        self.supervisor = CalcLaunchSupervisor(self.executable,
            popen_factory=self.factory,
            start_ticks_reader=lambda pid: START_TICKS,
            cmdline_reader=lambda pid: tuple(self.supervisor.argv),
            clock=lambda: 123456789)
        self.call_id = '1' * 32
        (self.root / self.call_id).mkdir()
        self.artifact = CalcTaskArtifact(self.root / self.call_id,
            call_id=self.call_id, attempt_id='launch-test-01')

    def tearDown(self):
        self.supervisor.close()
        self.temp.cleanup()

    def _launch_and_bind(self):
        result = self.supervisor.launch(self.artifact)
        self.assertEqual(result['status'], 'launched')
        metadata = {'xid':XID,'process_pid':PID,
            'process_start_ticks':START_TICKS,
            'process_generation':GENERATION,'window_incarnation':'a'*64,
            'mapped':True,'focused_before':True,'focused_after':True}
        self.supervisor.bind_xres_target(metadata)
        return result

    def _make_oosplash_owner(self, artifact, *, replacement=False):
        factory = _Factory()
        ticks = [0.0]
        state = {'replacement':replacement}
        def children(pid):
            if factory.process.reaped:
                return ()
            return (GUI_PID + 1,) if state['replacement'] else (GUI_PID,)
        def process_ticks(pid):
            if pid == PID:
                return START_TICKS
            if pid == GUI_PID and factory.process.reaped:
                raise OSError('GUI child exited')
            if pid == GUI_PID:
                return GUI_START_TICKS
            raise OSError('unknown process')
        owner = CalcLaunchSupervisor(self.executable,
            popen_factory=factory,
            start_ticks_reader=process_ticks,
            cmdline_reader=lambda pid: (str(self.executable),
                f'-env:UserInstallation={owner._profile_dir.as_uri()}',
                '--calc', str(artifact.path), '--nologo', '--nodefault',
                '--nofirststartwizard', '--norestore'),
            clock=lambda: 123456789,
            custody_mode='libreoffice-oosplash-child',
            gui_executable=self.executable,
            oosplash_executable=self.executable,
            package_version_reader=lambda:'4:7.4.7-1+deb12u14',
            parent_pid_reader=lambda pid:PID,
            executable_reader=lambda pid:str(self.executable),
            direct_children_reader=children,
            monotonic=lambda:ticks[0],
            sleep=lambda seconds:(ticks.__setitem__(0,ticks[0]+seconds),
                setattr(factory.process,'reaped',True)))
        return owner,factory

    def test_launch_uses_only_reserved_document_unique_profile_and_direct_child(self):
        result = self.supervisor.launch(self.artifact)
        argv, options = self.factory.calls[0]
        self.assertEqual(argv[0], str(self.executable))
        self.assertIn('--calc', argv)
        self.assertIn(str(self.artifact.path), argv)
        profile_arg = next(value for value in argv
                           if value.startswith('-env:UserInstallation='))
        self.assertEqual(profile_arg,
            '-env:UserInstallation=' +
            (self.artifact.call_root / 'calc-launch-profile').as_uri())
        self.assertTrue((self.artifact.call_root / 'calc-launch.log').is_file())
        self.assertTrue(options['shell'] is False)
        self.assertTrue(options['close_fds'])
        self.assertTrue(options['start_new_session'])
        self.assertEqual(result['pid'], PID)
        self.assertEqual(result['start_ticks'], START_TICKS)
        self.assertFalse(result['input_dispatched'])
        self.assertIsNone(result['task_success'])
        with self.assertRaisesRegex(RuntimeError, 'one-shot'):
            self.supervisor.launch(self.artifact)
        self.assertEqual(len(self.factory.calls), 1)

    def test_unbound_or_wrong_xres_target_cannot_create_exit_receipt(self):
        self.supervisor.launch(self.artifact)
        unbound = self.supervisor.wait_for_verified_exit(timeout_s=1)
        self.assertEqual(unbound['reason'], 'exact_calc_target_not_bound')
        wrong = {'xid':XID,'process_pid':PID+1,
            'process_start_ticks':START_TICKS,
            'process_generation':process_generation_from_identity(
                XID,PID+1,START_TICKS),'window_incarnation':'a'*64,
            'mapped':True,'focused_before':True,'focused_after':True}
        with self.assertRaisesRegex(ValueError, 'not this live Calc'):
            self.supervisor.bind_xres_target(wrong)

    def test_command_line_must_name_reserved_artifact_and_profile(self):
        supervisor = CalcLaunchSupervisor(self.executable,
            popen_factory=self.factory,
            start_ticks_reader=lambda pid: START_TICKS,
            cmdline_reader=lambda pid: (str(self.executable), '--calc', '/other.fods'))
        try:
            supervisor.launch(self.artifact)
            metadata = {'xid':XID,'process_pid':PID,
                'process_start_ticks':START_TICKS,
                'process_generation':GENERATION,'window_incarnation':'a'*64,
                'mapped':True,'focused_before':True,'focused_after':True}
            with self.assertRaisesRegex(ValueError, 'command line'):
                supervisor.bind_xres_target(metadata)
        finally:
            supervisor.close()

    def test_clean_exact_child_exit_emits_verifier_shaped_receipt_once(self):
        self._launch_and_bind()
        receipt = self.supervisor.wait_for_verified_exit(timeout_s=4)
        self.assertEqual(receipt, {
            'schema':'agent-interface/calc-target-exit-receipt-v1',
            'status':'exited','verified':True,
            'process_generation':GENERATION,'xid':XID,'pid':PID,
            'start_ticks':START_TICKS,'exit_code':0,
            'observed_monotonic_ns':123456789})
        self.assertEqual(self.supervisor.wait_for_verified_exit(timeout_s=4), receipt)
        self.assertEqual(self.factory.process.wait_calls, [4])

    def test_oosplash_custody_separates_launcher_and_gui_exit_identities(self):
        call_id = '2' * 32
        (self.root / call_id).mkdir()
        artifact = CalcTaskArtifact(self.root / call_id, call_id=call_id,
            attempt_id='wrapped-launch-test')
        owner,factory = self._make_oosplash_owner(artifact)
        self.supervisor = owner
        owner.launch(artifact)
        metadata = {'xid':GUI_XID,'process_pid':GUI_PID,
            'process_start_ticks':GUI_START_TICKS,
            'process_generation':GUI_GENERATION,'window_incarnation':'c'*64,
            'mapped':True,'focused_before':True,'focused_after':True}
        bound=owner.bind_xres_target(metadata)
        receipt=owner.wait_for_verified_exit(timeout_s=4)
        self.assertEqual(bound['pid'],GUI_PID)
        self.assertEqual(bound['launcher_pid'],PID)
        self.assertEqual(receipt['schema'],
            'agent-interface/calc-target-exit-receipt-v2')
        self.assertEqual(receipt['pid'],GUI_PID)
        self.assertEqual(receipt['launcher_pid'],PID)
        self.assertEqual(receipt['launcher_exit_code'],0)
        self.assertFalse(receipt['replacement_observed'])
        self.assertEqual(factory.process.wait_calls,[0])

    def test_current_oosplash_gui_child_validation_is_read_only(self):
        call_id='5'*32
        (self.root/call_id).mkdir()
        artifact=CalcTaskArtifact(self.root/call_id,call_id=call_id,
            attempt_id='wrapped-child-inspection')
        owner,factory=self._make_oosplash_owner(artifact)
        self.supervisor=owner
        owner.launch(artifact)
        child=owner.validate_current_gui_child()
        self.assertEqual(child['pid'],GUI_PID)
        self.assertEqual(child['start_ticks'],GUI_START_TICKS)
        self.assertEqual(child['parent_pid'],PID)
        self.assertEqual(child['expected_argv'][0],str(self.executable))
        self.assertFalse(child['authority_granted'])
        self.assertFalse(child['input_dispatched'])
        self.assertIsNone(child['task_success'])
        self.assertFalse(child['replay_allowed'])
        self.assertIsNone(owner._target_identity)
        self.assertEqual(factory.process.wait_calls,[])

    def test_owned_process_group_synchronization_retains_then_advances_child(self):
        call_id='6'*32
        (self.root/call_id).mkdir()
        artifact=CalcTaskArtifact(self.root/call_id,call_id=call_id,
            attempt_id='wrapped-custody-handoff')
        owner,factory=self._make_oosplash_owner(artifact)
        self.supervisor=owner
        owner.launch(artifact)
        class ParentOwner:
            _calc_process_group_custody=None
            def retain_calc_process_group_custody(self,custody):
                self._calc_process_group_custody=custody
                return custody
            def advance_calc_process_group_custody(self,**kwargs):
                self.advance_kwargs=kwargs
                previous=self._calc_process_group_custody
                advanced={**previous,'target':{'pid':GUI_PID+1,
                    'start_ticks':GUI_START_TICKS+1},
                    'expected_members':{str(PID):START_TICKS,
                        str(GUI_PID+1):GUI_START_TICKS+1}}
                self._calc_process_group_custody=advanced
                return {'custody':advanced,'transition':{
                    'previous_target':previous['target'],'target':advanced['target']}}
        parent=ParentOwner()
        first_rows=[{'pid':PID,'start_ticks':START_TICKS,
                'process_group':PID,'session_id':PID,'parent_pid':1},
            {'pid':GUI_PID,'start_ticks':GUI_START_TICKS,
                'process_group':PID,'session_id':PID,'parent_pid':PID}]
        with patch('runtime.guarded_x11_v1.calc_process_group_v1.read_linux_process_group',
                   return_value=first_rows):
            retained=owner.synchronize_owned_process_group(parent)
            unchanged=owner.synchronize_owned_process_group(parent)
        self.assertEqual(retained['status'],'retained')
        self.assertEqual(unchanged['status'],'unchanged')
        self.assertEqual(parent._calc_process_group_custody['target']['pid'],GUI_PID)

        replacement=GUI_PID+1
        owner._direct_children_reader=lambda _pid:(replacement,)
        owner._start_ticks_reader=lambda pid:(START_TICKS if pid==PID
            else GUI_START_TICKS+1)
        owner._cmdline_reader=lambda _pid:(str(self.executable),
            f'-env:UserInstallation={owner._profile_dir.as_uri()}',
            '--calc',str(artifact.path),'--nologo','--nodefault',
            '--nofirststartwizard','--norestore')
        owner._parent_pid_reader=lambda _pid:PID
        owner._executable_reader=lambda _pid:str(self.executable)
        replacement_rows=[{'pid':PID,'start_ticks':START_TICKS,
                'process_group':PID,'session_id':PID,'parent_pid':1},
            {'pid':replacement,'start_ticks':GUI_START_TICKS+1,
                'process_group':PID,'session_id':PID,'parent_pid':PID}]
        with patch('runtime.guarded_x11_v1.calc_process_group_v1.read_linux_process_group',
                   return_value=replacement_rows):
            advanced=owner.synchronize_owned_process_group(parent)
        self.assertEqual(advanced['status'],'advanced')
        self.assertEqual(parent.advance_kwargs['target_pid'],replacement)
        self.assertEqual(parent.advance_kwargs['target_start_ticks'],GUI_START_TICKS+1)
        self.assertEqual(parent.advance_kwargs['expected_argv'][0],str(self.executable))
        self.assertFalse(advanced['authority_granted'])
        self.assertFalse(advanced['input_dispatched'])
        self.assertIsNone(advanced['task_success'])
        self.assertFalse(advanced['replay_allowed'])
        self.assertEqual(factory.process.wait_calls,[])

    def test_owned_group_cleanup_reaps_only_the_retained_launcher_after_signal(self):
        self.supervisor.launch(self.artifact)
        custody={'pgid':PID,'session_id':PID}
        def exercise(receipt,killpg):
            killpg(PID,15)
            return receipt
        receipt={'status':'unknown','verified_empty':False,
            'clean_exit_verified':False,'task_success':None,'replay_allowed':False}
        with (patch('runtime.guarded_x11_v1.calc_process_group_v1.cleanup_process_group',
                    side_effect=lambda value,killpg:exercise(receipt,killpg)),
              patch('runtime.guarded_x11_v1.calc_launcher_v1.os.killpg',
                    create=True) as killpg):
            result=self.supervisor.cleanup_owned_process_group(custody)
        self.assertEqual(result,receipt)
        killpg.assert_called_once_with(PID,15)
        self.assertEqual(self.factory.process.wait_calls,[0.25])
        with patch('runtime.guarded_x11_v1.calc_launcher_v1.os.killpg',
                   create=True) as wrong_group:
            with self.assertRaisesRegex(ValueError,'another launch group'):
                self.supervisor.cleanup_owned_process_group(
                    {'pgid':PID+1,'session_id':PID+1})
        wrong_group.assert_not_called()

    def test_oosplash_replacement_child_stays_unknown(self):
        call_id = '3' * 32
        (self.root / call_id).mkdir()
        artifact = CalcTaskArtifact(self.root / call_id, call_id=call_id,
            attempt_id='wrapped-replacement-test')
        owner,factory = self._make_oosplash_owner(artifact,replacement=True)
        self.supervisor = owner
        owner.launch(artifact)
        self.assertEqual(factory.calls[0][1]['env']['SAL_USE_VCLPLUGIN'],'gen')
        metadata = {'xid':GUI_XID,'process_pid':GUI_PID,
            'process_start_ticks':GUI_START_TICKS,
            'process_generation':GUI_GENERATION,'window_incarnation':'c'*64,
            'mapped':True,'focused_before':True,'focused_after':True}
        owner._direct_children_reader = lambda pid:(GUI_PID,)
        owner.bind_xres_target(metadata)
        owner._direct_children_reader = lambda pid:(GUI_PID+1,)
        receipt=owner.wait_for_verified_exit(timeout_s=4)
        self.assertEqual(receipt['status'],'unknown',receipt)
        self.assertEqual(receipt['reason'],'calc_gui_child_replaced',receipt)
        self.assertNotIn('verified',receipt)
        self.assertFalse(factory.process.wait_calls)

    def test_oosplash_launcher_records_generic_vcl_backend(self):
        owner,factory=self._make_oosplash_owner(self.artifact)
        try:
            receipt=owner.launch(self.artifact)
            self.assertEqual(factory.calls[0][1]['env']['SAL_USE_VCLPLUGIN'],'gen')
            self.assertEqual(receipt['environment_overrides'],
                {'SAL_USE_VCLPLUGIN':'gen'})
        finally:
            owner.close()

    def test_timeout_and_nonzero_exit_remain_unknown(self):
        timeout_factory = _Factory(returncode=None, timeout=True)
        timeout_owner = CalcLaunchSupervisor(self.executable,
            popen_factory=timeout_factory,
            start_ticks_reader=lambda pid: START_TICKS,
            cmdline_reader=lambda pid: tuple(timeout_owner.argv))
        try:
            timeout_owner.launch(self.artifact)
            metadata = {'xid':XID,'process_pid':PID,
                'process_start_ticks':START_TICKS,
                'process_generation':GENERATION,'window_incarnation':'a'*64,
                'mapped':True,'focused_before':True,'focused_after':True}
            timeout_owner.bind_xres_target(metadata)
            result = timeout_owner.wait_for_verified_exit(timeout_s=2)
            self.assertEqual(result['reason'], 'calc_target_exit_timeout')
            self.assertNotIn('verified', result)
        finally:
            timeout_owner.close()

        self.artifact.call_root.joinpath('calc-launch-profile').rmdir()
        self.artifact.call_root.joinpath('calc-launch.log').unlink()
        nonzero_factory = _Factory(returncode=255)
        nonzero_owner = CalcLaunchSupervisor(self.executable,
            popen_factory=nonzero_factory,
            start_ticks_reader=lambda pid: START_TICKS,
            cmdline_reader=lambda pid: tuple(nonzero_owner.argv))
        try:
            nonzero_owner.launch(self.artifact)
            metadata = {'xid':XID,'process_pid':PID,
                'process_start_ticks':START_TICKS,
                'process_generation':GENERATION,'window_incarnation':'a'*64,
                'mapped':True,'focused_before':True,'focused_after':True}
            nonzero_owner.bind_xres_target(metadata)
            result = nonzero_owner.wait_for_verified_exit(timeout_s=2)
            self.assertEqual(result['reason'], 'calc_target_nonzero_exit')
            self.assertEqual(result['exit_code'], 255)
            self.assertNotIn('verified', result)
        finally:
            nonzero_owner.close()

    def test_modified_reserved_artifact_is_refused_before_spawn(self):
        self.artifact.path.write_bytes(b'modified')
        with self.assertRaisesRegex(ValueError, 'original blank file'):
            self.supervisor.launch(self.artifact)
        self.assertFalse(self.factory.calls)
        with self.assertRaisesRegex(RuntimeError, 'one-shot'):
            self.supervisor.launch(self.artifact)

    def test_receipt_cannot_be_minted_for_wrong_start_ticks_or_generation(self):
        self.supervisor.launch(self.artifact)
        wrong = {'xid':XID,'process_pid':PID,
            'process_start_ticks':START_TICKS+1,
            'process_generation':process_generation_from_identity(
                XID,PID,START_TICKS+1),'window_incarnation':'a'*64,
            'mapped':True,'focused_before':True,'focused_after':True}
        with self.assertRaisesRegex(ValueError, 'not this live Calc'):
            self.supervisor.bind_xres_target(wrong)

    def test_owned_window_discovery_retains_custody_before_read_only_query(self):
        child={'pid':GUI_PID,'start_ticks':GUI_START_TICKS,
            'executable':str(self.executable),'authority_granted':False,
            'input_dispatched':False,'task_success':None,'replay_allowed':False}
        custody={'schema':'agent-interface/calc-process-group-custody-v1',
            'pgid':PID,'session_id':PID,
            'launcher':{'pid':PID,'start_ticks':START_TICKS},
            'target':{'pid':GUI_PID,'start_ticks':GUI_START_TICKS}}
        candidate={'xid':GUI_XID,'process_pid':GUI_PID,
            'process_start_ticks':GUI_START_TICKS,
            'process_generation':GUI_GENERATION,
            'window_incarnation':'b'*64,'mapped':True,
            'focused_before':True,'focused_after':True}
        class Owner:
            _calc_process_group_custody=custody
            def __init__(self): self.events=[]
            def get(self): self.events.append('owner_opened')
            def windows_for_process(self,pid,title_hint):
                self.events.append(('query',pid,title_hint))
                return {'status':'discovered','windows':[candidate],
                    'input_dispatched':False,'authority_granted':False}
        owner=Owner()
        self.supervisor._process=_Process()
        self.supervisor._pid=PID
        self.supervisor._custody_mode='libreoffice-oosplash-child'
        with patch.object(self.supervisor,'synchronize_owned_process_group',
                          return_value={'status':'retained','child':child,
                              'custody':custody,'authority_granted':False,
                              'input_dispatched':False}) as synchronize:
            result=self.supervisor.discover_owned_window(owner,
                title_hint='task-artifact.fods')
        self.assertEqual(result['status'],'candidate_found',result)
        self.assertEqual(result['candidate'],candidate)
        self.assertEqual(result['custody'],custody)
        self.assertEqual(owner.events,['owner_opened',
            ('query',GUI_PID,'task-artifact.fods')])
        synchronize.assert_called_once_with(owner)
        self.assertEqual(owner._calc_process_group_cleanup_target,
                         self.supervisor.cleanup_owned_process_group)
        self.assertFalse(result['authority_granted'])
        self.assertFalse(result['input_dispatched'])
        self.assertIsNone(result['task_success'])
        self.assertFalse(result['replay_allowed'])

    def test_owned_window_discovery_stops_on_ambiguous_mapped_windows(self):
        child={'pid':GUI_PID,'start_ticks':GUI_START_TICKS}
        custody={'schema':'agent-interface/calc-process-group-custody-v1',
            'pgid':PID,'session_id':PID,
            'launcher':{'pid':PID,'start_ticks':START_TICKS},
            'target':{'pid':GUI_PID,'start_ticks':GUI_START_TICKS}}
        rows=[{'xid':GUI_XID,'process_pid':GUI_PID,
            'process_start_ticks':GUI_START_TICKS,'mapped':True},
            {'xid':GUI_XID+1,'process_pid':GUI_PID,
            'process_start_ticks':GUI_START_TICKS,'mapped':True}]
        class Owner:
            _calc_process_group_custody=custody
            def get(self): pass
            def windows_for_process(self,pid,title_hint):
                return {'status':'discovered','windows':rows}
        self.supervisor._process=_Process()
        self.supervisor._pid=PID
        self.supervisor._custody_mode='libreoffice-oosplash-child'
        with patch.object(self.supervisor,'synchronize_owned_process_group',
                          return_value={'status':'retained','child':child,
                              'custody':custody}):
            result=self.supervisor.discover_owned_window(Owner(),
                title_hint='task-artifact.fods')
        self.assertEqual(result['status'],'ambiguous',result)
        self.assertEqual(result['reason'],'multiple_mapped_calc_windows')
        self.assertEqual(len(result['candidates']),2)
        self.assertFalse(result['authority_granted'])
        self.assertFalse(result['input_dispatched'])
        self.assertIsNone(result['task_success'])
        self.assertFalse(result['replay_allowed'])

    def test_review_and_bind_requires_same_focused_process_and_window_generation(self):
        child={'pid':GUI_PID,'start_ticks':GUI_START_TICKS,
            'executable':str(self.executable)}
        custody={'schema':'agent-interface/calc-process-group-custody-v1',
            'pgid':PID,'session_id':PID,
            'launcher':{'pid':PID,'start_ticks':START_TICKS},
            'target':{'pid':GUI_PID,'start_ticks':GUI_START_TICKS}}
        metadata={'xid':GUI_XID,'process_pid':GUI_PID,
            'process_start_ticks':GUI_START_TICKS,
            'process_generation':GUI_GENERATION,
            'process_incarnation':'d'*64,'window_incarnation':'e'*64,
            'mapped':True,'focused_before':True,'focused_after':True}
        candidate=dict(metadata)
        class Owner:
            _calc_process_group_custody=custody
            def __init__(self): self.events=[]
            def windows_for_process(self,pid,title_hint):
                self.events.append(('discover',pid,title_hint))
                return {'status':'discovered','windows':[candidate]}
            def inspect_window_metadata(self,xid):
                self.events.append(('metadata',xid))
                return {'status':'inspected','window_metadata':metadata}
            def invoke_guarded(self,operation,arguments,*,call_root):
                self.events.append(('review',arguments['window_id']))
                return {'status':'reviewed','input_dispatched':False,
                    'review':{'status':'reviewed'}}
        owner=Owner()
        self.supervisor._pid=PID
        self.supervisor._start_ticks=START_TICKS
        self.supervisor._artifact=self.artifact
        with patch.object(self.supervisor,'validate_current_gui_child',return_value=child), \
                patch.object(self.supervisor,'bind_xres_target',return_value={
                    'status':'bound','xid':GUI_XID,'process_pid':GUI_PID,
                    'process_start_ticks':GUI_START_TICKS}) as bind:
            result=self.supervisor.review_and_bind_owned_window(owner,GUI_XID,
                call_root=self.root/'review')
        self.assertEqual(result['status'],'reviewed',result)
        self.assertEqual(result['binding']['process_start_ticks'],GUI_START_TICKS)
        self.assertEqual(owner.events,[('discover',GUI_PID,'task-artifact.fods'),
            ('metadata',GUI_XID),('review',GUI_XID),('metadata',GUI_XID)])
        bind.assert_called_once_with(metadata)
        self.assertFalse(result['authority_granted'])
        self.assertFalse(result['input_dispatched'])
        self.assertIsNone(result['task_success'])
        self.assertFalse(result['replay_allowed'])

    def test_review_and_bind_refuses_unfocused_candidate_without_activation(self):
        child={'pid':GUI_PID,'start_ticks':GUI_START_TICKS}
        custody={'schema':'agent-interface/calc-process-group-custody-v1',
            'pgid':PID,'session_id':PID,
            'launcher':{'pid':PID,'start_ticks':START_TICKS},
            'target':{'pid':GUI_PID,'start_ticks':GUI_START_TICKS}}
        metadata={'xid':GUI_XID,'process_pid':GUI_PID,
            'process_start_ticks':GUI_START_TICKS,
            'process_generation':GUI_GENERATION,
            'process_incarnation':'d'*64,'window_incarnation':'e'*64,
            'mapped':True,'focused_before':False,'focused_after':False}
        class Owner:
            _calc_process_group_custody=custody
            def __init__(self): self.reviews=0
            def windows_for_process(self,pid,title_hint):
                return {'status':'discovered','windows':[dict(metadata)]}
            def inspect_window_metadata(self,xid):
                return {'window_metadata':metadata}
            def invoke_guarded(self,*args,**kwargs): self.reviews+=1
        owner=Owner();self.supervisor._pid=PID
        self.supervisor._start_ticks=START_TICKS;self.supervisor._artifact=self.artifact
        with patch.object(self.supervisor,'validate_current_gui_child',return_value=child), \
                patch.object(self.supervisor,'bind_xres_target') as bind:
            result=self.supervisor.review_and_bind_owned_window(owner,GUI_XID,
                call_root=self.root/'review')
        self.assertEqual(result['status'],'needs_review',result)
        self.assertEqual(result['reason'],'fresh_candidate_metadata_mismatch_or_unfocused')
        self.assertEqual(owner.reviews,0)
        bind.assert_not_called()


if __name__ == '__main__':
    unittest.main()
