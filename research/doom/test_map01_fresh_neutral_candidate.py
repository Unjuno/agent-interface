"""Offline contract tests for the fresh, input-free MAP01 candidate path."""
import sys
import types
import tempfile
import json
from unittest.mock import Mock, patch
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_map01_verified_fixture_setup import session_module

class FreshNeutralCandidateTests(unittest.TestCase):
    def test_only_one_fixed_passive_coast_is_admitted(self):
        s = session_module()
        steps = [{'op':'coast','duration_ms':5000,'sample_ms':250},
                 {'op':'coast','duration_ms':4768,'sample_ms':250}]
        digest = s.program_sha256(steps)
        self.assertTrue(s.admit_fresh_neutral_program(steps, digest, False))
        for bad, claimed in ((steps, True), ([{'op':'hold','keys':['a'],'duration_ms':1}], False),
                             ([{'op':'coast','duration_ms':1,'sample_ms':1}], False),
                             ([{'op':'observe'}], False)):
            with self.subTest(bad=bad, claimed=claimed), self.assertRaises(ValueError):
                s.admit_fresh_neutral_program(bad, digest, claimed)

    def test_fresh_mode_requires_private_target_and_no_parent_or_gate(self):
        s = session_module()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            args=types.SimpleNamespace(verified_fixture_setup=False, fresh_neutral_fixture_setup=True,
                load_fixture_manifest=None, fixture_out=root/'candidate.png',
                renewal_passive_observer=True, fixture_setup_program_sha256='a'*64)
            self.assertIsNotNone(s.validate_verified_fixture_setup(args, None))
            for change, gate in (({'load_fixture_manifest':root/'parent.json'}, None),
                                 ({},object()), ({'renewal_passive_observer':False},None),
                                 ({'fixture_setup_program_sha256':None},None),
                                 ({'verified_fixture_setup':True},None)):
                wrong=types.SimpleNamespace(**{**vars(args),**change})
                with self.subTest(change=change), self.assertRaises(ValueError):
                    s.validate_verified_fixture_setup(wrong,gate)
            (root/'candidate.png').write_text('existing')
            with self.assertRaises(ValueError): s.validate_verified_fixture_setup(args,None)

    def test_admission_must_remain_fresh_after_receipt_delivery(self):
        s=session_module()
        source={'capture_ns':100}
        owner={'sample_finished_ns':200}
        s.require_fresh_neutral_deadline(source,owner,100,300,now=250)
        for now in (300, 1_000_000_201, 2_000_000_101):
            with self.subTest(now=now), self.assertRaises(ValueError):
                s.require_fresh_neutral_deadline(source,owner,100,300,now=now)

    def test_final_snapshot_requires_same_rgb_and_no_hud_drop(self):
        s=session_module()
        def pair(seq, health, identifier):
            binding={'focus':5,'surface':5,'geometry':[0,0,640,480]}
            base={'id':identifier,'sequence':seq,'capture_ns':seq*100,'frame_rgb_sha256':'a'*64,
                  'pointer_binding':binding,'input_owner_generation':0,'renewal_owner_id':'owner',
                  'target_process_identity':{'sequence':seq,'surface':5,'digest':'b'*64},
                  'target_renewal_window_identity':{'sequence':seq,'surface':5,'digest':'d'*64}}
            signals={name:{'status':'observed','value':value,'sequence':seq,'capture_ns':seq*100,
                           'binding':binding,'signal_id':name}
                     for name,value in [('health',health),('ammo',50)]}
            typed={'event':'typed_observation',**base,'signals':signals}
            full={'event':'observation',**base,'exact':True,'focus_samples_match':True,
                  'input_focus_before':5,'input_focus_after':5}
            return typed,full
        initial=pair(1,100,'initial'); final=pair(2,100,'fixture-source')
        events=[*initial,*final]
        s.validate_fresh_neutral_snapshot(events,final[1])
        for rows in ([*initial,*pair(2,97,'fixture-source')],
                     [*initial,*pair(2,None,'fixture-source')],
                     [*initial,final[0],dict(final[1],frame_rgb_sha256='c'*64)],
                     [*initial,final[0],dict(final[1],exact=False)],
                     [*initial,dict(final[0],renewal_owner_id='other'),final[1]],
                     [*initial,*[dict(x,target_process_identity={'sequence':2,'surface':5,'digest':'e'*64}) for x in final]],
                     [*initial,*[dict(x,target_renewal_window_identity={'sequence':2,'surface':5,'digest':'f'*64}) for x in final]],
                     [*final]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                s.validate_fresh_neutral_snapshot(rows,rows[-1])

    def test_failed_end_clock_stops_real_command_loop_before_save(self):
        from test_map01_session_retirement_boundary import command_loop
        run=command_loop(json.dumps({'op':'save_fixture'})+'\n')
        scope=run.__globals__
        scope.update(door_coordinator=None,setup_events=[],setup_sources={},last_accepted={},last_terminal={},
                     validate_fresh_neutral_completed=lambda *args: None,
                     close_before_control_effect=lambda *args: None,
                     fresh_gate=types.SimpleNamespace(display=':120'))
        end_gate=types.SimpleNamespace(path=None, after_load=Mock(side_effect=ValueError('clock stopped')))
        fake_gate_module=types.SimpleNamespace(PostLoadGate=lambda *args:end_gate)
        game=types.SimpleNamespace(get_episode_time=lambda:100,save=Mock())
        args=types.SimpleNamespace(out=Path('/tmp'),fixture_out=Path('/tmp/candidate.png'),
            fresh_neutral_fixture_setup=True,verified_fixture_setup=False,timeout_seconds=75,
            fixture_setup_program_sha256='a'*64)
        backend=types.SimpleNamespace(snapshot=Mock())
        with patch.dict(sys.modules,{'map01_post_load_gate_v1':fake_gate_module}):
            with self.assertRaisesRegex(ValueError,'clock stopped'):
                run(Mock(),backend,game,args,Mock(),lambda row:None,{},0)
        game.save.assert_not_called()
        backend.snapshot.assert_not_called()

    def test_bad_final_hud_stops_real_command_loop_before_save(self):
        from test_map01_session_retirement_boundary import command_loop
        run=command_loop(json.dumps({'op':'save_fixture'})+'\n')
        scope=run.__globals__
        def reject(*args): raise ValueError('health decreased')
        scope.update(door_coordinator=None,setup_events=[],setup_sources={},last_accepted={},last_terminal={},
                     validate_fresh_neutral_completed=lambda *args: None,
                     validate_fresh_neutral_snapshot=reject,
                     close_before_control_effect=lambda *args: None,
                     fresh_gate=types.SimpleNamespace(display=':120'))
        end_gate=types.SimpleNamespace(path=None,display=':120',after_load=Mock())
        fake_gate_module=types.SimpleNamespace(PostLoadGate=lambda *args:end_gate)
        game=types.SimpleNamespace(get_episode_time=lambda:100,save=Mock())
        args=types.SimpleNamespace(out=Path('/tmp'),fixture_out=Path('/tmp/candidate.png'),
            fresh_neutral_fixture_setup=True,verified_fixture_setup=False,timeout_seconds=75,
            fixture_setup_program_sha256='a'*64)
        backend=types.SimpleNamespace(snapshot=Mock())
        with patch.dict(sys.modules,{'map01_post_load_gate_v1':fake_gate_module}):
            with self.assertRaisesRegex(ValueError,'health decreased'):
                run(Mock(),backend,game,args,Mock(),lambda row:None,{},0)
        backend.snapshot.assert_called_once_with('fixture-source',0)
        game.save.assert_not_called()

    def test_success_requires_matching_completed_owner_and_no_input(self):
        s = session_module()
        accepted = {'event':'accepted','id':'coast','program_sha256':'a'*64}
        terminal = {'event':'terminal','id':'coast','status':'completed','input_owner_id':'owner',
                    'input_owner_generation':0,'release':{'verified':True,'keys_down':[],
                    'buttons_down':[],'keys_unknown':[],'key_state_errors':[]}}
        source = {'renewal_owner_id':'owner','input_owner_generation':0}
        backend = types.SimpleNamespace(owner=types.SimpleNamespace(owner_id='owner'), _owner_generation=0)
        s.validate_fresh_neutral_completed([accepted,terminal], {'coast':source}, 'a'*64,
                                           dict(accepted,emit_ns=100),dict(terminal,emit_ns=200),backend)
        for events in ([accepted], [accepted,dict(terminal,status='cancelled')],
                       [accepted,terminal,{'event':'input_admission','id':'coast'}],
                       [accepted,terminal,{'event':'pointer_admission','id':'coast'}],
                       [accepted,terminal,{'event':'input_release_transition','id':'coast'}]):
            with self.subTest(events=events), self.assertRaises(ValueError):
                s.validate_fresh_neutral_completed(events, {'coast':source}, 'a'*64,
                                                   accepted,terminal,backend)
        backend.owner.owner_id = 'foreign'
        with self.assertRaises(ValueError):
            s.validate_fresh_neutral_completed([accepted,terminal], {'coast':source}, 'a'*64,
                                               accepted,terminal,backend)

if __name__ == '__main__': unittest.main()
